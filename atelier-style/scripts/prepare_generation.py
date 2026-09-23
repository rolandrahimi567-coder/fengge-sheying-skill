"""Validate evidence bindings and compile a text-only job; no API calls or image export."""
import argparse
import hashlib
import json
from pathlib import Path
from validate_references import validate as validate_references
ROOT = Path(__file__).resolve().parents[1]
VERSION = '3.1-research'

def read(name):
    return json.loads((ROOT / 'references' / name).read_text())

def nonempty(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Missing text: ' + name)
    return value.strip()

def build(d):
    profiles = read('profiles.json')
    observations = read('observations300.json')
    deep_cards = read('deep-cards.json')
    reference_errors = validate_references(profiles, observations, deep_cards)
    if reference_errors:
        raise ValueError('Reference audit failed: ' + '; '.join(reference_errors))
    author = d.get('photographer_id')
    if author not in profiles:
        raise ValueError('Unsupported photographer')
    profile = profiles[author]
    branches = {x['id']: x for x in profile['branches']}
    if d.get('branch_id') not in branches:
        raise ValueError('Unknown branch')
    branch = branches[d['branch_id']]
    mode = d.get('prompt_mode', 'legacy')
    if mode not in ('legacy', 'selective'):
        raise ValueError('Unknown prompt_mode')
    scene_fields = {'composition': 'Composition', 'subject_state': 'People and actions',
                    'light_and_color': 'Light and color', 'material_and_focus': 'Surface and focus'}
    for k in ['user_request', 'branch_reason', 'feasibility_check']:
        nonempty(d.get(k), k)
    if mode == 'legacy':
        for k in scene_fields:
            nonempty(d.get(k), k)
    else:
        nonempty(d.get('selection_reason'), 'selection_reason')
        reasons = d.get('guidance_reasons', {})
        if not isinstance(reasons, dict) or not set(reasons) <= set(scene_fields):
            raise ValueError('Invalid guidance_reasons')
        for k in scene_fields:
            value = d.get(k)
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            nonempty(value, k)
            nonempty(reasons.get(k), k + ' reason')
    constraints = d.get('user_constraints')
    if not isinstance(constraints, list) or not constraints:
        raise ValueError('Explicit user constraints required')
    for x in constraints:
        nonempty(x, 'user_constraint')
    # This flag is the agent's declared review, not a semantic proof.
    if d.get('unresolved_conflicts') != []:
        raise ValueError('Resolve declared conflicts before generation')
    relations = {x['id']: x for x in profile['relations']}
    obs = {x['sequence']: x for x in observations}
    cards = {x['sequence']: x for x in deep_cards}
    applied = d.get('applied_relations')
    minimum = 1 if mode == 'legacy' else 0
    if not isinstance(applied, list) or not minimum <= len(applied) <= 3:
        raise ValueError('Invalid number of relations')
    ids = [x.get('relation_id') for x in applied]
    recommended = branch.get('recommended', branch.get('required', []))
    allowed = set(recommended + branch['optional'])
    if (len(set(ids)) != len(ids) or not set(ids) <= allowed
            or (mode == 'legacy' and not set(recommended) <= set(ids))):
        raise ValueError('Missing, duplicate or incompatible branch relations')
    compiled = []
    # Required rules first even when the caller supplies optional rules first.
    order = recommended + branch['optional']
    for a in sorted(applied, key=lambda x: order.index(x['relation_id'])):
        rel = relations[a['relation_id']]
        refs = a.get('evidence_sequences')
        if not isinstance(refs, list) or len(refs) < 2 or any(type(x) is not int for x in refs) or len(set(refs)) != len(refs):
            raise ValueError('At least two distinct integer evidence IDs required')
        if not set(refs) <= set(rel['evidence']):
            raise ValueError('Evidence does not support selected relation in profile')
        for seq in refs:
            row = obs.get(seq, {})
            if row.get('photographer_label') != author or not row.get('evidence_eligible') or row.get('duplicate_of') or seq not in cards:
                raise ValueError('Ineligible, duplicate or not deeply reviewed evidence')
        item = dict(relation_id=rel['id'], priority=('required' if mode == 'legacy' else 'recommended') if rel['id'] in recommended else 'optional', rule=rel['rule'], boundary=rel['boundary'], evidence_sequences=refs, implementation=nonempty(a.get('implementation'), 'implementation'))
        if mode == 'selective':
            item['reason'] = nonempty(a.get('reason'), 'relation reason')
        compiled.append(item)
    failure_signs = d.get('failure_signs', [] if mode == 'selective' else None)
    if not isinstance(failure_signs, list) or not minimum <= len(failure_signs) <= 6:
        raise ValueError('Invalid number of failure signs')
    for f in failure_signs:
        nonempty(f, 'failure_sign')
    if mode == 'selective':
        prompt = ['Generate one original editorial photograph in the style of ' + profile['name'] + '.', d['user_request']]
        for r in compiled:
            prompt.append('Direction: ' + r['implementation'])
        for k, label in scene_fields.items():
            if isinstance(d.get(k), str) and d[k].strip():
                prompt.append(label + ': ' + d[k].strip())
        if failure_signs:
            prompt.append('Avoid: ' + '; '.join(failure_signs))
    else:
        prompt = ['Generate one original editorial photograph in the style of ' + profile['name'] + '.',
              'User request: ' + d['user_request'],
              'Keep these user requirements: ' + '; '.join(constraints),
              'Apply these relationships, in priority order:']
        for r in compiled:
            prompt += [r['rule'], 'In this new image: ' + r['implementation']]
        prompt += ['Composition: ' + d['composition'], 'People and actions: ' + d['subject_state'],
               'Light and color: ' + d['light_and_color'], 'Surface and focus: ' + d['material_and_focus'],
               'Avoid: ' + '; '.join(failure_signs),
               'Make a new scene, not a reconstruction of a source photograph. No photographer signature or watermark.']
    return dict(schema_version='atelier-generation-3.1' if mode == 'selective' else 'atelier-generation-3', skill_version=VERSION, prompt_mode=mode, generation_status='ready', review_status='not_reviewed', tool_arguments={'prompt': '\n'.join(prompt)}, decision=d, compiled_relations=compiled,
                provenance={n: hashlib.sha256((ROOT/'references'/n).read_bytes()).hexdigest() for n in ['profiles.json','deep-cards.json','observations300.json']},
                source_images_sent=0, actual_model_id=None, usage=None, cost=None, output=None, human_acceptance=None)

def finish(job, output=None, error=None):
    if job.get('generation_status') != 'ready':
        raise ValueError('Job already finished')
    if bool(output) == bool(error):
        raise ValueError('Provide output OR error')
    result = dict(job)
    if output:
        p = Path(output).resolve()
        if not p.is_file():
            raise ValueError('Output missing')
        result.update(generation_status='generated', output=str(p), output_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    else:
        result.update(generation_status='failed', error=str(error))
    # Neither API success nor this state transition constitutes review.
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--decision', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    job = build(json.loads(a.decision.read_text()))
    with a.out.open('x') as f:
        json.dump(job, f, ensure_ascii=False, indent=2)
