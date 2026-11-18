"""FastAPI interface, bound to loopback by the launcher; no external CDN is used."""
from __future__ import annotations

from contextlib import asynccontextmanager
from io import BytesIO
import os
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .exporting import export_zip
from .provider import normalize_url
from .storage import Store
from .worker import Worker


class JobRequest(BaseModel):
    url: str = Field(min_length=10,max_length=500)
    languages: list[str] = Field(default_factory=lambda:['es'],min_length=1,max_length=5)
    max_videos: int = Field(default=0,ge=0,le=100000)
    pause_min: float = Field(default=3,ge=0,le=180)
    pause_max: float = Field(default=7,ge=0,le=180)
    retries: int = Field(default=2,ge=0,le=6)
    backoff: float = Field(default=30,ge=0,le=3600)
    max_backoff: float = Field(default=300,ge=0,le=3600)
    subtitle_delay: float = Field(default=1,ge=0,le=30)
    browser: str | None = None
    cookies_path: str | None = None

    @field_validator('languages')
    @classmethod
    def valid_languages(cls,value):
        if any(not re.fullmatch(r'[A-Za-z]{2,3}(?:-[A-Za-z]{2,8})?',lang) for lang in value):
            raise ValueError('Códigos de idioma inválidos')
        return list(dict.fromkeys(value))

    @model_validator(mode='after')
    def valid_options(self):
        if self.pause_min>self.pause_max or self.backoff>self.max_backoff:
            raise ValueError('La espera máxima no puede ser inferior a la mínima')
        if self.browser and self.cookies_path:
            raise ValueError('Elige cookies o navegador, no ambos')
        if self.browser and self.browser not in {'brave','chrome','chromium','edge','firefox','opera','vivaldi'}:
            raise ValueError('Navegador no admitido')
        return self


def default_data_dir():
    if os.name=='nt':
        return Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData'/'Local'))/'TranscriptStudio'
    if os.sys.platform=='darwin':
        return Path.home()/'Library'/'Application Support'/'TranscriptStudio'
    return Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local'/'share'))/'transcript-studio'


def create_app(data_dir=None, provider_factory=None, start_worker=True):
    root=Path(data_dir or default_data_dir()).expanduser().resolve()
    root.mkdir(parents=True,exist_ok=True)
    store=Store(root/'library.sqlite3')
    worker=Worker(store,provider_factory=provider_factory) if provider_factory else Worker(store)

    @asynccontextmanager
    async def lifespan(app):
        if start_worker:
            worker.start()
        yield
        if start_worker:
            worker.stop()

    app=FastAPI(title='Transcript Studio',version='0.2.0',lifespan=lifespan,
                docs_url=None,redoc_url=None,openapi_url=None)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1','testserver'])
    app.state.store=store
    app.state.worker=worker
    app.state.data_dir=root

    @app.middleware('http')
    async def deny_cross_origin_writes(request:Request,call_next):
        if request.method not in {'GET','HEAD','OPTIONS'}:
            origin=request.headers.get('origin')
            if origin and not re.fullmatch(r'https?://(?:127\.0\.0\.1|localhost)(?::\d+)?',origin):
                return Response('Origin no permitido',status_code=403)
        return await call_next(request)

    @app.get('/api/health')
    def health():
        return {'ok':True,'version':'0.2.0'}

    @app.get('/api/stats')
    def stats():
        return store.stats()

    @app.get('/api/jobs')
    def jobs():
        return store.list_jobs()

    @app.post('/api/jobs',status_code=201)
    def create_job(payload:JobRequest):
        try:
            url=normalize_url(payload.url)
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
        opts=payload.model_dump(exclude={'url','languages'})
        return store.create_job(url,payload.languages,opts)

    @app.get('/api/jobs/{job_id}')
    def job(job_id:str):
        result=store.get_job(job_id)
        if result is None:
            raise HTTPException(404,'Trabajo no encontrado')
        return {'job':result,'videos':store.list_job_videos(job_id)}

    @app.post('/api/jobs/{job_id}/{action}')
    def job_action(job_id:str,action:str):
        result=store.get_job(job_id)
        if result is None:
            raise HTTPException(404,'Trabajo no encontrado')
        status=result['status']
        transitions={
            'pause':({'running','queued'},'paused'),
            'resume':({'paused','blocked','failed','partial'},'queued'),
            'cancel':({'queued','running','paused','blocked','failed'},'cancelled'),
        }
        if action not in transitions:
            raise HTTPException(404,'Acción desconocida')
        allowed,target=transitions[action]
        if status not in allowed or not store.set_status(job_id,target,expected=allowed):
            raise HTTPException(409,f'No se puede {action} desde {status}')
        return store.get_job(job_id)

    @app.get('/api/transcripts')
    def transcripts(q:str='',language:str='',limit:int=100,offset:int=0):
        if not 1<=limit<=200 or not 0<=offset<=100000 or len(q)>250 or len(language)>15:
            raise HTTPException(422,'Parámetros de búsqueda no válidos')
        return store.search(q,limit,offset,language)

    @app.get('/api/transcripts/{item_id}')
    def transcript(item_id:int):
        result=store.get_transcript(item_id)
        if result is None:
            raise HTTPException(404,'Transcripción no encontrada')
        return result

    @app.get('/api/export')
    def export(ids:str,format:str='txt',words:int=450000,bytes_limit:int=8_000_000):
        try:
            selected=[int(part) for part in ids.split(',')]
        except ValueError as exc:
            raise HTTPException(422,'IDs inválidos') from exc
        if not selected or len(selected)>500 or any(item<=0 for item in selected):
            raise HTTPException(422,'Selecciona entre 1 y 500 transcripciones')
        items=store.get_transcripts(selected)
        if len(items)!=len(set(selected)):
            raise HTTPException(404,'Alguna transcripción no existe')
        try:
            output=export_zip(items,format,words,bytes_limit)
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
        return Response(output,media_type='application/zip',headers={
            'Content-Disposition':'attachment; filename="transcript-studio-export.zip"',
            'Cache-Control':'no-store',
        })

    static=Path(__file__).parent/'static'
    app.mount('/static',StaticFiles(directory=static),name='static')
    @app.get('/')
    def index():
        return FileResponse(static/'index.html',headers={'Cache-Control':'no-store'})
    return app


app=create_app()
