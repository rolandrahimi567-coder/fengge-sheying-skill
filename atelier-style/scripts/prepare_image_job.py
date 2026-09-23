"""Validate a session-scoped image edit and emit built-in tool arguments; no HTTP calls."""
import argparse,hashlib,json
from pathlib import Path

def build_job(pack, consent):
    if pack.get('status')!='DRAFT_FOR_REVIEW' or not pack.get('prompt') or pack.get('pending_questions'):
        raise ValueError('Handoff has unresolved decisions')
    if pack.get('request',{}).get('mode')!='edit' or not pack.get('input'):
        raise ValueError('Direct edit requires an input image')
    if consent.get('intent')!='generate' or not isinstance(consent.get('user_authorization'),str) or not consent['user_authorization'].strip():
        raise ValueError('Current session must request generation')
    if consent.get('edit_mode') not in ('fidelity','creative','photographer_transform'):
        raise ValueError('Choose fidelity, creative or photographer_transform edit mode')
    if consent.get('max_outputs')!=1:
        raise ValueError('This job prepares exactly one output')
    direction=pack.get('style_direction')
    if consent['edit_mode']=='photographer_transform':
        if not isinstance(direction,dict): raise ValueError('Photographer transformation requires a style direction')
        if direction.get('branch_id')!=pack.get('selection',{}).get('branch_id'): raise ValueError('Style direction branch mismatch')
        for key in ('photographer_name','target_effect','subject_treatment','reference_basis'):
            if not isinstance(direction.get(key),str) or not direction[key].strip(): raise ValueError('Missing style direction: '+key)
        for key,minimum in [('signature_relations',2),('failure_signs',1)]:
            value=direction.get(key)
            if not isinstance(value,list) or len(value)<minimum or any(not isinstance(x,str) or not x.strip() for x in value): raise ValueError('Invalid style direction: '+key)
    source=pack['input']
    candidates=[{'path':source['local_analysis_path'],'sha256':source['analysis_sha256'],'role':'edit_target'}]
    # Select only user-authorized image references. No silent substitution or export.
    refs=consent.get('reference_record_ids',[])
    if not isinstance(refs,list) or len(refs)>4 or len(set(refs))!=len(refs):
        raise ValueError('At most four distinct references')
    selected=[]
    for rid in refs:
        ref=next((x for x in pack['references'] if x['record_id']==rid),None)
        if ref is None:raise ValueError('Reference not in handoff')
        candidates.append({'path':ref['local_analysis_path'],'sha256':ref['sha256'],'role':ref['role']})
        selected.append(ref)
    approved=consent.get('approved_images',[])
    inspected=consent.get('inspected_sha256',[])
    for image in candidates:
        path=Path(image['path'])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=image['sha256']:
            raise ValueError('Image missing or changed')
        if image['sha256'] not in inspected:raise ValueError('Image must be visually inspected before tool use')
        if not any(a.get('sha256')==image['sha256'] and a.get('generation_allowed') is True and a.get('external_export_allowed') is True for a in approved):
            raise ValueError('Missing session permission for an input/reference image')
    req=pack['request']
    lines=['Use case: style-transfer. Edit image 1; return exactly one image, not a comparison grid.',
           '只修改用户允许的部分；明确锁定项优先，未获准改变长宽比时沿用输入比例；不得新增摄影师署名。',
           '保真改图：身份、服装结构与细节优先于风格强度。' if consent['edit_mode']=='fidelity' else '风格重创作：整体落实允许范围内的主体表现、光照、空间与成像变化；用户保留项优先，不能退化为仅换背景。',
           '需求：'+req['need'],'画面方案：'+pack['visual_plan'],
           '保留：'+'；'.join(req['preserve']),'允许改变：'+'；'.join(req['allowed_changes']),'禁止：'+'；'.join(req['avoid'])]
    if consent['edit_mode']=='photographer_transform':
        lines.extend(['摄影师风格目标：'+direction['photographer_name'],
                      '选定分支：'+direction['branch_id'],
                      '观看效果：'+direction['target_effect'],
                      '共同实现的风格关系：'+'；'.join(direction['signature_relations']),
                      '主体处理：'+direction['subject_treatment'],
                      '依据与限制：'+direction['reference_basis'],
                      '避免这些失败表现：'+'；'.join(direction['failure_signs'])])
    for i,ref in enumerate(selected,2):
        lines.append(f"Image {i} is a style reference only ({ref['role']}): {ref['borrow']}. Do not copy: "+'；'.join(ref['do_not_copy']))
    if not selected:
        lines.append('未附带风格参考图，仅按上述已整理的文字关系编辑；不要声称看到了额外参考图。')
    return {'schema_version':'atelier-image-job-1','status':'READY_FOR_AGENT_TOOL_CALL',
            'tool':'image_gen.imagegen','tool_arguments':{'prompt':'\n'.join(lines),'referenced_image_paths':[i['path'] for i in candidates]},
            'input_manifest':candidates,'authorization_note':consent['user_authorization'],
            'edit_mode':consent['edit_mode'],'style_direction':direction,'max_outputs':1,'automatic_retries':0,'provider_model':None,'cost':None,
            'generated':False,'instruction':'Agent must now call the built-in image tool if generation was requested. Preparing this JSON is not completion.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--handoff',type=Path,required=True);p.add_argument('--consent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:
        job=build_job(json.loads(a.handoff.read_text()),json.loads(a.consent.read_text()))
        if a.out.exists():raise ValueError('Do not overwrite an existing job')
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(job,ensure_ascii=False,indent=2));print(str(a.out.resolve()))
    except (ValueError,KeyError,TypeError,OSError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':main()
