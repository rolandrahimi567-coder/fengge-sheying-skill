"""Photographer-scoped brief preparation, local only; never calls a provider."""
import json,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'references/photographers'
def catalog():return json.loads((P/'catalog.json').read_text())
def inventory():
 p=Path(json.loads((P/'scope.json').read_text())['inventory_file'])
 return json.loads((p if p.is_absolute() else ROOT/p).read_text())
def checked_item(record_id):
 item=next((x for x in inventory() if x['record_id']==record_id),None)
 if item is None:raise ValueError('OUTSIDE_SELECTED_150')
 p=Path(item['local_analysis_path'])
 p=p if p.is_absolute() else ROOT/p
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['analysis_sha256']:raise ValueError('SOURCE_IMAGE_MISSING_OR_CHANGED')
 return item

def plan(photographer_id,branch_id,record_id,mode='edit'):
 if mode not in ('edit','new'):raise ValueError('INVALID_MODE')
 c=catalog();profile=next((p for p in c['profiles'] if p['id']==photographer_id),None)
 if profile is None:raise ValueError('UNKNOWN_PHOTOGRAPHER')
 branch=next((b for b in c['branches'] if b['id']==branch_id and b['photographer_id']==photographer_id),None)
 if branch is None:raise ValueError('BRANCH_NOT_OWNED_BY_PHOTOGRAPHER')
 item=checked_item(record_id);p=P/'recipes'/f'{branch_id}.json'
 if not p.exists():return {'status':'BRANCH_CARD_ONLY','photographer':profile['name'],'branch':branch['name'],'prompt':None,'generated':False}
 recipe=json.loads(p.read_text())
 for ref in recipe['references']:
  source=checked_item(ref['record_id'])
  if source['photographer_label']!=profile['name'] or source['analysis_sha256']!=ref['analysis_sha256']:raise ValueError('REFERENCE_ATTRIBUTION_OR_HASH_CONFLICT')
 note=recipe['input_notes'].get(str(item['sequence']));is_test=note is not None
 common='目标摄影师参考：'+profile['name']+'；候选分支：'+branch['name']+'。模式：'+mode+'。保持摄影质感。'
 fidelity='保留输入人物身份、服装版型、图案和明确锁定的对象；只改获准部分。' if mode=='edit' else '允许新主体；不声称服装与原商品完全一致，不复制完整作品或署名。'
 prompt='\n'.join([common,fidelity,'针对当前图：'+note,'组合特征：',*recipe['signature'],'操作：',*recipe['steps'],'检查：',*recipe['checks']]) if is_test else None
 return {'photographer_id':photographer_id,'branch_id':branch_id,'record_id':record_id,'sequence':item['sequence'],'mode':mode,'status':'BLOCKED_RIGHTS_AND_PROVIDER_UNSELECTED' if is_test else 'NEEDS_INPUT_VISUAL_REVIEW','prompt':prompt,'baseline_prompt':common+fidelity+(note or '') if is_test else None,'reference_record_ids':[x['record_id'] for x in recipe['references']],'attribution_status':'FILENAME_LABEL_ONLY_NOT_VERIFIED','quality_status':'NOT_GENERATION_VALIDATED','generated':False,'paid_calls':0}

def main():
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='cmd',required=True);sub.add_parser('list');b=sub.add_parser('branches');b.add_argument('--photographer',required=True);q=sub.add_parser('plan');q.add_argument('--photographer',required=True);q.add_argument('--branch',required=True);q.add_argument('--record-id',required=True);q.add_argument('--mode',choices=['edit','new'],default='edit');a=parser.parse_args()
 result=catalog()['profiles'] if a.cmd=='list' else [b for b in catalog()['branches'] if b['photographer_id']==a.photographer] if a.cmd=='branches' else plan(a.photographer,a.branch,a.record_id,a.mode)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
