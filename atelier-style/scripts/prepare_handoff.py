"""Compile an assistant-authored decision into a local-only, source-bound handoff."""
import argparse, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ROLES = {'lighting', 'spatial_relation', 'color', 'pose', 'garment_relation'}
def asset_path(value):
    p=Path(value)
    return p if p.is_absolute() else ROOT/p
def text(value, label):
    if not isinstance(value, str) or not value.strip(): raise ValueError('Missing text: ' + label)
    return value

def strings(value, label):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError('Expected string list: ' + label)
    return value

def compile_pack(request, decision):
    p = ROOT / 'references/photographers'
    cards_data = json.loads((p/'style-cards.json').read_text())
    cards = cards_data['cards']
    rows = json.loads((p/'archive150.json').read_text())
    inventory = {x['record_id']: x for x in rows}
    text(request.get('need'), 'need')
    if request.get('mode') not in ('edit', 'new'): raise ValueError('mode must be edit or new')
    for key in ('preserve', 'allowed_changes', 'avoid'):
        strings(request.get(key), key)
    card = next((c for c in cards if c['branch_id']==decision.get('branch_id') and c['photographer_id']==decision.get('photographer_id')), None)
    if card is None: raise ValueError('Invalid photographer / branch combination')
    text(decision.get('selection_reason'), 'selection_reason')
    text(decision.get('visual_plan'), 'visual_plan')
    strings(decision.get('pending_questions'), 'pending_questions')
    refs = decision.get('references')
    if not isinstance(refs,list) or not 1 <= len(refs) <= 4: raise ValueError('Select 1 to 4 purpose-bound references')
    subtype = decision.get('subtype_id')
    if card.get('subtypes'):
        sub = next((s for s in card['subtypes'] if s['id']==subtype), None)
        if sub is None: raise ValueError('Choose one subtype before combining references')
        allowed = set(sub['refs'])
    else:
        if subtype is not None: raise ValueError('This branch has no subtype')
        allowed = {r['sequence'] for r in card['evidence']}
    def asset(record_id):
        if record_id not in inventory: raise ValueError('Asset outside frozen 150: '+str(record_id))
        item = inventory[record_id]; file = asset_path(item['local_analysis_path'])
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=item['analysis_sha256']:
            raise ValueError('Missing or changed source: '+record_id)
        return {**item, 'local_analysis_path': str(file.resolve())}
    direction = decision.get('style_direction')
    if direction is not None:
        if not isinstance(direction, dict): raise ValueError('style_direction must be an object')
        if direction.get('branch_id') != card['branch_id']: raise ValueError('Style direction branch mismatch')
        for key in ('photographer_name', 'target_effect', 'subject_treatment', 'reference_basis'):
            text(direction.get(key), 'style_direction.'+key)
        strings(direction.get('signature_relations'), 'signature_relations')
        if len(direction['signature_relations']) < 2: raise ValueError('Provide interacting style relations')
        strings(direction.get('failure_signs'), 'failure_signs')
        if not direction['failure_signs']: raise ValueError('Provide observable failure signs')
    source = None
    if request.get('input_record_id') and request.get('input_image_path'):
        raise ValueError('Choose one input source, not both')
    if request.get('input_record_id'):
        source = asset(request['input_record_id'])
    elif request.get('input_image_path'):
        file = Path(request['input_image_path']).expanduser()
        if not file.is_absolute() or not file.is_file():
            raise ValueError('External input must be an existing absolute image path')
        if file.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
            raise ValueError('Unsupported external image extension')
        source = {'record_id': None, 'asset_id': None,
                  'analysis_sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                  'local_analysis_path': str(file.resolve()),
                  'original_permissions': {'status': 'SESSION_INPUT_NOT_CATALOG_ASSET'}}
    seen=set(); evidence=[]
    for ref in refs:
        item=asset(ref.get('record_id'))
        if item['record_id'] in seen: raise ValueError('Duplicate reference')
        seen.add(item['record_id'])
        if source and item['record_id']==source['record_id']: raise ValueError('Input cannot count as independent style reference')
        if item['photographer_id']!=card['photographer_id'] or item['sequence'] not in allowed:
            raise ValueError('Reference outside selected branch/subtype')
        if ref.get('role') not in ROLES: raise ValueError('Unknown reference role')
        text(ref.get('borrow'), 'borrow');strings(ref.get('do_not_copy'), 'do_not_copy')
        evidence.append({'record_id':item['record_id'],'asset_id':item['asset_id'],'sequence':item['sequence'],
            'sha256':item['analysis_sha256'],'local_analysis_path':item['local_analysis_path'],
            'role':ref['role'],'borrow':ref['borrow'],'do_not_copy':ref['do_not_copy'],
            'observed_fact':item['observed_fact'],'attribution_status':item['attribution_status'],
            'permissions':item['original_permissions']})
    # A preparatory contract never upgrades the user's source permissions or validates a model judgement.
    pending=list(decision['pending_questions'])
    if request['mode']=='edit' and source is None: pending.append('缺少编辑输入；提供图片或库内ID后检查保留项。')
    if source and decision.get('inspected_input_sha256')!=source['analysis_sha256']:
        pending.append('尚未提供与当前输入一致的看图记录。')
    if not request['allowed_changes'] and request['mode']=='edit': pending.append('尚未明确允许变化范围。')
    prompt=None
    if not pending:
        prompt='\n'.join(['任务：'+request['need'],'模式：'+request['mode'],
            '画面方案：'+decision['visual_plan'],'保留：'+'；'.join(request['preserve']),
            '允许改变：'+'；'.join(request['allowed_changes']),'避免：'+'；'.join(request['avoid']),
            '参考只借鉴所列关系，不转移人物身份、服装或独特装置。',
            *[f"参考#{r['sequence']} / {r['role']}：{r['borrow']}；不要复制："+'；'.join(r['do_not_copy']) for r in evidence]])
    return {'schema_version':'atelier-handoff-1','style_version':cards_data['version'],
        'status':'NEEDS_CLARIFICATION' if pending else 'DRAFT_FOR_REVIEW',
        'request':request,'style_direction':direction,'selection':{'photographer_id':card['photographer_id'],'branch_id':card['branch_id'],
        'subtype_id':subtype,'reason':decision['selection_reason']},'visual_plan':decision['visual_plan'],
        'references':evidence,'input':None if source is None else {k:source[k] for k in ('record_id','asset_id','analysis_sha256','local_analysis_path','original_permissions')},
        'prompt':prompt,'pending_questions':pending,'provider':None,'provider_settings':None,
        'execution_authorized':False,'generated':False,'quality_validated':False,
        'evidence_note':'归属为文件名标签，观察为候选；助手提交的输入看图记录并非人工验收。B/B1、衣物结果仍由原项目保有，本脚本不重新测量或更改检索。'}

