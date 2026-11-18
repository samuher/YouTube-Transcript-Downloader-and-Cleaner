"""Sequential, cooperative and resumable job worker."""
from __future__ import annotations

import random
from threading import Event, Thread
import time

from .provider import AccessBlocked, RateLimited, TemporaryFailure, YouTubeProvider, VideoFailure


class Worker:
    def __init__(self, store, provider_factory=YouTubeProvider, sleeper=time.sleep):
        self.store=store
        self.provider_factory=provider_factory
        self.sleep=sleeper
        self.stop_event=Event()
        self.thread=None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.thread=Thread(target=self._loop,name='transcript-studio-worker',daemon=True)
        self.thread.start()

    def stop(self, timeout=3):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout)

    def _loop(self):
        while not self.stop_event.is_set():
            job=self.store.next_job()
            if not job:
                self.stop_event.wait(.75)
                continue
            try:
                self.process(job['id'])
            except Exception as exc:
                self.store.set_status(job['id'],'failed',str(exc))

    def _interrupt(self, job_id):
        job=self.store.get_job(job_id)
        if not job:
            return True
        if job['status'] in ('paused','cancelled') or self.stop_event.is_set():
            if self.stop_event.is_set() and job['status']=='running':
                self.store.set_status(job_id,'queued','El proceso se detuvo; se reanudará al reiniciar')
            return True
        return False

    def _wait(self, seconds, job_id):
        # Controlled shutdown, pause and cancel are checked during long backoffs.
        until=time.monotonic()+seconds
        while time.monotonic()<until:
            if self._interrupt(job_id):
                return False
            self.sleep(min(.5,until-time.monotonic()))
        return not self._interrupt(job_id)

    def _attempt(self, job_id, callback, *, retries, delay, max_delay):
        for attempt in range(1,retries+2):
            if self._interrupt(job_id):
                return None,attempt,True
            try:
                return callback(),attempt,False
            except AccessBlocked:
                raise
            except (RateLimited,TemporaryFailure):
                if attempt>retries:
                    raise
                wait=min(max_delay,delay*(2**(attempt-1)))*random.uniform(.9,1.1)
                if not self._wait(wait,job_id):
                    return None,attempt,True
        return None,retries+1,False

    def process(self, job_id):
        job=self.store.get_job(job_id)
        if job is None or job['status']!='running':
            return
        options=job['options']
        provider=self.provider_factory(browser=options.get('browser'),
                                       cookies_path=options.get('cookies_path'),
                                       subtitle_delay=options.get('subtitle_delay',1))
        retries=options.get('retries',2)
        delay=options.get('backoff',30)
        max_delay=options.get('max_backoff',300)
        try:
            videos,_,interrupted=self._attempt(
                job_id,lambda:provider.list_videos(job['url'],options.get('max_videos',0)),
                retries=retries,delay=delay,max_delay=max_delay)
            if interrupted or self._interrupt(job_id):
                return
            self.store.set_total(job_id,len(videos))
            previous_request=False
            for item in videos:
                if self._interrupt(job_id):
                    return
                code,title=item['video_id'],item['title']
                if self.store.video_status(job_id,code) in ('downloaded','skipped'):
                    continue
                if self.store.has_languages(code,job['languages']):
                    self.store.record_video(job_id,code,title,'skipped')
                    continue
                if previous_request:
                    wait=random.uniform(options.get('pause_min',3),options.get('pause_max',7))
                    if not self._wait(wait,job_id):
                        return
                previous_request=True
                attempts=0
                try:
                    subtitles,attempts,interrupted=self._attempt(
                        job_id,lambda:provider.get_captions(code,job['languages']),
                        retries=retries,delay=delay,max_delay=max_delay)
                    if interrupted or self._interrupt(job_id):
                        return
                    if not subtitles:
                        self.store.record_video(job_id,code,title,'missing',attempts=attempts)
                    else:
                        for sub in subtitles:
                            self.store.upsert_transcript(
                                video_id=code,title=title,language=sub.language,kind=sub.kind,
                                source_url='https://www.youtube.com/watch?v='+code,
                                original=sub.original,text=sub.text,segments=sub.segments)
                        self.store.record_video(job_id,code,title,'downloaded',attempts=attempts)
                except (AccessBlocked,RateLimited) as exc:
                    self.store.record_video(job_id,code,title,'blocked',str(exc),attempts)
                    self.store.set_status(job_id,'blocked','Acceso restringido o límite de YouTube; reanuda manualmente más tarde')
                    return
                except (VideoFailure,TemporaryFailure,ValueError,OSError) as exc:
                    self.store.record_video(job_id,code,title,'failed',str(exc),attempts)
            if not self._interrupt(job_id):
                self.store.set_status(job_id,'completed')
        except (AccessBlocked,RateLimited) as exc:
            self.store.set_status(job_id,'blocked',str(exc))
        except (VideoFailure,TemporaryFailure,ValueError,OSError) as exc:
            self.store.set_status(job_id,'failed',str(exc))
