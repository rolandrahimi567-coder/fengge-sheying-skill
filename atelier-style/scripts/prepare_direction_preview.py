"""Prepare two separate direction jobs for an explicitly requested preview; no generation."""
import argparse
import json
from pathlib import Path
from prepare_reference_generation import ROOT, build


def prepare(request, directions, reasons, root=ROOT):
    if len(directions) != 2 or len(reasons) != 2:
        raise ValueError("A direction preview requires two directions and two reasons")
    library = json.loads((root / "references/roversi-library.json").read_text())
    codes = []
    for direction in directions:
        matches = [g for g in library["groups"] if direction in (g["code"], g["name"])]
        if len(matches) != 1:
            raise ValueError("Unknown direction")
        codes.append(matches[0]["code"])
    if len(set(codes)) != 2:
        raise ValueError("Preview directions must be distinct")
    jobs = [build(request, code, reason, "auto", root=root)
            for code, reason in zip(codes, reasons)]
    return dict(mode="direction_preview", user_request=request, planned_outputs=2,
                generation_status="prepared_not_called", jobs=jobs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-file", required=True, type=Path)
    parser.add_argument("--directions", required=True, nargs=2)
    parser.add_argument("--reasons", required=True, nargs=2)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output already exists; choose a new path")
    pack = prepare(args.request_file.read_text(encoding="utf-8"), args.directions, args.reasons)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(pack, handle, ensure_ascii=False, indent=2)
