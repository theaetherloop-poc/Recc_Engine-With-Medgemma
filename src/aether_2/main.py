import argparse
import json
import os
import sys
import csv
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.aether_2.crew import Aether2
from src.aether_2.phase3.pipeline import run_phase3_refinement
from src.aether_2.utils.logging_setup import logger, csv_log_file
from src.aether_2.utils.auth_setup import initialize_auth
from src.aether_2.utils.data_processing import (
    clean_agent_output,
    load_and_combine_inputs,
    create_excel_report
)
from src.aether_2.utils.preprocessing import (
    evaluate_biomarkers,
    compile_user_profile,
    evaluate_focus_areas,
    extract_patient_issues
)

# Initialize authentication and environment
initialize_auth()


def run(input_path="inputs/combined_data.json", run_phase3_flag: bool = False, phase3_input_path: str = None):
    """Run the crew on combined patient data (patient details + blood report).

    Args:
        input_path: Path to combined_data.json.
        run_phase3_flag: If True, run Phase 3 refinement after Phase 2.
            Requires either `phase3_input_path` or a `phase3_detailed_intake`
            field inside the input JSON.
        phase3_input_path: Optional path to a separate Phase 3 questionnaire
            JSON file shaped like ``{"questions": [{...}, ...]}``.  When
            provided, this takes precedence over any `phase3_detailed_intake`
            field embedded in `combined_data.json`.
    """
    start_time = datetime.now()
    logger.info(f"🎯 Starting Aether2 pipeline with input: {input_path}")
    
    # Load the original input data for Excel export
    with open(input_path, "r") as f:
        original_input_data = json.load(f)
    
    patient_data = load_and_combine_inputs(input_path)
    logger.info(f"📊 Loaded patient data with {len(patient_data)} main sections")

    # Extract email for output directory (sanitized for folder name)
    email = original_input_data[0]["user_full_data"]["metadata"].get("email", "unknown_user")
    user_id = email.replace("@", "_at_").replace(".", "_")
    logger.info(f"👤 Processing patient: {email}")

    print(f"\n=== Running Aether2 Pipeline ===")
    print(f"📁 Input: {input_path}")
    print(f"👤 Patient: {user_id}")

    # ========== PREPROCESSING PIPELINE (Agents 1-3) ==========
    print("\n🔧 Running preprocessing pipeline...")
    logger.info("🔧 Starting preprocessing pipeline...")

    try:
        # Step 1: Evaluate biomarkers (Agent 1)
        biomarker_results = evaluate_biomarkers(patient_data)
        logger.info("✅ Biomarker evaluation complete")

        # Step 2: Compile user profile (Agent 2)
        user_profile = compile_user_profile(patient_data, biomarker_results)
        logger.info("✅ User profile compilation complete")

        # Step 3: Evaluate focus areas (Agent 3)
        focus_areas_results = evaluate_focus_areas(patient_data)
        logger.info("✅ Focus areas evaluation complete")

        # Step 4: Extract patient issues (NEW - moved outside CrewAI)
        patient_issues = extract_patient_issues(user_profile)
        logger.info("✅ Patient issues extraction complete")

        # Step 5: Extract patient demographics for dosage context
        demographics = patient_data.get("phase1_basic_intake", {}).get("demographics", {})
        patient_demographics = f"{demographics.get('age', 'unknown')}-year-old {demographics.get('biological_sex', 'unknown')}"
        logger.info(f"✅ Patient demographics: {patient_demographics}")

        print("✅ Preprocessing complete")

    except Exception as e:
        logger.error(f"❌ Preprocessing failed: {str(e)}", exc_info=True)
        print(f"❌ Preprocessing error: {e}")

        # Log failure to CSV
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        with open(csv_log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([user_id, start_time.isoformat(), end_time.isoformat(), duration, 'failed'])

        return

    # ========== CREWAI EXECUTION (Agents 4-7) ==========
    print("\n🤖 Starting CrewAI execution...")
    logger.info("🚀 Initializing Aether2 crew...")

    try:
        # Set kickoff inputs for tools to access (class variable)
        Aether2.kickoff_inputs = {
            "user_profile": user_profile.model_dump_json(),
            "focus_areas": focus_areas_results["markdown_output"],
            "patient_issues": json.dumps(patient_issues),
            "patient_demographics": patient_demographics
        }

        # Run crew with inputs
        result = Aether2().crew().kickoff(
            inputs={
                "user_profile": user_profile.model_dump_json(),
                "focus_areas": focus_areas_results["markdown_output"],
                "patient_issues": json.dumps(patient_issues),
                "patient_demographics": patient_demographics
            }
        )
        print("✅ CrewAI execution completed successfully")
        logger.info("✅ CrewAI execution completed successfully")
    except Exception as e:
        logger.error(f" Crew execution failed: {str(e)}", exc_info=True)
        print(f"❌ Error: {e}")
        print(f"📝 Check logs/crewai_debug.log for detailed error information")
        
        # Log failure to CSV
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        with open(csv_log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([user_id, start_time.isoformat(), end_time.isoformat(), duration, 'failed'])
        
        return

    # Save results
    out_dir = os.path.join("outputs", user_id)
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n📁 Output directory: {out_dir}")

    # 1. Save preprocessing outputs (Agents 1-3)
    print("\n📄 Saving preprocessing outputs...")

    # Save biomarker evaluation (Agent 1)
    with open(os.path.join(out_dir, "biomarker_status.md"), "w") as f:
        f.write(biomarker_results["markdown_output"])
    print("  ✅ biomarker_status.md")

    # Save user profile (Agent 2)
    with open(os.path.join(out_dir, "user_profile.json"), "w") as f:
        f.write(user_profile.model_dump_json(indent=2))
    print("  ✅ user_profile.json")

    # Save focus areas (Agent 3)
    with open(os.path.join(out_dir, "focus_areas.md"), "w") as f:
        f.write(focus_areas_results["markdown_output"])
    print("  ✅ focus_areas.md")

    # 2. Save full crew run
    with open(os.path.join(out_dir, "crew_final.json"), "w") as f:
        json.dump(result.model_dump(), f, indent=2)

    # 3. Save CrewAI outputs (Agents 4-7)
    name_map = {
        "discover_ingredients_web": "discovered_ingredients_web.json",  # Agent 4: Web ingredient discovery
        "rank_ingredients_rag": "ranked_ingredients_rag.json",  # Agent 5: RAG ingredient ranker
        "generate_supplement_recommendations": "supplement_recommendations.json",  # Agent 6: Medical supplement recommendations
        "compile_final_supplement_recommendations": "final_supplement_recommendations.json",  # Agent 7: Final complete protocol
    }

    print("\n📄 Saving CrewAI outputs...")
    if hasattr(result, "tasks_output"):
        for task_output in result.tasks_output:
            filename = name_map.get(task_output.name, f"{task_output.name}.md")
            filepath = os.path.join(out_dir, filename)

            # Get the raw content
            content = ""
            if getattr(task_output, "pydantic", None):
                # Task used output_pydantic — serialize properly, not via str()
                content = task_output.pydantic.model_dump_json(indent=2)
            elif getattr(task_output, "raw", None):
                content = str(task_output.raw)
            else:
                content = "No output captured"

            # Apply post-processing for specific tasks
            if task_output.name in ["generate_supplement_recommendations", "compile_final_supplement_recommendations"]:
                content = clean_agent_output(content, task_output.name)

            # Write the cleaned content
            with open(filepath, "w") as f:
                f.write(content)

            print(f"  ✅ {filename}")
    
    # 4. Create Excel report
    print("\n📊 Creating Excel report...")
    try:
        user_email = original_input_data[0]["user_full_data"]["metadata"].get("email", "N/A")
        create_excel_report(original_input_data[0]["user_full_data"], out_dir, user_id, user_email)
        print(f"  ✅ {user_id}.xlsx")
    except Exception as e:
        print(f"  ⚠️ Warning: Could not create Excel report: {e}")

    # 5. Phase 3 refinement (optional)
    phase3_status = "skipped"
    phase3_duration = 0.0

    # Load Phase 3 questionnaire: separate file takes precedence over embedded field
    if phase3_input_path:
        try:
            with open(phase3_input_path, "r") as f:
                phase3_data = json.load(f)
            print(f"\n📋 Loaded Phase 3 questionnaire from: {phase3_input_path}")
            logger.info(f"Loaded Phase 3 data from separate file: {phase3_input_path}")
        except Exception as e:
            print(f"❌ Could not load Phase 3 input file '{phase3_input_path}': {e}")
            logger.error(f"Failed to load phase3_input_path={phase3_input_path}: {e}")
            phase3_data = None
    else:
        phase3_data = original_input_data[0]["user_full_data"].get("phase3_detailed_intake")

    if run_phase3_flag and phase3_data:
        print("\n🧪 Running Phase 3 refinement...")
        logger.info("🧪 Starting Phase 3 refinement")

        # Recover Phase 2 baseline protocol from disk (already cleaned + serialized above)
        phase2_protocol_path = os.path.join(out_dir, "final_supplement_recommendations.json")
        try:
            with open(phase2_protocol_path, "r") as f:
                phase2_protocol = json.loads(f.read())
        except Exception as e:
            logger.error(f"Could not load Phase 2 protocol from {phase2_protocol_path}: {e}")
            phase2_protocol = None

        if phase2_protocol:
            phase3_result = run_phase3_refinement(
                phase2_protocol=phase2_protocol,
                user_profile=user_profile,
                focus_areas_results=focus_areas_results,
                patient_issues=patient_issues,
                phase3_data=phase3_data,
            )
            phase3_duration = phase3_result.get("execution_time_seconds", 0.0)

            if phase3_result.get("status") == "success":
                phase3_dir = os.path.join(out_dir, "phase3")
                os.makedirs(phase3_dir, exist_ok=True)

                with open(os.path.join(phase3_dir, "refined_protocol.json"), "w") as f:
                    json.dump(phase3_result["refined_protocol"], f, indent=2)
                print(f"  ✅ phase3/refined_protocol.json")

                # Per-task audit dumps
                for task_name, output in phase3_result.get("task_outputs", {}).items():
                    with open(os.path.join(phase3_dir, f"{task_name}.json"), "w") as f:
                        json.dump(output, f, indent=2)

                phase3_status = "success"
                logger.info(f"✅ Phase 3 refinement saved to {phase3_dir}")
            else:
                phase3_status = "failed"
                logger.error(f"Phase 3 failed: {phase3_result.get('error')}")
                print(f"  ❌ Phase 3 failed: {phase3_result.get('error')}")
    elif run_phase3_flag and not phase3_data:
        print("\n⚠️  --run-phase3 set but no Phase 3 questionnaire found.")
        print("    Pass --phase3-input <path/to/phase3.json> or embed phase3_detailed_intake in the input file.")
        phase3_status = "no_questionnaire"

    # Log execution to CSV
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Write to CSV log
    with open(csv_log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            user_id, start_time.isoformat(), end_time.isoformat(), duration, 'success',
            phase3_status, f"{phase3_duration:.2f}",
        ])

    logger.info(f"📊 Execution logged to CSV: {duration:.2f} seconds")

    print(f"\n🎉 Pipeline completed successfully!")
    print(f"📁 All outputs saved to: {out_dir}")
    print(f"⏱️  Total execution time: {duration:.2f} seconds")
    print(f"📊 Preprocessing: Rule-based functions")
    print(f"🤖 Phase 2 CrewAI: AI-powered baseline recommendations")
    if phase3_status == "success":
        print(f"🧪 Phase 3 refinement: completed in {phase3_duration:.2f} seconds")
    elif phase3_status != "skipped":
        print(f"🧪 Phase 3 refinement: {phase3_status}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Aether 2 recommendation pipeline.")
    parser.add_argument(
        "input_file",
        nargs="?",
        default="inputs/combined_data.json",
        help="Path to combined_data.json (default: inputs/combined_data.json)",
    )
    parser.add_argument(
        "--run-phase3",
        action="store_true",
        help="Run Phase 3 refinement after Phase 2.",
    )
    parser.add_argument(
        "--phase3-input",
        default=None,
        metavar="FILE",
        help=(
            "Path to a separate Phase 3 questionnaire JSON file "
            "(shaped like {\"questions\": [{...}, ...]}). "
            "Takes precedence over any phase3_detailed_intake embedded in the input file."
        ),
    )
    args = parser.parse_args()

    logger.info(
        f"🎯 Processing file: {args.input_file} "
        f"(run_phase3={args.run_phase3}, phase3_input={args.phase3_input})"
    )
    run(args.input_file, run_phase3_flag=args.run_phase3, phase3_input_path=args.phase3_input)
