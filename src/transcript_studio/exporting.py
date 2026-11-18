"""Export TXT/MD/SRT/JSON and word/byte-bounded NotebookLM volumes."""
from __future__ import annotations

from io import BytesIO
import json
import re
from zipfile import ZipFile, ZIP_DEFLATED

from .captions import format_timestamp


def safe_name(value, length=90):
    value=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',value).strip(' ._')[:length].rstrip(' .')
    return value or 'transcript'


def export_one(item, fmt):
    title=item['title']
    url=item['source_url']
    if fmt=='txt':
        return (item['text'].strip()+'\n').encode('utf-8')
    if fmt=='md':
        return (f'# {title}\n\nVídeo: {url}\n\nIdioma: {item["language"]}\n\n'+item['text'].strip()+'\n').encode('utf-8')
    if fmt=='json':
        return json.dumps({key:item[key] for key in ('video_id','title','language','kind','source_url','text','segments')},
                          ensure_ascii=False,indent=2).encode('utf-8')
    if fmt=='srt':
        lines=[]
        for index,seg in enumerate(item['segments'],1):
            lines.append(f'{index}\n{format_timestamp(seg["start"])} --> {format_timestamp(seg["end"])}\n{seg["text"]}\n')
        return ('\n'.join(lines)+'\n').encode('utf-8')
    raise ValueError('Formato de exportación no admitido')


def _volume_chunks(items, word_limit=450000, byte_limit=8_000_000):
    if not 10<=word_limit<=500000 or not 1024<=byte_limit<=200_000_000:
        raise ValueError('Límitesde volumen no válidos')
    volumes=[]
    parts=[]
    words=0
    size=0
    def save():
        nonlocal parts,words,size
        if parts:
            volumes.append((''.join(parts).lstrip()+'\n').encode('utf-8'))
            parts=[]; words=0; size=0
    for item in items:
        tokens=item['text'].split()
        if not tokens:
            continue
        index=0
        section=1
        while index<len(tokens):
            header=(f'\n\n---\nFuente: {item["title"]}\n'
                    f'Enlace: {item["source_url"]}\nIdioma: {item["language"]}\n'
                    f'Parte: {section}\n---\n\n')
            head_words=len(header.split()); head_bytes=len(header.encode('utf-8'))
            if head_words>=word_limit or head_bytes>=byte_limit:
                raise ValueError('Límites demasiado pequeños para el encabezado')
            available_words=word_limit-words-head_words
            available_bytes=byte_limit-size-head_bytes-3
            if available_words<=0 or available_bytes<=0:
                save()
                continue
            taken=[]
            added_bytes=0
            while index+len(taken)<len(tokens) and len(taken)<available_words:
                token=tokens[index+len(taken)]
                encoded=len(token.encode('utf-8'))+(1 if taken else 0)
                if added_bytes+encoded>available_bytes:
                    break
                taken.append(token)
                added_bytes+=encoded
            if not taken:
                if parts:
                    save()
                    continue
                raise ValueError('Una palabra supera el límite de bytes por fuente')
            parts.append(header+' '.join(taken))
            words+=head_words+len(taken)
            size+=head_bytes+added_bytes
            index+=len(taken)
            section+=1
    save()
    return volumes


def export_zip(items, fmt='txt', word_limit=450000, byte_limit=8_000_000):
    buffer=BytesIO()
    with ZipFile(buffer,'w',ZIP_DEFLATED) as zf:
        if fmt=='notebooklm':
            for index,bytes_ in enumerate(_volume_chunks(items,word_limit,byte_limit),1):
                zf.writestr(f'notebooklm_tomo_{index:03d}.txt',bytes_)
        elif fmt in ('txt','md','srt','json'):
            for item in items:
                name=f'{safe_name(item["title"])} [{item["video_id"]}].{safe_name(item["language"])}.{fmt}'
                zf.writestr(name,export_one(item,fmt))
        else:
            raise ValueError('Formato de exportación no admitido')
    return buffer.getvalue()
