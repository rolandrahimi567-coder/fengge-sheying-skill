"""Compile the preserved Roversi summary; no creative expansion or API calls."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(user_request):
    if not isinstance(user_request, str) or not user_request.strip():
        raise ValueError('A nonempty original user request is required')
    path = ROOT / 'references' / 'roversi-style-summary.txt'
    summary = path.read_text(encoding='utf-8').strip()
    if not summary:
        raise ValueError('Preserved style summary is empty')
    prompt = '\n'.join([
        'Generate one original editorial photograph in the style of Paolo Roversi.',
        user_request,
        summary,
        (ROOT / "references" / "roversi-default-rendering.txt").read_text(encoding="utf-8").strip(),
    ])
    return {
        'schema_version': 'atelier-summary-1',
        'prompt_mode': 'style_summary',
        'photographer': 'Paolo Roversi',
        'user_request': user_request,
        'tool_arguments': {'prompt': prompt},
        'summary_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'summary_origin': '2026-09-10 comparison: group B, unchanged',
        'generation_status': 'ready',
        'human_acceptance': None,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request-file', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    job = build(args.request_file.read_text(encoding='utf-8'))
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(job, stream, ensure_ascii=False, indent=2)
