"""Route one normalized Atelier specification to the selected photographer compiler."""

import argparse
import json
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import prepare_porodina_generation as porodina
import prepare_reference_generation as roversi
import prepare_tim_walker_generation as tim_walker


ALIASES = {
    "roversi": "paolo-roversi",
    "paolo-roversi": "paolo-roversi",
    "tim-walker": "tim-walker",
    "walker": "tim-walker",
    "porodina": "elizaveta-porodina",
    "elizaveta-porodina": "elizaveta-porodina",
}


def required(mapping: dict, key: str):
    value = mapping.get(key)
    if value is None or value == "" or value == []:
        raise ValueError("Missing specification field: " + key)
    return value


def compile_spec(spec: dict) -> dict:
    photographer = ALIASES.get(str(required(spec, "photographer")).strip().lower())
    if photographer is None:
        raise ValueError("Unknown photographer")
    request = str(required(spec, "user_request"))
    selection = required(spec, "selection")
    if not isinstance(selection, dict):
        raise ValueError("selection must be an object")
    options = spec.get("options") or {}

    if photographer == "paolo-roversi":
        direction = selection.get("direction")
        scene_category = selection.get("scene_category")
        if bool(direction) == bool(scene_category):
            raise ValueError("Roversi requires exactly one direction or scene_category")
        job = roversi.build(
            request=request,
            group=direction,
            reason=str(required(selection, "selection_reason")),
            selection=selection.get("selection_mode", "auto"),
            scene_filters=selection.get("scene_filters") or {},
            scene_category=scene_category,
        )
    elif photographer == "tim-walker":
        clothing = spec.get("clothing_reference")
        clothing_path = Path(clothing["path"]) if clothing else None
        clothing_plan = clothing.get("plan") if clothing else None
        job = tim_walker.build(
            request=request,
            category=str(required(selection, "category")),
            photo_sequences=[int(value) for value in required(selection, "photo_reference_sequences")],
            selection_reason=str(required(selection, "selection_reason")),
            inspection_note=str(required(selection, "visual_inspection_note")),
            reference_plan=str(required(selection, "reference_plan")),
            pair_consistency=selection.get("pair_consistency"),
            clothing_reference=clothing_path,
            clothing_plan=clothing_plan,
            no_clothing_reference_reason=options.get("no_clothing_reference_reason"),
            explicit_casting=bool(options.get("explicit_casting", False)),
            background_override=bool(options.get("background_override", False)),
        )
    else:
        clothing = spec.get("clothing_reference")
        clothing_path = Path(clothing["path"]) if clothing else None
        clothing_plan = clothing.get("plan") if clothing else None
        job = porodina.build(
            request=request,
            photo_ids=[str(value).zfill(3) for value in required(selection, "photo_reference_ids")],
            selection_reason=str(required(selection, "selection_reason")),
            inspection_note=str(required(selection, "visual_inspection_note")),
            reference_plan=str(required(selection, "reference_plan")),
            category=selection.get("category"),
            axis_codes=selection.get("research_axes") or [],
            pair_consistency=selection.get("pair_consistency"),
            clothing_reference=clothing_path,
            clothing_plan=clothing_plan,
            no_clothing_reference_reason=options.get("no_clothing_reference_reason"),
            explicit_casting=bool(options.get("explicit_casting", False)),
            background_override=bool(options.get("background_override", False)),
        )
    job.setdefault("tool", "image_gen.imagegen")
    job.setdefault("output_count", 1)
    job.setdefault("automatic_retries", 0)
    job.setdefault("human_review", "unreviewed")
    job.setdefault("validated_recipe", False)
    return {"atelier_router_version": 2, "photographer": photographer, **job}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    job = compile_spec(spec)
    if args.out.exists():
        raise ValueError("Do not overwrite an existing job")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.out.resolve())


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
