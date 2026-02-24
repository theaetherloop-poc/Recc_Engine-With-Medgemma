#!/usr/bin/env python3
"""
Batch processing script for Aether2 pipeline.
Processes all JSON files in the inputs/ folder sequentially.

Usage:
    python run_batch.py              # Process all files
    python run_batch.py --dry-run    # List files without processing
"""

import os
import sys
import shutil
import argparse
import subprocess
from datetime import datetime


INPUT_DIR = "inputs"
WORKING_FILE = "combined_data.json"
PROCESSED_DIR = "processed"


def get_input_files():
    """Get all JSON files in inputs/ folder, excluding the working file."""
    files = []
    for f in os.listdir(INPUT_DIR):
        if f.endswith(".json") and f != WORKING_FILE:
            files.append(f)
    return sorted(files)


def run_batch(dry_run=False):
    """Run the batch processing."""
    input_files = get_input_files()
    
    if not input_files:
        print("❌ No JSON files found in inputs/ folder (excluding combined_data.json)")
        return
    
    print(f"\n{'='*60}")
    print(f"🚀 AETHER2 BATCH PROCESSING")
    print(f"{'='*60}")
    print(f"📁 Input folder: {INPUT_DIR}/")
    print(f"📄 Files found: {len(input_files)}")
    print(f"{'='*60}\n")
    
    # List all files
    for i, f in enumerate(input_files, 1):
        print(f"  {i}. {f}")
    print()
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be processed")
        print(f"{'='*60}\n")
        return
    
    # Create processed folder
    processed_path = os.path.join(INPUT_DIR, PROCESSED_DIR)
    os.makedirs(processed_path, exist_ok=True)
    
    # Track results
    results = {"success": [], "failed": []}
    start_time = datetime.now()
    
    # Process each file
    for i, filename in enumerate(input_files, 1):
        print(f"\n{'='*60}")
        print(f"📄 [{i}/{len(input_files)}] Processing: {filename}")
        print(f"{'='*60}")
        
        source_path = os.path.join(INPUT_DIR, filename)
        working_path = os.path.join(INPUT_DIR, WORKING_FILE)
        
        # Copy to working file
        shutil.copy2(source_path, working_path)
        print(f"✅ Copied to {WORKING_FILE}")
        
        # Run main.py
        try:
            result = subprocess.run(
                [sys.executable, "-m", "src.aether_2.main", working_path],
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                results["success"].append(filename)
                # Move to processed folder
                dest_path = os.path.join(processed_path, filename)
                shutil.move(source_path, dest_path)
                print(f"✅ Moved to {PROCESSED_DIR}/{filename}")
            else:
                results["failed"].append(filename)
                print(f"❌ Failed with return code: {result.returncode}")
                
        except Exception as e:
            results["failed"].append(filename)
            print(f"❌ Error: {e}")
    
    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"📊 BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Success: {len(results['success'])}")
    print(f"❌ Failed:  {len(results['failed'])}")
    print(f"⏱️  Total time: {duration:.2f} seconds")
    print(f"{'='*60}\n")
    
    if results["failed"]:
        print("Failed files:")
        for f in results["failed"]:
            print(f"  - {f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch process Aether2 pipeline")
    parser.add_argument("--dry-run", action="store_true", help="List files without processing")
    args = parser.parse_args()
    
    run_batch(dry_run=args.dry_run)

