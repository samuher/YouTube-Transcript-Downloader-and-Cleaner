"""Timed caption parsing and conservative, reversible text cleanup."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import html
import re

_TIME = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{3})")
_TAGS = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str

    def to_dict(self):
        return asdict(self)


def _seconds(value: str) -> float:
    value = value.strip().split()[0]
    match = _TIME.fullmatch(value)
    if not match:
        raise ValueError(f"Invalid subtitle timestamp: {value!r}")
    hours, minutes, seconds, millis = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def parse_captions(content: str) -> list[Segment]:
    """Parse WebVTT/SRT cues, preserving timestamps; skip styling and metadata."""
    content = content.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", content)
    found: list[Segment] = []
    for block in blocks:
        lines = block.splitlines()
        if not lines or lines[0].lstrip().startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        index = next((n for n, line in enumerate(lines) if "-->" in line), None)
        if index is None:
            continue
        line = lines[index]
        start_raw, end_raw = line.split("-->", maxsplit=1)
        try:
            start, end = _seconds(start_raw), _seconds(end_raw)
        except ValueError:
            continue
        if end <= start:
            continue
        text = html.unescape(_TAGS.sub("", " ".join(lines[index + 1:])))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            found.append(Segment(start, end, text))
    return found


def clean_segments(segments: list[Segment]) -> tuple[str, list[Segment]]:
    """Remove only clear adjacent word overlap; keep original cues separately."""
    result: list[Segment] = []
    previous: list[str] = []
    for segment in segments:
        words = segment.text.split()
        old = [word.casefold() for word in previous]
        new = [word.casefold() for word in words]
        overlap = 0
        for size in range(min(len(old), len(new)), 0, -1):
            if old[-size:] == new[:size]:
                overlap = size
                break
        # Some auto-captions repeat the whole earlier cue as a prefix.
        if not overlap and len(new) <= len(old) and old[:len(new)] == new:
            overlap = len(new)
        remainder = " ".join(words[overlap:])
        if remainder:
            result.append(Segment(segment.start, segment.end, remainder))
        previous = words
    return " ".join(s.text for s in result), result


def format_timestamp(seconds: float, *, srt: bool = True) -> str:
    ms = max(0, round(seconds * 1000))
    hrs, ms = divmod(ms, 3_600_000)
    mins, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1_000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}{',' if srt else '.'}{ms:03d}"
