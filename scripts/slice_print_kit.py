#!/usr/bin/env python3
"""Validate real Bambu Studio toolpaths without sending anything to a printer.

The official application's bundled profiles are flattened, including inherited
and included settings. One STL is sliced at a time. Temporary G-code files
are inspected and then deleted, keeping only JSON evidence and console logs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "exports/dragon-pla-kit-v03/work/slicer"
DEFAULT_APP = next((p for p in [Path("/Applications/BambuStudio.app"),
    Path("/tmp/dragon-bambu-volume/BambuStudio.app")] if p.exists()),
    Path("/Applications/BambuStudio.app"))


def profiles(app: Path) -> tuple[Path, Path, Path]:
    root = app / "Contents/Resources/profiles/BBL"
    index = {}
    for path in root.rglob("*.json"):
        try:
            doc = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        index[path.stem] = doc
        if doc.get("name"):
            index[doc["name"]] = doc

    def resolve(name, stack=()):
        if name in stack:
            raise ValueError(f"Cyclic preset inheritance: {stack} -> {name}")
        doc = index[name]
        result = {}
        if doc.get("inherits"):
            result.update(resolve(doc["inherits"], stack + (name,)))
        for included in doc.get("include", []):
            result.update(resolve(included, stack + (name,)))
        result.update(doc)
        result.pop("inherits", None)
        result.pop("include", None)
        return result

    configs = [
        ("machine", resolve("Bambu Lab X1 Carbon 0.4 nozzle")),
        ("process", resolve("0.16mm High Quality @BBL X1C")),
        ("filament", resolve("Generic PLA")),
    ]
    configs[1][1].update({
        "enable_support": "1", "support_type": "tree(auto)",
        "support_on_build_plate_only": "1", "support_threshold_angle": "25",
        "brim_type": "outer_only", "brim_width": "3", "brim_object_gap": "0.1",
        "wall_loops": "3", "sparse_infill_density": "15%", "sparse_infill_pattern": "gyroid",
        "curr_bed_type": "Textured PEI Plate", "enable_prime_tower": "0",
    })
    outputs = []
    for kind, doc in configs:
        path = WORK / f"resolved-{kind}.json"
        path.write_text(json.dumps(doc, indent=2))
        outputs.append(path)
    (WORK / "profile-assumptions.json").write_text(json.dumps({
        "printer": "Bambu Lab X1 Carbon", "nozzle_mm": 0.4,
        "material": "Generic PLA", "layer_height_mm": 0.16,
        "process_base": "0.16mm High Quality @BBL X1C",
        "plate_assumption": "Textured PEI Plate; user must select their actual plate",
        "supports": "automatic tree supports, build plate only, 25 degree threshold",
        "brim_mm": 3, "wall_loops": 3, "infill_percent": 15,
        "profile_source": str(root),
        "documentation": "https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage",
        "printer_communication": "None. Offline validation only; no G-code delivered for direct printing.",
    }, indent=2))
    return tuple(outputs)


def inspect_gcode(lines):
    counts = {"lines": 0, "extrusion_moves": 0, "layer_changes": 0,
              "support_markers": 0, "support_extrusion_moves": 0, "brim_markers": 0}
    support = False
    summaries = []
    for raw in lines:
        line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        counts["lines"] += 1
        if "LAYER_CHANGE" in line or "CHANGE_LAYER" in line:
            counts["layer_changes"] += 1
        if line.startswith("; FEATURE:") or line.startswith(";TYPE:"):
            support = "support" in line.lower()
            counts["support_markers"] += int(support)
            counts["brim_markers"] += int("brim" in line.lower())
        if re.match(r"G[123] ", line) and re.search(r"\bE[-+0-9.]", line):
            counts["extrusion_moves"] += 1
            counts["support_extrusion_moves"] += int(support)
        if line.startswith(";") and any(k in line.lower() for k in
              ("total estimated time", "total filament", "filament used", "model printing time")):
            summaries.append(line.strip())
    counts["summary_comments"] = summaries
    return counts


def slice_one(app, stl, config, keep_project=False):
    key = stl.parent.name + "_" + stl.stem
    out = WORK / key
    out.mkdir(exist_ok=True)
    project = out / "validation.3mf"
    machine, process, filament = config
    plate = None
    manifest = ROOT / "exports/dragon-pla-kit-v03/manifest.json"
    if manifest.exists():
        inventory = json.loads(manifest.read_text())
        plate = next((p for p in inventory.get("plates", [])
            if (manifest.parent / p["file"]).resolve() == stl), None)
    support_enabled = plate["supports_required"] if plate else (
        "_flat_" not in stl.stem and not stl.stem.startswith("test_"))
    brim = 5 if plate and any(p["name"] in {"head_platform_snout","test_head_platform_peg_A"}
        for p in plate["parts"]) else 3
    settings = json.loads(process.read_text())
    settings.update(enable_support="1" if support_enabled else "0", brim_width=str(brim))
    process = out / "process.json"
    process.write_text(json.dumps(settings, indent=2))
    command = [str(app / "Contents/MacOS/BambuStudio"), "--datadir", str(WORK / "appdata"),
        "--debug", "2", "--load-settings", f"{machine};{process}",
        "--load-filaments", str(filament), "--curr-bed-type", "Textured PEI Plate",
        "--arrange", "0", "--orient", "0", "--ensure-on-bed", "--slice", "0",
        "--mstpp", "480", "--outputdir", str(out), str(stl)]
    started = time.monotonic()
    result = {"input": str(stl.relative_to(ROOT)) if stl.is_relative_to(ROOT) else str(stl),
              "sha256": hashlib.sha256(stl.read_bytes()).hexdigest(), "command": command,
              "supports_enabled": support_enabled, "brim_width_mm": brim}
    try:
        with (out / "console.log").open("w") as log:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                       timeout=540, cwd=out)
        result["returncode"] = completed.returncode
    except subprocess.TimeoutExpired:
        result.update(returncode=None, error="Slicing timeout after 540 seconds")
    result["elapsed_seconds"] = round(time.monotonic() - started, 2)
    gcode = []
    if project.exists() and zipfile.is_zipfile(project):
        with zipfile.ZipFile(project) as archive:
            for name in archive.namelist():
                if name.lower().endswith(".gcode"):
                    with archive.open(name) as stream:
                        stats = inspect_gcode(stream)
                    stats["archive_member"] = name
                    gcode.append(stats)
    for path in out.rglob("*.gcode"):
        with path.open("rb") as stream:
            stats = inspect_gcode(stream)
        stats["file"] = path.name
        gcode.append(stats)
    result["gcode"] = gcode
    result["passed"] = result.get("returncode") == 0 and any(
        x["extrusion_moves"] > 0 and x["layer_changes"] > 0 for x in gcode)
    result["support_toolpaths_generated"] = any(x["support_extrusion_moves"] > 0 for x in gcode)
    (out / "result.json").write_text(json.dumps(result, indent=2))
    if not keep_project:
        for path in out.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".3mf", ".gcode", ".tmp"}:
                path.unlink()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stls", nargs="*", type=Path)
    parser.add_argument("--app", type=Path, default=DEFAULT_APP)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--keep-gcode", action="store_true")
    args = parser.parse_args()
    if not (args.app / "Contents/MacOS/BambuStudio").exists():
        raise SystemExit("Bambu Studio is unavailable. Supply --app /path/to/BambuStudio.app; no printer connection is needed.")
    WORK.mkdir(parents=True, exist_ok=True)
    config = profiles(args.app)
    if args.prepare_only:
        print("Resolved official profiles:", *(str(p) for p in config))
        return
    inputs = [p.resolve() for p in args.stls] or sorted((ROOT / "exports/dragon-pla-kit-v03/plates").rglob("*.stl"))
    if not inputs:
        raise SystemExit("No plate STLs found")
    results = []
    for path in inputs:
        if shutil.disk_usage(WORK).free < 200 * 1024**2:
            raise SystemExit("Less than 200 MiB free; avoid starting a slicer job until task scratch space is freed.")
        result = slice_one(args.app, path, config, args.keep_gcode)
        results.append(result)
        (WORK / "slicing-report.json").write_text(json.dumps(results, indent=2))
        print(json.dumps({"input": result["input"], "passed": result["passed"],
                          "supports": result["support_toolpaths_generated"],
                          "seconds": result["elapsed_seconds"]}), flush=True)
        if not result["passed"]:
            raise SystemExit("Slicing failed; inspect the per-plate console log and result JSON.")


if __name__ == "__main__":
    main()
