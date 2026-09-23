"""Offline input-specific preparation. No provider client and no permission override."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def asset_path(value):
 p=Path(value)
 return p if p.is_absolute() else ROOT/p
def recipes():return {r['id']:r for p in sorted((ROOT/'references/recipes').glob('*.json')) if (r:=json.loads(p.read_text()))}
def plan(recipe_id,record_id,mode='edit'):
 if mode not in ('edit','new'):raise ValueError('INVALID_MODE')
 recipe=recipes().get(recipe_id)
 if recipe is None:raise ValueError('UNKNOWN_RECIPE')
 index=json.loads((ROOT/'references/style-index.json').read_text());item=next((x for x in index['items'] if x['record_id']==record_id),None)
 if item is None:raise ValueError('RECORD_OUTSIDE_FROZEN_SCOPE')
 # Check all reference hashes too: a valid input does not prove references are intact.
 for rid in [record_id]+[r['record_id'] for r in recipe['references']]:
  row=next(x for x in index['items'] if x['record_id']==rid);p=asset_path(row['local_analysis_path'])
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['analysis_image']['sha256']:raise ValueError('SOURCE_IMAGE_MISSING_OR_CHANGED')
 negative=record_id in recipe['negative_record_ids'];reviewed=record_id in recipe['held_out_record_ids'] or any(r['record_id']==record_id for r in recipe['references'])
 boundary=recipe_id=='pale-layer-separation' and item['sequence']==19
 applicability='UNSUITABLE_EXAMPLE' if negative else 'BOUNDARY_REQUIRES_BACKGROUND_PERMISSION' if boundary else 'ASSISTANT_REVIEWED_CANDIDATE' if reviewed else 'NEEDS_INPUT_SPECIFIC_REVIEW'
 fact=item['screening'].get('visible_note');instruction=item.get('input_adaptation') if record_id in recipe['held_out_record_ids'] else None
 common='目标：'+recipe['name']+'。模式：'+mode+'。'+recipe['fidelity'][mode]+'仅输出摄影质感；保留未授权修改的文字、人物、衣物和物件；不凭空补造细节。'
 prompt=None
 if reviewed and not negative:
  prompt='\n'.join([common,'当前图可见依据：'+(fact or '尚缺针对本图的观察'),'当前图执行边界：'+(instruction or '参考图只用于提炼关系；编辑前仍需用户明确变化范围。'),'关系优先级：',*[f"{x['rank']}. {x['rule']}" for x in recipe['must_preserve']],'操作：',*recipe['steps'],'不得照搬：',*recipe['must_not_copy']])
 return {'recipe_id':recipe_id,'recipe_version':recipe['version'],'record_id':record_id,'sequence':item['sequence'],'input_sha256':item['analysis_image']['sha256'],'mode':mode,'status':'NO_FIT' if negative else 'NEEDS_VISUAL_REVIEW' if not reviewed else 'BLOCKED_RIGHTS','applicability':applicability,'permission_reason':'NO_LIVE_AUTHORIZED_CONTEXT_SELECTED_FOR_INPUT_AND_REFERENCES','baseline_prompt':common if prompt else None,'prompt':prompt,'input_observation':fact,'input_adaptation':instruction,'checks':recipe['checks'],'evidence_file':item.get('evidence_file'),'generated':False,'paid_calls':0}
def recommend_methods(record_id):
 index=json.loads((ROOT/'references/style-index.json').read_text());item=next((x for x in index['items'] if x['record_id']==record_id),None)
 if item is None:raise ValueError('RECORD_OUTSIDE_FROZEN_SCOPE')
 image=asset_path(item['local_analysis_path'])
 if not image.is_file() or hashlib.sha256(image.read_bytes()).hexdigest()!=item['analysis_image']['sha256']:raise ValueError('SOURCE_IMAGE_MISSING_OR_CHANGED')
 rs=recipes();choices=[]
 for rid in item['candidate_groups']:
  r=rs.get(rid)
  if r is None:raise ValueError('BROKEN_RECIPE_REFERENCE')
  choices.append({'id':rid,'name':r['name'],'selection_basis':'CONTACT_SCREEN_CANDIDATE_REQUIRES_CURRENT_VISUAL_REVIEW','distinction':r.get('distinction'),'suitable':r['suitable'],'unsuitable':r['unsuitable'],'reference_sequences':[v['sequence'] for v in r['references']]})
 return {'record_id':record_id,'sequence':item['sequence'],'status':'CANDIDATES_NEED_REVIEW' if choices else 'NO_CONFIRMED_RECIPE','candidates':choices,'ranked':False,'note':'候选关联读取，不是语义检索分数；请结合用户要求和原图选择，不默认第一项最合适。','paid_calls':0}
def styles():return json.loads((ROOT/'references/style-catalog.json').read_text())['styles']
def recommend(record_id):
 old=recommend_methods(record_id) # preserves source identity checks
 index=json.loads((ROOT/'references/style-index.json').read_text());item=next(x for x in index['items'] if x['record_id']==record_id)
 candidates=[s for s in styles() if s['id'] in item['style_candidates']]
 return {'record_id':record_id,'sequence':item['sequence'],'status':'CANDIDATES_NEED_REVIEW' if candidates else 'NO_CONFIRMED_STYLE','candidates':candidates,'ranked':False,'primary_style':None,'paid_calls':0}
def style_plan(style_id,record_id,mode='edit',treatment='photographic'):
 if mode not in ('edit','new'):raise ValueError('INVALID_MODE')
 st=next((s for s in styles() if s['id']==style_id),None)
 if st is None:raise ValueError('UNKNOWN_STYLE')
 source=recommend(record_id)
 treatments=json.loads((ROOT/'references/output-treatments.json').read_text())['treatments'];t=next((x for x in treatments if x['id']==treatment),None)
 if t is None:raise ValueError('UNKNOWN_OUTPUT_TREATMENT')
 status='OUTPUT_TREATMENT_NOT_IMPLEMENTED' if treatment!='photographic' else 'NEEDS_INPUT_SPECIFIC_REVIEW'
 return {'style_id':style_id,'style_name':st['name'],'record_id':record_id,'mode':mode,'treatment':treatment,'status':status,'candidate_association':any(s['id']==style_id for s in source['candidates']),'judgment_focus':st['judgment_focus'],'controls':st['controls'],'exclusion':st['exclusion'],'available_method_ids':st['method_ids'],'recipe_readiness':st['readiness'],'prompt':None,'next_step':'先检查当前原图、主导关系和保留项，再选对应方法；不自动采用全部方法。','generated':False,'paid_calls':0}
def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True);s.add_parser('list');s.add_parser('methods');q=s.add_parser('plan');g=q.add_mutually_exclusive_group(required=True);g.add_argument('--recipe');g.add_argument('--style');q.add_argument('--record-id',required=True);q.add_argument('--mode',choices=['edit','new'],default='edit');q.add_argument('--treatment',default='photographic');z=s.add_parser('recommend');z.add_argument('--record-id',required=True);a=p.parse_args()
 if a.cmd=='list':result=styles()
 elif a.cmd=='methods':result=[{'id':x['id'],'name':x['name']} for x in recipes().values()]
 elif a.cmd=='recommend':result=recommend(a.record_id)
 elif a.style:result=style_plan(a.style,a.record_id,a.mode,a.treatment)
 elif a.treatment!='photographic':raise ValueError('OUTPUT_TREATMENT_NOT_IMPLEMENTED')
 else:result=plan(a.recipe,a.record_id,a.mode)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
