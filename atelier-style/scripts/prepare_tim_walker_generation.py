"""Compile an inspected Tim Walker reference plan into one built-in imagegen job."""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIM_WALKER = ROOT / "references" / "tim-walker"


def read_nonempty(path: Path, label: str) -> str:
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError(f"{label} is empty")
    return value


def load_index() -> dict[int, dict]:
    records = json.loads((TIM_WALKER / "reference-index.json").read_text(encoding="utf-8"))
    return {int(record["sequence"]): record for record in records}


def verified_reference(record: dict) -> dict:
    path = Path(record["reference_path"])
    path = (path if path.is_absolute() else ROOT / path).resolve()
    if not path.is_file():
        raise ValueError(f"Missing reference: {record['sequence']}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != record["sha256"]:
        raise ValueError(f"Reference changed: {record['sequence']}")
    return {
        "sequence": record["sequence"],
        "path": str(path),
        "sha256": digest,
        "group_code": record["group_code"],
        "primary_group": record["primary_group"],
        "attribution": record["attribution"],
        "generation_validated": record["generation_validated"],
    }


def build(
    request: str,
    category: str,
    photo_sequences: list[int],
    selection_reason: str,
    inspection_note: str,
    reference_plan: str,
    pair_consistency: str | None = None,
    clothing_reference: Path | None = None,
    clothing_plan: str | None = None,
    no_clothing_reference_reason: str | None = None,
    explicit_casting: bool = False,
    background_override: bool = False,
) -> dict:
    request = request.strip()
    selection_reason = selection_reason.strip()
    inspection_note = inspection_note.strip()
    reference_plan = reference_plan.strip()
    if not request or not selection_reason or not inspection_note or not reference_plan:
        raise ValueError("Request, selection reason, inspection note and reference plan are required")
    if len(photo_sequences) not in (1, 2) or len(set(photo_sequences)) != len(photo_sequences):
        raise ValueError("Choose one or two distinct photographic references")
    if len(photo_sequences) == 2 and pair_consistency != "confirmed":
        raise ValueError("Two references require --pair-consistency confirmed after visual inspection")
    if len(photo_sequences) == 1 and pair_consistency:
        raise ValueError("Pair consistency applies only to two photographic references")

    rules = json.loads((TIM_WALKER / "category-rules.json").read_text(encoding="utf-8"))
    if category not in rules:
        raise ValueError("Unknown Tim Walker category: " + category)
    index = load_index()
    unknown = [value for value in photo_sequences if value not in index]
    if unknown:
        raise ValueError("Unknown Tim Walker reference: " + ", ".join(map(str, unknown)))
    mismatched = [value for value in photo_sequences if index[value]["group_code"] != category]
    if mismatched:
        raise ValueError("Reference does not belong to selected category: " + ", ".join(map(str, mismatched)))

    manifest = [verified_reference(index[value]) for value in photo_sequences]
    paths = [record["path"] for record in manifest]
    roles = [f"摄影原作{record['sequence']}" for record in manifest]
    if len(manifest) == 1:
        role_line = (
            "输入图1是唯一摄影原作，以其中可见的衣形、身体、空间、尺度、材料和光线关系控制本次画面。"
            "具体参考关系：" + reference_plan
        )
    else:
        role_line = (
            "输入图1和输入图2是经完整看图后确认风格一致的摄影原作，共同控制本次可见的衣形、身体、"
            "空间、尺度、材料和光线关系。具体参考关系：" + reference_plan
        )

    clothing_manifest = None
    no_clothing_reference_reason = (no_clothing_reference_reason or "").strip() or None
    if clothing_reference is None and clothing_plan:
        raise ValueError("Clothing plan requires a clothing reference")
    if clothing_reference is None and not no_clothing_reference_reason:
        raise ValueError(
            "Tim Walker defaults to one clothing reference; provide --clothing-reference and "
            "--clothing-plan-file, or record an explicit user override with "
            "--no-clothing-reference-reason"
        )
    if clothing_reference is not None and no_clothing_reference_reason:
        raise ValueError("Choose a clothing reference or an explicit no-clothing reason, not both")
    if clothing_reference is not None:
        if not clothing_plan or not clothing_plan.strip():
            raise ValueError("Clothing reference requires a clothing plan")
        clothing_path = clothing_reference.resolve()
        if not clothing_path.is_file():
            raise ValueError("Missing clothing reference")
        clothing_manifest = {
            "path": str(clothing_path),
            "sha256": hashlib.sha256(clothing_path.read_bytes()).hexdigest(),
            "role": "服装参考",
        }
        paths.append(str(clothing_path))
        roles.append("服装参考")
        role_line += (
            f" 输入图{len(paths)}是独立服装参考，只控制服装轮廓、结构、材料、工艺与用户指定颜色："
            + clothing_plan.strip()
            + "；不采用其中的模特身份、姿势、构图、景别、背景、秀场、建筑、观众、灯光或整体调色。"
            "摄影原作继续控制衣形与身体的关系、构图、人物尺度、空间、光线和整体摄影表达；两类参考冲突时，"
            "优先遵守用户题材，并保持摄影原作的画面关系与服装参考的衣装职责分离。"
        )

    prompt_parts = [
        "创作一张受 Tim Walker 摄影表达启发的原创艺术时装摄影。",
        "用户题材与要求：" + request,
        role_line,
        (
            "把人物、衣形、道具和空间组织成一个完整而可信的摄影场景。只采用参考中明确可见的画面关系，"
            "不要把巨大道具、梦幻森林、复古室内、拖影或电影冷暖光当作固定风格标签。"
            "改变参考人物身份、具体服装、独特道具和精确姿势，除非用户明确要求保留。"
        ),
        (
            "保持真实皮肤、衣料厚度与重量、身体支撑及人物和环境的接触关系。"
            "不要使用塑料渲染、蜡质磨皮、统一锐化或去色来制造摄影感。"
        ),
    ]
    if not explicit_casting:
        prompt_parts.append("用户未明确选角时，使用虚构的非亚裔成年人物；人物身份与摄影原作不同。")
    if not background_override:
        prompt_parts.append(
            "背景遵循摄影原作支持的空间形式、密度、明暗分区和人物比例；平面色底不能擅自扩写为街道、房间或建筑。"
        )
    prompt_parts.append("不要文字、水印、参考图网格或并列比较版面。")

    return {
        "schema_version": "atelier-tim-walker-compiler-2",
        "workflow": "tim_walker_compiled_reference_generation",
        "user_request": request,
        "category": {"code": category, **rules[category]},
        "selection_reason": selection_reason,
        "visual_inspection_note": inspection_note,
        "pair_consistency": pair_consistency or "not_applicable",
        "reference_plan": reference_plan,
        "reference_manifest": manifest,
        "clothing_reference": clothing_manifest,
        "no_clothing_reference_reason": no_clothing_reference_reason,
        "input_roles": roles,
        "tool": "image_gen.imagegen",
        "tool_arguments": {"prompt": "\n\n".join(prompt_parts), "referenced_image_paths": paths},
        "generation_status": "compiled_not_called",
        "output_count": 1,
        "automatic_retries": 0,
        "human_review": "unreviewed",
        "validated_recipe": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--photo-ref", action="append", type=int, required=True, dest="photo_refs")
    parser.add_argument("--selection-reason", required=True)
    parser.add_argument("--inspection-file", type=Path, required=True)
    parser.add_argument("--reference-plan-file", type=Path, required=True)
    parser.add_argument("--pair-consistency", choices=["confirmed"])
    parser.add_argument("--clothing-reference", type=Path)
    parser.add_argument("--clothing-plan-file", type=Path)
    parser.add_argument("--no-clothing-reference-reason")
    parser.add_argument("--explicit-casting", action="store_true")
    parser.add_argument("--background-override", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    clothing_plan = None
    if args.clothing_plan_file:
        clothing_plan = read_nonempty(args.clothing_plan_file, "Clothing plan")
    job = build(
        request=read_nonempty(args.request_file, "User request"),
        category=args.category,
        photo_sequences=args.photo_refs,
        selection_reason=args.selection_reason,
        inspection_note=read_nonempty(args.inspection_file, "Inspection note"),
        reference_plan=read_nonempty(args.reference_plan_file, "Reference plan"),
        pair_consistency=args.pair_consistency,
        clothing_reference=args.clothing_reference,
        clothing_plan=clothing_plan,
        no_clothing_reference_reason=args.no_clothing_reference_reason,
        explicit_casting=args.explicit_casting,
        background_override=args.background_override,
    )
    if args.out.exists():
        raise ValueError("Do not overwrite an existing job")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.out.resolve())


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(str(error))
