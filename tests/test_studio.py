"""Regression tests use fake captions; they never contact YouTube."""
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from io import BytesIO
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from transcript_studio.captions import Segment,parse_captions,clean_segments,format_timestamp
from transcript_studio.storage import Store
from transcript_studio.provider import normalize_url,AccessBlocked,RateLimited,DownloadedCaption, classify_error
from transcript_studio.exporting import export_one,export_zip,_volume_chunks
from transcript_studio.worker import Worker
from transcript_studio.app import create_app
from fastapi.testclient import TestClient


class ParserTests(unittest.TestCase):
    def test_srt_and_vtt(self):
        data='''WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n<v Mary>Hello &amp; welcome</v>\n\n00:00:02.000 --> 00:00:03.000\nHello &amp; welcome everyone\n'''
        segments=parse_captions(data)
        self.assertEqual(len(segments),2)
        text,clean=clean_segments(segments)
        self.assertEqual(text,'Hello & welcome everyone')
        self.assertEqual(len(clean),2)
        self.assertEqual(format_timestamp(61.25),'00:01:01,250')
        self.assertEqual(parse_captions('1\n00:00:01,000 --> 00:00:02,000\nHola\n')[0].text,'Hola')

    def test_invalid_cues_skipped(self):
        self.assertFalse(parse_captions('WEBVTT\n\nNOTE invalid\n\n00:00:03.000 --> 00:00:01.000\nreverse\n'))

    def test_normalize_rejects_other_hosts(self):
        with self.assertRaises(ValueError): normalize_url('https://youtube.com.evil.org/@user')
        with self.assertRaises(ValueError): normalize_url('file:///etc/passwd')
        self.assertEqual(normalize_url('https://youtu.be/abcdefghijk?t=3'),
                         'https://www.youtube.com/watch?v=abcdefghijk')
        self.assertEqual(normalize_url('https://youtube.com/@channel'),
                         'https://www.youtube.com/@channel/videos')
        self.assertIsInstance(classify_error('HTTP Error 429'), RateLimited)
        self.assertIsInstance(classify_error("Sign in to confirm you're not a bot"), AccessBlocked)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.store=Store(Path(self.tmp.name)/'test.sqlite3')
    def tearDown(self): self.tmp.cleanup()

    def test_queue_survives_restarts_and_transitions(self):
        job=self.store.create_job('https://www.youtube.com/@test/videos',['es'],{'max_videos':0})
        self.assertEqual(job['status'],'queued')
        next_=self.store.next_job()
        self.assertEqual(next_['id'],job['id'])
        self.assertEqual(self.store.get_job(job['id'])['status'],'running')
        Store(self.store.path)
        self.assertEqual(self.store.get_job(job['id'])['status'],'queued')
        self.assertTrue(self.store.set_status(job['id'],'paused',expected={'queued'}))
        self.assertFalse(self.store.set_status(job['id'],'running',expected={'cancelled'}))

    def test_transcripts_are_upserted_and_searchable(self):
        args=dict(video_id='abcdefghijk',title='Prueba',language='es',kind='manual',
            source_url='https://www.youtube.com/watch?v=abcdefghijk',original='WEBVTT',text='Hola mundo',
            segments=[{'start':0.0,'end':1.0,'text':'Hola mundo'}])
        self.store.upsert_transcript(**args)
        self.store.upsert_transcript(**{**args,'text':'Hola corregido'})
        result=self.store.search('corregido')
        self.assertEqual(len(result),1)
        self.assertTrue(self.store.has_languages('abcdefghijk',['es']))
        self.assertFalse(self.store.has_languages('abcdefghijk',['es','en']))
        self.assertEqual(self.store.get_transcript(result[0]['id'])['segments'][0]['start'],0)
        self.assertFalse(self.store.search('%'))


