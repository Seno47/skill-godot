"""Candidate/media/receipt checks. Admissibility is not perceptual acceptance."""
from __future__ import annotations

import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import re
import shutil
import struct
import subprocess
from typing import Any

from mjpeg_avi_watchback import walk_chunks, parse_stream_header, jpeg_payload


class IntegrityError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def resolve(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise IntegrityError('expected a concrete path')
    path = Path(value).expanduser()
    return (root / path).resolve() if not path.is_absolute() else path.resolve()


def concrete(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.lower().startswith(
        ('unrecorded', 'unresolved', 'not tested', 'not_tested', 'replace', 'todo')
    )


def observations_present(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(concrete(item) for item in value)


def finite_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def check_hash(path: Path, expected: Any) -> str:
    if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', expected):
        raise IntegrityError(f'missing/invalid SHA-256: {path}')
    actual = sha256(path)
    if actual != expected.lower():
        raise IntegrityError(f'SHA-256 mismatch (stale or replaced artifact): {path}')
    return actual


def decode_media(path: Path, kind: str) -> dict[str, Any]:
    if kind not in {'image', 'video'}:
        return {}
    if kind == 'image':
        from PIL import Image
        with Image.open(path) as picture:
            picture.verify()
        with Image.open(path) as picture:
            picture.load()
            return {'width': picture.width, 'height': picture.height, 'decoded': True}
    if path.suffix.lower() == '.avi':
        from PIL import Image
        with path.open('rb') as stream:
            header = stream.read(12)
            if len(header) != 12 or header[:4] != b'RIFF' or header[8:] != b'AVI ':
                raise IntegrityError('not a RIFF AVI video')
            end = struct.unpack_from('<I', header, 4)[0] + 8
            if end > path.stat().st_size:
                raise IntegrityError('AVI is shorter than its RIFF declaration')
            # Godot can append valid top-level chunks beyond the initial RIFF size.
            # Parse them too; arbitrary trailing/truncated data must still fail.
            chunks = list(walk_chunks(stream, 12, path.stat().st_size))
            streams = []
            declared = None
            dimensions = None
            for chunk in chunks:
                if chunk.fourcc in {b'strh', b'avih'}:
                    stream.seek(chunk.offset)
                    payload = stream.read(chunk.size)
                    if chunk.fourcc == b'strh':
                        streams.append(parse_stream_header(len(streams), payload))
                    elif len(payload) >= 40:
                        declared = struct.unpack_from('<I', payload, 16)[0]
                        dimensions = struct.unpack_from('<II', payload, 32)
            videos = [s for s in streams if s.stream_type == 'vids']
            if len(videos) != 1 or videos[0].handler.upper() not in {'MJPG', 'JPEG'}:
                raise IntegrityError('AVI requires one MJPEG stream; use ffmpeg/transcode for other codecs')
            video = videos[0]
            if video.rate <= 0 or video.scale <= 0:
                raise IntegrityError('invalid video clock')
            prefix = f'{video.index:02d}'.encode()
            frames = [c for c in chunks if b'movi' in c.parents and c.fourcc[:2] == prefix and c.fourcc[2:] in {b'dc', b'db'}]
            if not frames or declared not in {0, len(frames)} or video.length not in {0, len(frames)}:
                raise IntegrityError('missing frames or inconsistent AVI frame count')
            for index, frame in enumerate(frames):
                stream.seek(frame.offset)
                payload, _, _ = jpeg_payload(stream.read(frame.size), index)
                with Image.open(BytesIO(payload)) as picture:
                    picture.load()
                    if picture.size != dimensions:
                        raise IntegrityError('video frame dimensions changed or disagree with header')
            return {'decoded': True, 'frames': len(frames), 'duration_seconds': len(frames) * video.scale / video.rate}
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        raise IntegrityError('video decoding requires ffmpeg/ffprobe or Godot MJPEG AVI')
    probe = subprocess.run([ffprobe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], capture_output=True, text=True, timeout=60, check=True)
    container = json.loads(probe.stdout)
    streams = container['streams']
    video = next((s for s in streams if s.get('codec_type') == 'video'), None)
    if video is None:
        raise IntegrityError('no video stream')
    duration_value = video.get('duration')
    if duration_value in {None, 'N/A'}:
        duration_value = container.get('format', {}).get('duration', 0)
    duration = float(duration_value)
    if not math.isfinite(duration) or duration <= 0:
        raise IntegrityError('video has no verifiable duration; transcode to bounded MJPEG capture')
    subprocess.run([ffmpeg, '-v', 'error', '-xerror', '-i', str(path), '-map', '0:v:0', '-f', 'null', '-'], capture_output=True, timeout=60, check=True)
    return {'decoded': True, 'duration_seconds': duration}


def validate_gate_integrity(gate_id: str, value: dict, owner: str, metadata: dict,
                            root: Path, cache: dict | None = None) -> list[str]:
    errors: list[str] = []
    cache = cache if cache is not None else {}
    def bound_hash(path: Path, expected: Any) -> str:
        stat = path.stat()
        key = ('hash', str(path), stat.st_size, stat.st_mtime_ns, str(expected))
        if key not in cache:
            cache[key] = check_hash(path, expected)
        return cache[key]
    try:
        candidate = metadata.get('candidate', {})
        if not isinstance(candidate, dict) or not concrete(candidate.get('build_id')):
            raise IntegrityError('run_metadata.candidate needs a concrete build_id, path and sha256')
        candidate_path = resolve(root, candidate.get('path'))
        candidate_hash = bound_hash(candidate_path, candidate.get('sha256'))
        if value.get('build_id') != candidate['build_id'] or value.get('candidate_sha256') != candidate_hash:
            raise IntegrityError('gate is not bound to the current candidate')
        artifact_claims: dict[str, set[str]] = {}
        content_paths: dict[tuple[str, str], str] = {}
        for item in value.get('artifacts', []):
            try:
                path = resolve(root, item.get('path'))
                digest = bound_hash(path, item.get('sha256'))
                identity = (item['kind'], digest)
                if item['kind'] in {'image', 'video'} and identity in content_paths and content_paths[identity] != str(path):
                    raise IntegrityError('identical media copied to different paths cannot manufacture state coverage')
                content_paths[identity] = str(path)
                key = (str(path), digest, item['kind'])
                if key not in cache:
                    cache[key] = decode_media(path, item['kind'])
                decoded = cache[key]
                states = item.get('states', [])
                artifact_claims.setdefault(digest, set()).update(states)
                if item['kind'] == 'video':
                    segments = item.get('segments', {})
                    for state in states:
                        span = segments.get(state)
                        if not isinstance(span, list) or len(span) != 2 or any(isinstance(n, bool) or not isinstance(n, (float, int)) or not math.isfinite(n) for n in span) or not 0 <= span[0] < span[1] <= decoded['duration_seconds'] + 0.001:
                            raise IntegrityError(f'video state {state} needs a valid timed segment')
                    if gate_id in {'production_motion_quality_evidence', 'production_character_motion_evidence'}:
                        watchback = value.get('watchback', {}).get(digest, {})
                        if (not all(finite_number(watchback.get(key)) for key in ('playback_speed', 'start_seconds', 'end_seconds'))
                                or watchback['playback_speed'] != 1 or watchback['start_seconds'] != 0
                                or abs(watchback['end_seconds'] - decoded['duration_seconds']) > 0.001
                                or not observations_present(watchback.get('observations'))):
                            raise IntegrityError('motion gate needs full normal-speed watchback observations bound to this video')
            except Exception as exc:
                errors.append(f'{gate_id}: invalid artifact {item.get("path")}: {exc}')
        if owner == 'builder':
            return errors
        reviewer = value.get('reviewer', {})
        context = reviewer.get('context')
        builder = metadata.get('builder_context')
        if not concrete(builder) or not concrete(context) or context == builder:
            raise IntegrityError('external acceptance requires distinct concrete builder/reviewer contexts')
        receipt_ref = reviewer.get('receipt', {})
        receipt_path = resolve(root, receipt_ref.get('path'))
        bound_hash(receipt_path, receipt_ref.get('sha256'))
        receipt = json.loads(receipt_path.read_text(encoding='utf-8-sig'))
        if receipt.get('schema_version') != 1 or receipt.get('build_id') != candidate['build_id'] or receipt.get('candidate_sha256') != candidate_hash:
            raise IntegrityError('review receipt belongs to another candidate or schema')
        if receipt.get('reviewer_context') != context or receipt.get('source_context') != context or not concrete(receipt.get('source_message')):
            raise IntegrityError('receipt must preserve response provenance from the acceptance context')
        decision = receipt.get('gates', {}).get(gate_id, {})
        if decision.get('verdict') != 'pass' or decision.get('blockers') != []:
            raise IntegrityError('receipt does not award PASS with zero unresolved blockers')
        observations = decision.get('observations')
        if not observations_present(observations):
            raise IntegrityError('receipt needs actual observations')
        observed = decision.get('artifacts', {})
        if not isinstance(observed, dict):
            raise IntegrityError('receipt artifacts must map SHA-256 to observed states')
        for digest, states in artifact_claims.items():
            cited = observed.get(digest, [])
            if not isinstance(cited, list) or not states.issubset(set(cited)):
                raise IntegrityError('receipt did not observe all cited artifact hashes/states')
        blind_gates = {'cross_surface_production_craft_review', 'critical_action_comprehension_review', 'semantic_identity_review', 'progression_visual_comprehension_review'}
        if gate_id in blind_gates and (decision.get('first_read_before_intent') is not True or not observations_present(decision.get('first_read_observations'))):
            raise IntegrityError('blind gate needs preserved first-read observations before intent')
    except Exception as exc:
        errors.append(f'{gate_id}: {exc}')
    return errors
