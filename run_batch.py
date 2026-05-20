#!/usr/bin/env python3
"""
Batch processing script for Aether2 pipeline.
Processes JSON patient files in inputs/ sequentially, one at a time.

Usage:
    python run_batch.py                                      # All files, Phase 2 only
    python run_batch.py --dry-run                            # List files, no processing
    python run_batch.py --limit 10                           # First 10 files only
    python run_batch.py --run-phase3 --phase3-input inputs/phase3_questionnaire_sample.json
    python run_batch.py --input-dir inputs/processed         # Run from a specific folder
"""

import os
import sys
import json
import shutil
import argparse
import traceback
from datetime import datetime

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))

from src.aether_2.main import run as run_pipeline

INPUT_DIR = "inputs"
PROCESSED_DIR = "inputs/processed"

# Files that live in inputs/ but are NOT patient data files
_NON_PATIENT_FILES = {"combined_data.json", "phase3_questionnaire_sample.json"}


def get_input_files(input_dir: str, limit: int = None) -> list[str]:
    """Return sorted list of patient JSON file paths from input_dir."""
    files = []
    for f in sorted(os.listdir(input_dir)):
        if not f.endswith(".json"):
            continue
        if f in _NON_PATIENT_FILES:
            continue
        # Quick sanity check: must contain user_full_data
        path = os.path.join(input_dir, f)
        try:
            with open(path) as fh:
                data = json.load(fh)
            if not (isinstance(data, list) and data and "user_full_data" in data[0]):
                print(f"  ⚠️  Skipping {f} — not a patient file (missing user_full_data)")
                continue
        except Exception:
            print(f"  ⚠️  Skipping {f} — could not parse as JSON")
            continue
        files.append(path)

    if limit:
        files = files[:limit]
    return files


def run_batch(
    input_dir: str = INPUT_DIR,
    dry_run: bool = False,
    limit: int = None,
    run_phase3: bool = False,
    phase3_input: str = None,
    no_move: bool = False,
):
    input_files = get_input_files(input_dir, limit=limit)

    print(f"\n{'='*60}")
    print(f"AETHER2 BATCH PROCESSING")
    print(f"{'='*60}")
    print(f"  Input folder : {input_dir}/")
    print(f"  Files queued : {len(input_files)}")
    print(f"  Phase 3      : {'yes — ' + phase3_input if run_phase3 and phase3_input else 'yes (embedded)' if run_phase3 else 'no'}")
    print(f"{'='*60}\n")

    if not input_files:
        print("No patient JSON files found. Drop files into inputs/ and retry.")
        return

    for i, path in enumerate(input_files, 1):
        print(f"  {i:>2}. {os.path.basename(path)}")
    print()

    if dry_run:
        print("DRY RUN — no files processed.")
        return

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    results = {"success": [], "failed": [], "errors": {}}
    batch_start = datetime.now()

    for i, input_path in enumerate(input_files, 1):
        filename = os.path.basename(input_path)
        print(f"\n{'='*60}")
        print(f"[{i}/{len(input_files)}] {filename}")
        print(f"{'='*60}")

        # Resolve Phase 3 questionnaire for this file:
        # 1. Per-patient side-car file:  patient.json → patient_phase3.json  (highest priority)
        # 2. Shared --phase3-input flag (same file for every patient)
        # 3. Embedded phase3_detailed_intake inside the patient JSON (fallback)
        resolved_phase3_input = phase3_input  # default: shared file or None
        if run_phase3:
            base, ext = os.path.splitext(input_path)
            sidecar = f"{base}_phase3{ext}"
            if os.path.exists(sidecar):
                resolved_phase3_input = sidecar
                print(f"  Phase 3 questionnaire: {os.path.basename(sidecar)}")
            elif phase3_input:
                print(f"  Phase 3 questionnaire: {os.path.basename(phase3_input)} (shared)")
            else:
                print(f"  Phase 3 questionnaire: embedded in patient file (or none)")

        file_start = datetime.now()
        try:
            run_pipeline(
                input_path=input_path,
                run_phase3_flag=run_phase3,
                phase3_input_path=resolved_phase3_input,
            )
            duration = (datetime.now() - file_start).total_seconds()
            results["success"].append(filename)
            print(f"  Done in {duration:.0f}s")

            if not no_move:
                dest = os.path.join(PROCESSED_DIR, filename)
                shutil.move(input_path, dest)
                print(f"  Moved to processed/")

        except Exception as e:
            duration = (datetime.now() - file_start).total_seconds()
            results["failed"].append(filename)
            results["errors"][filename] = str(e)
            print(f"  FAILED after {duration:.0f}s: {e}")
            traceback.print_exc()
            print("  Continuing to next file...")

    total = (datetime.now() - batch_start).total_seconds()

    print(f"\n{'='*60}")
    print(f"BATCH SUMMARY")
    print(f"{'='*60}")
    print(f"  Success : {len(results['success'])}/{len(input_files)}")
    print(f"  Failed  : {len(results['failed'])}/{len(input_files)}")
    print(f"  Total   : {total:.0f}s  ({total/60:.1f} min)")
    print(f"{'='*60}\n")

    if results["failed"]:
        print("Failed files:")
        for f in results["failed"]:
            print(f"  - {f}: {results['errors'].get(f, '')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch process Aether2 pipeline over multiple patient files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input-dir",
        default=INPUT_DIR,
        metavar="DIR",
        help=f"Folder to scan for patient JSON files (default: {INPUT_DIR})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process only the first N files (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without processing",
    )
    parser.add_argument(
        "--run-phase3",
        action="store_true",
        help="Run Phase 3 refinement after Phase 2 for every file",
    )
    parser.add_argument(
        "--phase3-input",
        default=None,
        metavar="FILE",
        help=(
            "Fallback Phase 3 questionnaire JSON applied when no per-patient "
            "side-car file (<patient>_phase3.json) is found. "
            "Priority: side-car > this flag > embedded phase3_detailed_intake."
        ),
    )
    parser.add_argument(
        "--no-move",
        action="store_true",
        help="Keep input files in place after processing (don't move to processed/)",
    )
    args = parser.parse_args()

    run_batch(
        input_dir=args.input_dir,
        dry_run=args.dry_run,
        limit=args.limit,
        run_phase3=args.run_phase3,
        phase3_input=args.phase3_input,
        no_move=args.no_move,
    )
