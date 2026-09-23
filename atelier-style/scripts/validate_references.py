"""Audit all profile references, including branch counterexamples; no generation."""
import json
from pathlib import Path

def validate(profiles, observations, cards):
    errors = []
    def indexed(rows, label):
        result = {}
        for row in rows:
            key = row['sequence']
            if key in result:
                errors.append(f'{label}: duplicate sequence {key}')
            result[key] = row
        return result
    obs = indexed(observations, 'observations')
    deep = indexed(cards, 'deep cards')
    def check(seq, author, context):
        row, card = obs.get(seq, {}), deep.get(seq, {})
        if (row.get('photographer_label') != author
                or not row.get('evidence_eligible') or row.get('duplicate_of')
                or card.get('photographer_id') != author
                or not card.get('analysis_sha256')
                or card.get('analysis_sha256') != row.get('analysis_sha256')):
            errors.append(f'{context}: invalid reference {seq}')
    for seq, card in deep.items():
        check(seq, card.get('photographer_id'), 'deep card')
    for author, profile in profiles.items():
        ids = [r['id'] for r in profile['relations']]
        if len(ids) != len(set(ids)):
            errors.append(f'{author}: duplicate relation ID')
        branch_ids = [b['id'] for b in profile['branches']]
        if len(branch_ids) != len(set(branch_ids)):
            errors.append(f'{author}: duplicate branch ID')
        for rel in profile['relations']:
            for seq in rel['evidence']:
                check(seq, author, rel['id'])
        for branch in profile['branches']:
            if not set(branch.get('recommended', branch.get('required', [])) + branch['optional']) <= set(ids):
                errors.append(f"{author}/{branch['id']}: unknown relation")
            for seq in branch['counterexamples']:
                check(seq, author, branch['id'])
    return errors

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1] / 'references'
    errors = validate(*(json.loads((root / name).read_text()) for name in
                        ['profiles.json', 'observations300.json', 'deep-cards.json']))
    print(json.dumps({'ok': not errors, 'errors': errors}, indent=2))
    raise SystemExit(bool(errors))
