"""List visible scene matches. Does not generate or silently combine reference pools."""
import argparse,json
from prepare_reference_generation import ROOT,select_scene_records

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--style',choices=list('ABCDE'))
    p.add_argument('--scene',action='append',default=[],metavar='KEY=VALUE')
    a=p.parse_args();filters={}
    for item in a.scene:
        key,sep,value=item.partition('=')
        if not sep or key in filters:p.error('Use distinct KEY=VALUE filters')
        filters[key]=value
    rows=select_scene_records(ROOT,a.style,filters)
    print(json.dumps({'count':len(rows),'style':a.style,'filters':filters,'records':rows},ensure_ascii=False,indent=2))
