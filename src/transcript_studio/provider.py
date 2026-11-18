"""YouTube extraction adapter; no network calls are made when importing this module."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlsplit

from .captions import parse_captions, clean_segments

_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
_CHANNEL = {'channel','user','c'}
_BROWSERS = {'brave','chrome','chromium','edge','firefox','opera','vivaldi'}


class AccessBlocked(Exception):
    """Authentication/bot challenge: stop, do not retry aggressively."""


class RateLimited(Exception):
    """429 or equivalent: retry with delays, then stop."""


class TemporaryFailure(Exception):
    """Transient network/server issue."""


class VideoFailure(Exception):
    """Permanent-looking failure affecting only this video."""


@dataclass
class DownloadedCaption:
    language: str
    kind: str
    original: str
    text: str
    segments: list[dict]


def normalize_url(value: str):
    url = urlsplit(value.strip())
    if url.scheme not in ('http','https') or (url.hostname or '').lower() not in {
        'youtube.com','www.youtube.com','m.youtube.com','youtu.be'}:
        raise ValueError('Se necesita una URL válida de YouTube')
    if url.username or url.password or url.port not in (None,80,443):
        raise ValueError('La URL contiene datos de acceso o un puerto no permitido')
    path = url.path.strip('/')
    if url.hostname == 'youtu.be':
        if not _ID.fullmatch(path):
            raise ValueError('ID de vídeo inválido')
        return f'https://www.youtube.com/watch?v={path}'
    if path == 'watch':
        code = parse_qs(url.query).get('v', [''])[0]
        if not _ID.fullmatch(code):
            raise ValueError('ID de vídeo inválido')
        return f'https://www.youtube.com/watch?v={code}'
    parts = path.split('/')
    if len(parts)==2 and parts[0] in ('shorts','live') and _ID.fullmatch(parts[1]):
        return f'https://www.youtube.com/watch?v={parts[1]}'
    channel = ((parts[0].startswith('@') and len(parts[0])>1)
               or (parts[0] in _CHANNEL and len(parts)>1 and bool(parts[1])))
    if not channel:
        raise ValueError('Enlace no admitido: usa un vídeo o canal (@usuario, /channel/, /c/, /user/)')
    suffixes={'videos','shorts','streams'}
    if parts[-1] not in suffixes:
        if parts[-1] in {'playlists','community','about','featured'}:
            raise ValueError('Usa la pestaña /videos, /shorts o /streams del canal')
        path += '/videos'
    return 'https://www.youtube.com/' + path


def classify_error(exc):
    text = str(exc).casefold()
    if re.search(r'\b429\b', text) or 'too many requests' in text or 'rate limit' in text:
        return RateLimited(str(exc))
    if (re.search(r'\b(401|403)\b', text) or "not a bot" in text or
        'captcha' in text or 'sign in to confirm' in text or 'unusual traffic' in text):
        return AccessBlocked(str(exc))
    if (re.search(r'\b(500|502|503|504)\b', text) or 'timed out' in text or
        'timeout' in text or 'connection reset' in text or 'temporary failure' in text):
        return TemporaryFailure(str(exc))
    return VideoFailure(str(exc))


class YtLogger:
    def __init__(self):
        self.messages=[]
    def debug(self, message):
        pass
    def warning(self, message):
        self.messages.append(str(message))
    def error(self, message):
        self.messages.append(str(message))
    def raise_if_blocked(self):
        for message in self.messages:
            error=classify_error(message)
            if isinstance(error,(AccessBlocked,RateLimited,TemporaryFailure)):
                raise error


class YouTubeProvider:
    def __init__(self, browser=None, cookies_path=None, subtitle_delay=1):
        if browser and cookies_path:
            raise ValueError('Selecciona navegador o archivo de cookies, no ambos')
        if browser and browser not in _BROWSERS:
            raise ValueError('Navegador no admitido')
        self.browser=browser
        self.cookies_path=cookies_path
        self.subtitle_delay=subtitle_delay

    def _options(self, logger):
        options={'quiet':True,'logger':logger,'ignoreerrors':False,
                 'skip_download':True,'socket_timeout':25,'retries':2}
        if self.browser:
            options['cookiesfrombrowser']=(self.browser,)
        if self.cookies_path:
            path=Path(self.cookies_path).expanduser().resolve()
            if not path.is_file():
                raise ValueError('El archivo de cookies no existe')
            options['cookiefile']=str(path)
        return options

    def _download(self, fn):
        try:
            return fn()
        except (AccessBlocked,RateLimited,TemporaryFailure,VideoFailure):
            raise
        except Exception as exc:
            raise classify_error(exc) from exc

    def list_videos(self, url, max_videos=0):
        import yt_dlp
        logger=YtLogger()
        options=self._options(logger)
        options.update({'extract_flat':'in_playlist','noplaylist':False})
        if max_videos:
            options['playlistend']=max_videos
        def get():
            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(url,download=False)
        data=self._download(get)
        logger.raise_if_blocked()
        if not data:
            raise VideoFailure('No se encontraron vídeos')
        entries=data.get('entries') if isinstance(data,dict) else None
        entries=entries if entries is not None else [data]
        result=[]
        seen=set()
        for item in entries:
            if not isinstance(item,dict):
                continue
            code=item.get('id')
            if not isinstance(code,str) or not _ID.fullmatch(code) or code in seen:
                continue
            seen.add(code)
            result.append({'video_id':code,'title':item.get('title') or code})
            if max_videos and len(result)>=max_videos:
                break
        if not result:
            raise VideoFailure('No se encontraron vídeos válidos')
        return result

    def get_captions(self, video_id, languages):
        import yt_dlp
        if not _ID.fullmatch(video_id):
            raise ValueError('ID de vídeo inválido')
        logger=YtLogger()
        with TemporaryDirectory(prefix='ts_') as directory:
            opts=self._options(logger)
            opts.update({'writesubtitles':True,'writeautomaticsub':True,
                         'subtitleslangs':list(languages),'subtitlesformat':'vtt/srt',
                         'outtmpl':str(Path(directory)/'%(id)s.%(ext)s'),
                         'sleep_interval_subtitles':self.subtitle_delay})
            def get():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info('https://www.youtube.com/watch?v='+video_id, download=True)
            info=self._download(get)
            logger.raise_if_blocked()
            if not info:
                raise VideoFailure('Vídeo no disponible')
            manual=set((info.get('subtitles') or {}).keys())
            found=[]
            for file in sorted(Path(directory).iterdir()):
                if file.suffix.lower() not in {'.vtt','.srt'} or not file.name.startswith(video_id+'.'):
                    continue
                lang=file.name[len(video_id)+1:-len(file.suffix)]
                if not any(lang==selected or lang.startswith(selected+'-') for selected in languages):
                    continue
                try:
                    original=file.read_text(encoding='utf-8-sig')
                    raw=parse_captions(original)
                    cleaned, segments=clean_segments(raw)
                except (OSError,UnicodeError,ValueError):
                    continue
                if not cleaned:
                    continue
                found.append(DownloadedCaption(lang,'manual' if lang in manual else 'automatic',
                                               original,cleaned,[s.to_dict() for s in raw]))
            return found