def markdown(pack):
    s='# 视觉制作交接草案\n\n状态：'+pack['status']+'；未执行生成。\n\n## 需求\n\n'+pack['request']['need']+'\n\n## 方向\n\n'+pack['selection']['reason']+'\n\n## 画面方案\n\n'+pack['visual_plan']+'\n\n## 参考与用途\n\n'
    for r in pack['references']:
        s+=f"- #{r['sequence']}（{r['role']}）：{r['borrow']}。不复制："+'；'.join(r['do_not_copy'])+'。\n'
    for key,label in [('preserve','保留项'),('allowed_changes','允许变化'),('avoid','禁止项')]:
        s+='\n## '+label+'\n\n'+'\n'.join('- '+x for x in pack['request'][key])+'\n'
    s+='\n## 提示词\n\n'+(pack['prompt'] or '尚未编译：请先解决待确认项。')+'\n\n## 待确认\n\n'+'\n'.join('- '+x for x in pack['pending_questions'])+'\n\n'+pack['evidence_note']+'\n'
    return s

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',type=Path,required=True);parser.add_argument('--decision',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    try:
        pack=compile_pack(json.loads(args.request.read_text()),json.loads(args.decision.read_text()))
        if args.out.exists(): raise ValueError('Output path already exists; choose a new directory')
        args.out.mkdir(parents=True)
        (args.out/'handoff.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2))
        (args.out/'交接说明.md').write_text(markdown(pack))
        print(json.dumps({'status':pack['status'],'output':str(args.out.resolve()),'generated':False},ensure_ascii=False))
    except (ValueError,KeyError,TypeError,OSError) as e: parser.exit(2,str(e)+'\n')
if __name__=='__main__': main()
