"""Compile all originals from one semantically selected Roversi category."""
import argparse, hashlib, json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def select_scene_records(root=ROOT, style=None, filters=None):
    catalog=json.loads((root/"references/roversi-scenes.json").read_text())
    filters=filters or {}
    if style is not None and style not in catalog['styles']: raise ValueError('Unknown direction')
    for key,value in filters.items():
        if key not in catalog['vocabulary'] or value not in catalog['vocabulary'][key]: raise ValueError(f'Unknown scene filter: {key}={value}')
    return [r for r in catalog['records'] if r['scene']['space']!='nonphoto' and (style is None or style in r['styles']) and all(r['scene'][k]==v for k,v in filters.items())]

def build(request, group, reason, selection="auto", root=ROOT, scene_filters=None, scene_category=None):
    if not isinstance(request,str) or not request.strip(): raise ValueError("Empty request")
    if not reason.strip(): raise ValueError("Selection reason required")
    if selection not in ("auto","explicit","default"): raise ValueError("Invalid selection")
    library=json.loads((root/"references/roversi-library.json").read_text())
    if scene_category:
        if group is not None or scene_filters: raise ValueError('Scene mode is independent; do not combine selectors')
        catalog=json.loads((root/'references/roversi-scenes.json').read_text())
        if scene_category not in catalog['scene_categories'] or scene_category=='unassigned': raise ValueError('Choose a classified scene')
        records=[r for r in catalog['records'] if r['scene_category']==scene_category and r['scene']['space']!='nonphoto']
        matches=[dict(code='scene-'+scene_category,name=catalog['scene_categories'][scene_category],auto_enabled=True,quality_status='experimental',references=[{k:r[k] for k in ('number','file','sha256')} for r in records])]
    else:
        matches=[g for g in library["groups"] if group in (g["code"],g["name"])]
    if len(matches)!=1: raise ValueError("Unknown direction")
    g=matches[0]
    if selection=="auto" and not g["auto_enabled"]: raise ValueError("Direction is manual-only")
    if selection=="default":
        default=library.get("personal_default") or library["default"]
        if g["code"]!=default: raise ValueError("Selected direction is not the configured default")
    if scene_filters:
        selected=select_scene_records(root, g['code'], scene_filters)
        known={r['number']:r for r in g['references']}
        for r in selected:
            if r['number'] not in known or r['sha256']!=known[r['number']]['sha256']: raise ValueError('Scene/style reference mismatch')
        if not selected: raise ValueError('No matching style and scene references; do not mix unrelated references or silently drop filters')
        g={**g,'references':[known[r['number']] for r in selected]}
    refs=[]; seen=set()
    for r in g["references"]:
        p=(root/r["file"]).resolve()
        if not p.is_relative_to(root.resolve()): raise ValueError("Reference outside skill")
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest!=r["sha256"]: raise ValueError(f"Reference changed: {r['number']}")
        if digest in seen: raise ValueError("Duplicate reference")
        seen.add(digest); refs.append(str(p))
    if not refs: raise ValueError("Empty category")
    # The built-in tool was verified to accept at most five file paths.
    try:
        from PIL import Image, ImageOps
    except ModuleNotFoundError as error:
        raise ValueError(
            "Roversi compilation requires Pillow; use the bundled workspace Python returned by load_workspace_dependencies"
        ) from error
    fingerprint=hashlib.sha256(("720x1040-v1:"+"|".join(r["sha256"] for r in g["references"])).encode()).hexdigest()[:16]
    cache=root/"assets/roversi-boards"/g["code"]/fingerprint
    cache.mkdir(parents=True,exist_ok=True)
    per_sheet=math.ceil(len(refs)/5)
    boards=[];mapping=[]
    for start in range(0,len(refs),per_sheet):
        batch=refs[start:start+per_sheet];cols=min(3,len(batch));rows=math.ceil(len(batch)/cols)
        canvas=Image.new("RGB",(cols*720,rows*1040),(238,238,238))
        for index,path in enumerate(batch):
            with Image.open(path) as im:
                im=ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((704,1024),Image.Resampling.LANCZOS)
                x=(index%cols)*720+(720-im.width)//2;y=(index//cols)*1040+(1040-im.height)//2
                canvas.paste(im,(x,y))
        target=cache/f"sheet-{len(boards)+1}.jpg"
        canvas.save(target,quality=95,subsampling=0)
        boards.append(str(target.resolve()))
        mapping.append(dict(file=str(target.resolve()),numbers=[r["number"] for r in g["references"][start:start+per_sheet]],sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    instruction="输入的是参考拼版；每个格子是一张独立原作，拼版包含该类全部 "+str(len(refs))+" 张图片。全部格子仅作为摄影风格参考，网格布局和格间留白不属于目标画面。从这组作品中参考共同的视觉处理，并允许不同作品存在变化；围绕新需求生成一张独立的新照片，不要求把全部参考的特点同时放进一个画面。人物身份、服装、动作、文字和扫描边框不作为必须复现的内容。保留用户指定的内容，不生成拼贴或参考图网格。"
    prompt="\n".join(["创作一张受 Paolo Roversi 摄影表达启发的原创编辑时装摄影。",request,instruction])
    if scene_filters:
        instruction=instruction.replace('该类全部','所选摄影表现与场景标签交集的全部').replace('该类','所选交集')
        prompt="\n".join(["创作一张受 Paolo Roversi 摄影表达启发的原创编辑时装摄影。",request,instruction])
    if scene_category:
        instruction=instruction.replace('该类全部','该场景类全部')
        prompt="\n".join(["创作一张受 Paolo Roversi 摄影表达启发的原创编辑时装摄影。",request,instruction])
    prompt += "\n" + (root/"references/roversi-default-rendering.txt").read_text(encoding="utf-8").strip()
    return dict(classification_mode="scene" if scene_category else "six_categories",scene_category=scene_category,schema_version="atelier-all-reference-1",user_request=request,direction=g["name"],group=g["code"],selection=selection,selection_reason=reason,direction_status=g.get("quality_status","unverified"),default_source=("personal" if library.get("personal_default") else "system") if selection=="default" else None,reference_count=len(refs),reference_manifest=g["references"],input_mode="all_style_scene_matches_in_contact_sheets" if scene_filters else "all_category_images_in_contact_sheets",scene_filters=scene_filters or {},reference_support="single_reference_limited" if len(refs)==1 else "unverified",original_paths=refs,board_manifest=mapping,tool_arguments=dict(prompt=prompt,referenced_image_paths=boards),generation_status="prepared_not_called",reference_attention_verified=False,human_acceptance=None)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request-file",type=Path,required=True)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--direction")
    mode.add_argument("--scene-category",choices=["backdrop","interior","built_outdoor","nature"])
    p.add_argument("--reason",required=True)
    p.add_argument("--selection",choices=["auto","explicit","default"],default="auto")
    p.add_argument("--out",type=Path,required=True)
    p.add_argument('--scene',action='append',default=[],metavar='KEY=VALUE',help='Intersect style with visible scene tags; repeat for AND filters')
    a=p.parse_args();scene_filters={}
    for item in a.scene:
        key,sep,value=item.partition('=')
        if not sep or key in scene_filters:p.error('Use distinct scene KEY=VALUE arguments')
        scene_filters[key]=value
    job=build(a.request_file.read_text(),a.direction,a.reason,a.selection,scene_filters=scene_filters,scene_category=a.scene_category)
    job['scene_filters']=scene_filters
    with a.out.open("x") as f:json.dump(job,f,ensure_ascii=False,indent=2)
