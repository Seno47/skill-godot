"""Bind existing evidence to bytes; never generate observations or verdicts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from evidence_integrity import sha256, resolve


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', required=True)
    parser.add_argument('--candidate', required=True, help='Exact build or deterministic dependency manifest')
    parser.add_argument('--build-id', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        source, output = Path(args.evidence).resolve(), Path(args.output).resolve()
        if output.exists() and not args.force:
            raise ValueError('output exists; choose another path or pass --force')
        data = json.loads(source.read_text(encoding='utf-8-sig'))
        metadata = data.setdefault('run_metadata', {})
        root = resolve(source.parent, metadata.get('artifact_root', '.'))
        candidate = Path(args.candidate).resolve()
        digest = sha256(candidate)
        metadata['artifact_root'] = str(root)
        metadata['candidate'] = {'build_id': args.build_id, 'path': str(candidate), 'sha256': digest}
        count = 0
        for gate in data['gates'].values():
            gate['build_id'], gate['candidate_sha256'] = args.build_id, digest
            for item in gate.get('artifacts', []):
                item['sha256'] = sha256(resolve(root, item['path']))
                count += 1
            receipt = gate.get('reviewer', {}).get('receipt')
            if receipt:
                receipt['sha256'] = sha256(resolve(root, receipt['path']))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'[BOUND] {count} artifact references; verdicts unchanged. Re-run scorecard; old review receipts are not renewed.')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
