"""Read-only photographer profiles, branch briefs and frozen review inventory."""
import argparse
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / 'references/photographers'
def read(name): return json.loads((ROOT / name).read_text())
def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('profiles')
    show = commands.add_parser('show')
    show.add_argument('--photographer', required=True)
    show.add_argument('--branch')
    archive = commands.add_parser('archive')
    archive.add_argument('--photographer')
    archive.add_argument('--sequence', type=int)
    archive.add_argument('--unassigned', action='store_true')
    args = parser.parse_args()
    profiles = read('profiles.json')
    valid = {p['photographer_id'] for p in profiles}
    if getattr(args, 'photographer', None) and args.photographer not in valid:
        parser.error('Unknown photographer')
    if args.command == 'profiles':
        result = {'mode': 'BRIEF_ONLY', 'profiles': profiles}
    elif args.command == 'archive':
        rows = [x for x in read('archive150.json')
                if (not args.photographer or x['photographer_id'] == args.photographer)
                and (args.sequence is None or x['sequence'] == args.sequence)
                and (not args.unassigned or not x['branch_candidates'])]
        if args.sequence is not None and not rows:
            parser.error('Sequence not present in requested frozen scope')
        result = {'mode': 'READ_ONLY', 'count': len(rows), 'items': rows}
    else:
        selected = [c for c in read('style-cards.json')['cards']
                    if c['photographer_id'] == args.photographer
                    and (not args.branch or c['branch_id'] == args.branch)]
        if not selected:
            parser.error('Branch does not belong to photographer')
        result = {'mode': 'BRIEF_ONLY', 'input_review': 'NOT_PERFORMED',
                  'profile': next(p for p in profiles if p['photographer_id'] == args.photographer), 'cards': selected}
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
