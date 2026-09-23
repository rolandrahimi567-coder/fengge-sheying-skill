"""Validate recipe cross-references and pilot boundaries without source writes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate():
    index=json.loads((ROOT/'references/style-index.json').read_text());items={x['record_id']:x for x in index['items']}
    assert len(items)==len(index['items'])==300,'SCOPE_OR_DUPLICATE_ID'
    refs=set();tests=set();recipes=list((ROOT/'references/recipes').glob('*.json'))
    catalog=json.loads((ROOT/'references/recipe-catalog.json').read_text());assert {p.stem for p in recipes}=={r['id'] for r in catalog['recipes']},'RECIPE_CATALOG_MISMATCH'
    for p in recipes:
        r=json.loads(p.read_text());assert r['id']==p.stem
        assert r['status']=='DRAFT_NOT_CROSS_IMAGE_VALIDATED'
        assert 3<=len(r['references'])<=5 and len(r['held_out_record_ids']) in (0,2)
        assert [x['rank'] for x in r['must_preserve']]==list(range(1,len(r['must_preserve'])+1))
        for ref in r['references']:
            assert ref['record_id'] in items and ref['analysis_sha256']==items[ref['record_id']]['analysis_image']['sha256']
            assert ref['role'];refs.add(ref['record_id'])
        assert all(x in items for x in r['held_out_record_ids']+r['negative_record_ids'])
        tests.update(r['held_out_record_ids'])
        assert r['steps'] and r['unsuitable'] and r['checks'] and r['must_not_copy']
    assert not refs&tests,'REFERENCE_TEST_LEAKAGE'
    assert len(tests)==6,'TEST_COUNT'
    assert all(set(x['candidate_groups']) <= {p.stem for p in recipes} for x in items.values()),'UNKNOWN_GROUP'
    assert all(x['permissions']['selected_context_id'] is None for x in items.values())
    styles=json.loads((ROOT/'references/style-catalog.json').read_text())['styles']
    assert len(styles)==8 and len({s['id'] for s in styles})==8,'STYLE_DIRECTIONS'
    assert sum(s['pilot_priority'] for s in styles)==3,'PILOT_PRIORITY'
    for style in styles:
        assert set(style['method_ids'])<={p.stem for p in recipes},'UNKNOWN_STYLE_METHOD'
        for ref in style['references']:
            assert ref['analysis_sha256']==items[ref['record_id']]['analysis_image']['sha256'],'STYLE_REF_HASH'
    assert all(set(x['style_candidates'])<={s['id'] for s in styles} and x['primary_style'] is None for x in items.values()),'STYLE_ASSIGNMENT'
    return {'items':len(items),'recipes':len(recipes),'reference_images':len(refs),'held_out_images':len(tests),'status':'STRUCTURE_VALID_NOT_EFFECTIVENESS_VALIDATED'}
if __name__=='__main__':print(json.dumps(validate(),ensure_ascii=False,indent=2))
