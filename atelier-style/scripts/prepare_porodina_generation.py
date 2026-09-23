"""Compile an inspected Porodina reference plan into one built-in imagegen job."""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORODINA = ROOT / "references" / "porodina"
KNOWN_INCOMPATIBLE_PAIRS = {frozenset({"082", "147"})}


def read_nonempty(path: Path, label: str) -> str:
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError(f"{label} is empty")
    return value


def load_index() -> dict[str, dict]:
    records = json.loads((PORODINA / "reference-index.json").read_text(encoding="utf-8"))
    return {record["id"]: record for record in records}


def load_branches() -> dict[str, dict]:
    records = json.loads((PORODINA / "branches.json").read_text(encoding="utf-8"))
    return {record["code"]: record for record in records}


def verified_reference(record: dict) -> dict:
    path = Path(record["original_path"])
    path = (path if path.is_absolute() else ROOT / path).resolve()
    if not path.is_file():
        raise ValueError(f"Missing reference: {record['id']}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != record["sha256"]:
        raise ValueError(f"Reference changed: {record['id']}")
    return {
        "id": record["id"],
        "project": record["project"],
        "path": str(path),
        "sha256": digest,
        "previous_category": record["previous_category"],
        "research_axes": record.get("research_axes", []),
        "human_accepted": record.get("human_accepted"),
    }


def build(
    request: str,
    photo_ids: list[str],
    selection_reason: str,
    inspection_note: str,
    reference_plan: str,
    category: str | None = None,
    axis_codes: list[str] | None = None,
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
    axis_codes = axis_codes or []
    if not request:
        raise ValueError("Empty user request")
    if not selection_reason or not inspection_note or not reference_plan:
        raise ValueError("Selection reason, inspection note and reference plan are required")
    if len(photo_ids) not in (1, 2) or len(set(photo_ids)) != len(photo_ids):
        raise ValueError("Choose one or two distinct photographic references")
    if len(photo_ids) == 2 and pair_consistency != "confirmed":
        raise ValueError("Two references require --pair-consistency confirmed after visual inspection")
    if frozenset(photo_ids) in KNOWN_INCOMPATIBLE_PAIRS:
        raise ValueError("References 082 and 147 are a user-confirmed incompatible style pair")
    if len(photo_ids) == 1 and pair_consistency:
        raise ValueError("Pair consistency applies only to two photographic references")
    if not category and not axis_codes:
        raise ValueError("Choose at least one category or research axis")

    index = load_index()
    branches = load_branches()
    unknown_axes = [code for code in axis_codes if code not in branches]
    if unknown_axes:
        raise ValueError("Unknown research axis: " + ", ".join(unknown_axes))
    unknown_refs = [rid for rid in photo_ids if rid not in index]
    if unknown_refs:
        raise ValueError("Unknown photographic reference: " + ", ".join(unknown_refs))

    known_categories = {record["previous_category"] for record in index.values()}
    if category and category not in known_categories:
        raise ValueError("Unknown category: " + category)
    if category:
        mismatched = [rid for rid in photo_ids if index[rid]["previous_category"] != category]
        if mismatched:
            raise ValueError(
                "Reference does not belong to selected category: " + ", ".join(mismatched)
            )

    photo_manifest = [verified_reference(index[rid]) for rid in photo_ids]
    referenced_paths = [record["path"] for record in photo_manifest]
    input_roles = [f"摄影原作{record['id']}" for record in photo_manifest]

    if len(photo_manifest) == 1:
        role_line = (
            "输入图1是唯一摄影原作，控制本次明确选定的构图、人物与空间关系、"
            "光色、遮挡、虚实和材料表达。具体参考关系：" + reference_plan
        )
    else:
        role_line = (
            "输入图1和输入图2是经完整看图后确认风格一致的摄影原作，共同控制本次明确选定的"
            "构图、人物与空间关系、光色、遮挡、虚实和材料表达。具体参考关系：" + reference_plan
        )

    clothing_manifest = None
    no_clothing_reference_reason = (no_clothing_reference_reason or "").strip() or None
    if clothing_reference is None and clothing_plan:
        raise ValueError("Clothing plan requires a clothing reference")
    if clothing_reference is None and not no_clothing_reference_reason:
        raise ValueError(
            "Porodina defaults to one clothing reference; provide --clothing-reference and "
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
        referenced_paths.append(str(clothing_path))
        input_roles.append("服装参考")
        role_line += (
            f" 输入图{len(referenced_paths)}是独立服装参考，只控制服装轮廓、结构、材料、工艺与用户指定颜色："
            + clothing_plan.strip()
            + "；不采用其中的模特身份、姿势、构图、景别、背景、秀场、建筑、观众、灯光或整体调色。"
            "摄影原作继续控制构图、人物大小与方向、空间、光色、遮挡、虚实和运动表达；两类参考冲突时，"
            "优先遵守用户题材，并保持摄影原作的画面关系与服装参考的衣装职责分离。"
        )

    prompt_parts = [
        "创作一张受 Elizaveta Porodina 摄影表达启发的原创艺术时装摄影。",
        "用户题材与要求：" + request,
        role_line,
        (
            "保持高饱和、艳丽、虚幻与真实摄影同时成立。鲜艳颜色集中在受光皮肤、衣料或重叠区域，"
            "保留安静的暗部或中性色区域；虚幻感来自姿态、衣形、色彩、遮挡、曝光重叠和局部虚实，"
            "不依赖超能力式道具或统一发光边缘。不要复制参考人物身份、服装和精确姿势，除非用户要求明确保留。"
        ),
        (
            "人物保持真实骨骼、身体承重和衣料接触。皮肤有自然且不完全均一的细微色泽，"
            "五官与表情保留轻微不对称，眼睛不过度放大或玻璃化；高光随骨骼与皮肤起伏变化。"
            "手指关节、支撑脚和衣物受压褶皱可信。不要动漫、塑料渲染、蜡质磨皮、夸张毛孔或全脸统一锐化。"
        ),
    ]
    if not explicit_casting:
        prompt_parts.append("用户未明确选角时，使用虚构的非亚裔成年女性；人物身份与摄影原作不同。")
    if not background_override:
        prompt_parts.append(
            "背景遵循摄影原作可见的空间形式；原作没有墙壁或建筑时，不自行添加墙壁、混凝土通道、门窗或建筑空间。"
        )
    prompt_parts.append("不要文字、水印、参考图网格或并列比较版面。")
    prompt = "\n\n".join(prompt_parts)

    axis_manifest = [
        {
            "code": code,
            "title": branches[code]["title"],
            "status": branches[code]["status"],
            "evidence_ids": branches[code]["evidence_ids"],
        }
        for code in axis_codes
    ]
    return {
        "schema_version": "atelier-porodina-compiler-2",
        "workflow": "porodina_compiled_reference_generation",
        "user_request": request,
        "category": category,
        "research_axes": axis_manifest,
        "selection_reason": selection_reason,
        "visual_inspection_note": inspection_note,
        "pair_consistency": pair_consistency or "not_applicable",
        "reference_plan": reference_plan,
        "reference_manifest": photo_manifest,
        "clothing_reference": clothing_manifest,
        "no_clothing_reference_reason": no_clothing_reference_reason,
        "input_roles": input_roles,
        "tool": "image_gen.imagegen",
        "tool_arguments": {
            "prompt": prompt,
            "referenced_image_paths": referenced_paths,
        },
        "generation_status": "compiled_not_called",
        "output_count": 1,
        "automatic_retries": 0,
        "human_review": "unreviewed",
        "validated_recipe": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-file", type=Path, required=True)
    parser.add_argument("--photo-ref", action="append", required=True, dest="photo_refs")
    parser.add_argument("--category")
    parser.add_argument("--axis", action="append", default=[], dest="axes")
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
        photo_ids=args.photo_refs,
        selection_reason=args.selection_reason,
        inspection_note=read_nonempty(args.inspection_file, "Inspection note"),
        reference_plan=read_nonempty(args.reference_plan_file, "Reference plan"),
        category=args.category,
        axis_codes=args.axes,
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
