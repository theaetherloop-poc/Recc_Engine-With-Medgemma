#!/usr/bin/env python3
"""
Coverage Evaluator - Compares protocol recommendations against must-cover items.
"""

import json
import os
import glob
from must_cover_generator import MustCoverGenerator


def evaluate_coverage(user_folder: str) -> dict:
    """Evaluate how well a protocol covers must-cover items."""
    profile_path = os.path.join(user_folder, "user_profile.json")
    protocol_path = os.path.join(user_folder, "final_supplement_recommendations.json")
    
    if not os.path.exists(profile_path) or not os.path.exists(protocol_path):
        return None
    
    # Generate must-cover list
    with open(profile_path, 'r') as f:
        profile = json.load(f)
    must_cover = MustCoverGenerator(profile).extract_all()
    
    # Load protocol
    with open(protocol_path, 'r') as f:
        protocol = json.load(f)
    
    # Extract what the protocol addresses (from "why" field)
    supplements = protocol.get("supplement_recommendations", [])
    protocol_text = " ".join([s.get("why", "") for s in supplements]).lower()
    
    # Check biomarker coverage
    biomarker_covered = []
    biomarker_missed = []
    for bio in must_cover["biomarker_issues"]:
        # Extract biomarker name (before the status in parentheses)
        name = bio.split(" (")[0].lower()
        if name in protocol_text or any(name in s.get("why", "").lower() for s in supplements):
            biomarker_covered.append(bio)
        else:
            biomarker_missed.append(bio)
    
    # Check other problems coverage
    other_covered = []
    other_missed = []
    for prob in must_cover["other_problems"]:
        prob_lower = prob.lower()
        # Check if any keyword from the problem appears in protocol
        keywords = prob_lower.replace(":", " ").replace("/", " ").split()
        if any(kw in protocol_text for kw in keywords if len(kw) > 3):
            other_covered.append(prob)
        else:
            other_missed.append(prob)
    
    return {
        "user": os.path.basename(user_folder),
        "demographics": f"{must_cover['age']}yo {must_cover['sex']}",
        "total_must_cover": must_cover["total"],
        "biomarkers": {
            "total": len(must_cover["biomarker_issues"]),
            "covered": len(biomarker_covered),
            "missed": biomarker_missed
        },
        "other_problems": {
            "total": len(must_cover["other_problems"]),
            "covered": len(other_covered),
            "missed": other_missed
        },
        "supplements_count": len(supplements),
        "coverage_pct": {
            "biomarkers": round(len(biomarker_covered) / max(len(must_cover["biomarker_issues"]), 1) * 100),
            "other": round(len(other_covered) / max(len(must_cover["other_problems"]), 1) * 100),
            "overall": round((len(biomarker_covered) + len(other_covered)) / max(must_cover["total"], 1) * 100)
        }
    }


def print_evaluation(result: dict):
    """Print evaluation for one user."""
    print(f"\n{'='*60}")
    print(f"{result['user']} ({result['demographics']})")
    print(f"{'='*60}")
    print(f"Protocol: {result['supplements_count']} supplements")
    print(f"Must-Cover: {result['total_must_cover']} items")
    print(f"\nBIOMARKER COVERAGE: {result['biomarkers']['covered']}/{result['biomarkers']['total']} ({result['coverage_pct']['biomarkers']}%)")
    
    if result['biomarkers']['missed']:
        for m in result['biomarkers']['missed'][:5]:
            print(f"  ✗ {m}")
        if len(result['biomarkers']['missed']) > 5:
            print(f"  ... and {len(result['biomarkers']['missed']) - 5} more")
    
    print(f"\nOTHER PROBLEMS COVERAGE: {result['other_problems']['covered']}/{result['other_problems']['total']} ({result['coverage_pct']['other']}%)")
    if result['other_problems']['missed']:
        for m in result['other_problems']['missed'][:5]:
            print(f"  ✗ {m}")
        if len(result['other_problems']['missed']) > 5:
            print(f"  ... and {len(result['other_problems']['missed']) - 5} more")
    
    print(f"\nOVERALL: {result['coverage_pct']['overall']}%")


if __name__ == "__main__":
    outputs_dir = "outputs"
    results = []
    
    for folder in sorted(glob.glob(os.path.join(outputs_dir, "*_at_*"))):
        if os.path.isdir(folder):
            result = evaluate_coverage(folder)
            if result:
                results.append(result)
                print_evaluation(result)
    
    # Summary
    if results:
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        avg_bio = sum(r['coverage_pct']['biomarkers'] for r in results) / len(results)
        avg_other = sum(r['coverage_pct']['other'] for r in results) / len(results)
        avg_overall = sum(r['coverage_pct']['overall'] for r in results) / len(results)
        print(f"Users evaluated: {len(results)}")
        print(f"Avg Biomarker Coverage: {avg_bio:.0f}%")
        print(f"Avg Other Problems Coverage: {avg_other:.0f}%")
        print(f"Avg Overall Coverage: {avg_overall:.0f}%")