class DummyProvider:
    calls=[]
    mode='ok'
    def __init__(self,**kwargs): pass
    def list_videos(self,url,max_videos):
        self.calls.append('list')
        return [{'video_id':'abcdefghijk','title':'Clase 1'}, {'video_id':'lmnopqrstuv','title':'Clase 2'}]
    def get_captions(self,video_id,languages):
        self.calls.append(video_id)
        if self.mode=='blocked' and video_id=='lmnopqrstuv':
            raise AccessBlocked('confirm not a bot')
        return [DownloadedCaption('es','automatic','WEBVTT','Hola mundo',
                                  [{'start':0.,'end':1.,'text':'Hola mundo'}])]


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.store=Store(Path(self.tmp.name)/'test.sqlite3')
        DummyProvider.calls=[]
        DummyProvider.mode='ok'
    def tearDown(self): self.tmp.cleanup()
    def new_job(self):
        return self.store.create_job('https://www.youtube.com/@test/videos',['es'],{
            'max_videos':0,'pause_min':0,'pause_max':0,'retries':0,'backoff':0,'max_backoff':0})
    def test_job_downloads_and_avoids_duplicates(self):
        job=self.new_job()
        worker=Worker(self.store,provider_factory=DummyProvider)
        worker.process(self.store.next_job()['id'])
        self.assertEqual(self.store.get_job(job['id'])['status'],'completed')
        self.assertEqual(self.store.stats()['transcripts'],2)
        second=self.new_job()
        worker.process(self.store.next_job()['id'])
        self.assertEqual(self.store.get_job(second['id'])['skipped'],2)
        self.assertEqual(DummyProvider.calls.count('abcdefghijk'),1)
    def test_blocked_stays_blocked_and_resume(self):
        DummyProvider.mode='blocked'
        job=self.new_job(); worker=Worker(self.store,provider_factory=DummyProvider)
        worker.process(self.store.next_job()['id'])
        self.assertEqual(self.store.get_job(job['id'])['status'],'blocked')
        self.assertEqual(self.store.stats()['transcripts'],1)
        DummyProvider.mode='ok'
        self.store.set_status(job['id'],'queued',expected={'blocked'})
        worker.process(self.store.next_job()['id'])
        self.assertEqual(self.store.get_job(job['id'])['status'],'completed')
        self.assertEqual(self.store.stats()['transcripts'],2)
    def test_paused_job_not_claimed(self):
        job=self.new_job()
        self.store.set_status(job['id'],'paused')
        self.assertIsNone(self.store.next_job())


class ExportTests(unittest.TestCase):
    def sample(self,text='uno dos tres'):
        return dict(video_id='abcdefghijk',title='Título',language='es',kind='manual',
            source_url='https://www.youtube.com/watch?v=abcdefghijk',text=text,
            segments=[{'start':0.0,'end':1.5,'text':'uno dos tres'}])
    def test_txt_markdown_json_srt(self):
        item=self.sample()
        self.assertIn('uno dos',export_one(item,'txt').decode())
        self.assertIn(item['source_url'],export_one(item,'md').decode())
        self.assertEqual(json.loads(export_one(item,'json'))['language'],'es')
        self.assertIn('00:00:01,500',export_one(item,'srt').decode())
    def test_notebooklm_split_without_losing_tokens(self):
        words=[f'token{i}' for i in range(97)]
        parts=_volume_chunks([self.sample(' '.join(words))],word_limit=20,byte_limit=1100)
        self.assertGreater(len(parts),1)
        for part in parts:
            self.assertLessEqual(len(part.decode().split()),20)
            self.assertLessEqual(len(part),1100)
        text=' '.join(p.decode() for p in parts)
        for word in words:
            self.assertEqual(text.split().count(word),1)
        with ZipFile(BytesIO(export_zip([self.sample()],'notebooklm')),'r') as z:
            self.assertTrue(z.namelist()[0].endswith('.txt'))


class APITests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.app=create_app(self.tmp.name,start_worker=False)
        self.client=TestClient(self.app)
    def tearDown(self): self.client.close(); self.tmp.cleanup()
    def test_html_and_health(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertIn('Transcript Studio',self.client.get('/').text)
        self.assertTrue(self.client.get('/api/health').json()['ok'])
    def test_job_validation_and_pause_resume(self):
        self.assertEqual(self.client.post('/api/jobs',json={'url':'https://evil.org/x'}).status_code,422)
        res=self.client.post('/api/jobs',json={'url':'https://www.youtube.com/@test','languages':['es']})
        self.assertEqual(res.status_code,201)
        job=res.json()
        self.assertIn('/videos',job['url'])
        self.assertEqual(self.client.post(f'/api/jobs/{job["id"]}/pause').json()['status'],'paused')
        self.assertEqual(self.client.post(f'/api/jobs/{job["id"]}/resume').json()['status'],'queued')
        self.assertEqual(self.client.post(f'/api/jobs/{job["id"]}/resume').status_code,409)
    def test_cross_origin_and_bad_host_rejected(self):
        self.assertEqual(self.client.post('/api/jobs',headers={'origin':'https://evil.org'},json={}).status_code,403)
        self.assertEqual(self.client.get('/api/jobs',headers={'host':'evil.org'}).status_code,400)
    def test_export_api(self):
        self.app.state.store.upsert_transcript(**dict(video_id='abcdefghijk',title='Título',language='es',kind='manual',
            source_url='https://www.youtube.com/watch?v=abcdefghijk',original='WEBVTT',text='Hola mundo',
            segments=[{'start':0.0,'end':1.0,'text':'Hola mundo'}]))
        item=self.client.get('/api/transcripts').json()[0]
        self.assertIn('Hola',self.client.get(f'/api/transcripts/{item["id"]}').json()['text'])
        result=self.client.get('/api/export',params={'ids':str(item['id']),'format':'txt'})
        self.assertEqual(result.status_code,200)
        with ZipFile(BytesIO(result.content),'r') as z:
            self.assertIn('Hola mundo',z.read(z.namelist()[0]).decode())
        self.assertEqual(self.client.get('/api/export',params={'ids':'1,2','format':'txt'}).status_code,404)

if __name__=='__main__':unittest.main()
