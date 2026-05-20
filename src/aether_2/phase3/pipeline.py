"""
Phase 3 refinement pipeline.

Entry point: `run_phase3_refinement(...)`. Called by `src/aether_2/pipeline.py`
after Phase 2 produces a baseline protocol — never invoked standalone.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from src.aether_2.models import UserProfile
from src.aether_2.phase3.crew import Phase3Crew
from src.aether_2.phase3.utils.phase3_extractor import (
    format_chunk_qna_for_agent,
    get_all_chunks_qna,
)
from src.aether_2.utils.data_processing import clean_agent_output


def run_phase3_refinement(
    phase2_protocol: Dict[str, Any],
    user_profile: UserProfile,
    focus_areas_results: Dict[str, Any],
    patient_issues: Dict[str, Any],
    phase3_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Refine the Phase 2 protocol using the Phase 3 questionnaire.

    Args:
        phase2_protocol: Dict with `supplement_recommendations` key — the baseline
            from Phase 2's final task. Used verbatim as the starting point.
        user_profile: Pydantic UserProfile from Phase 2 preprocessing.
        focus_areas_results: Output of `evaluate_focus_areas` — needs `scores`,
            `markdown_output`, and `reasons_data` keys.
        patient_issues: Output of `extract_patient_issues`.
        phase3_data: Dict shaped like `{"questions": [{"id", "question", "value",
            "category", "subcategory"}, ...]}`. If None, the refiners receive
            empty chunks and effectively pass the Phase 2 protocol through.

    Returns:
        {
          "status": "success" | "error",
          "refined_protocol": dict,       # FinalSupplementProtocol JSON (≤10 items)
          "task_outputs": dict[str, dict] # per-task JSON outputs, useful for audit
          "execution_time_seconds": float,
          "error": str                    # only on failure
        }
    """
    start = datetime.now()

    try:
        # ── Build chunked questionnaire ────────────────────────────────────────
        if phase3_data and phase3_data.get("questions"):
            chunks = get_all_chunks_qna(phase3_data)
            chunk_strings = {
                f"chunk{i}_qna": format_chunk_qna_for_agent(chunks.get(f"chunk{i}", {}))
                for i in range(1, 7)
            }
        else:
            chunk_strings = {
                f"chunk{i}_qna": "No Phase 3 data available." for i in range(1, 7)
            }

        # ── Assemble kickoff inputs (matches placeholders in tasks.yaml) ───────
        focus_areas_scores_json = focus_areas_results["scores"].model_dump_json()
        focus_areas_reasons_json = json.dumps(focus_areas_results.get("reasons_data", {}))
        phase2_recommendations_json = json.dumps(phase2_protocol)

        kickoff_inputs = {
            "user_profile": user_profile.model_dump_json(),
            "focus_areas": focus_areas_results["markdown_output"],
            "focus_areas_scores": focus_areas_scores_json,
            "focus_areas_reasons": focus_areas_reasons_json,
            "phase2_recommendations": phase2_recommendations_json,
            "patient_issues": json.dumps(patient_issues),
            **chunk_strings,
        }

        Phase3Crew.kickoff_inputs = kickoff_inputs

        # ── Run crew ───────────────────────────────────────────────────────────
        print("\n🧪 Starting Phase 3 refinement crew...")
        result = Phase3Crew().crew().kickoff(inputs=kickoff_inputs)
        print("✅ Phase 3 crew completed")

        # ── Extract refined protocol from optimize_final_protocol task ─────────
        refined_protocol: Optional[Dict[str, Any]] = None
        task_outputs: Dict[str, Dict[str, Any]] = {}

        if hasattr(result, "tasks_output"):
            for task_output in result.tasks_output:
                content = _extract_task_content(task_output)
                cleaned = clean_agent_output(content, task_output.name)
                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    parsed = {"raw_output": cleaned}
                task_outputs[task_output.name] = parsed

                if task_output.name == "optimize_final_protocol":
                    refined_protocol = parsed

        if refined_protocol is None:
            raise RuntimeError("Could not extract refined protocol from Phase 3 crew output")

        duration = (datetime.now() - start).total_seconds()
        print(f"✅ Phase 3 refinement complete in {duration:.2f}s")

        return {
            "status": "success",
            "refined_protocol": refined_protocol,
            "task_outputs": task_outputs,
            "execution_time_seconds": duration,
        }

    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        print(f"❌ Phase 3 refinement failed after {duration:.2f}s: {e}")
        return {
            "status": "error",
            "error": str(e),
            "execution_time_seconds": duration,
        }


def _extract_task_content(task_output: Any) -> str:
    """Pull a string payload from a CrewAI TaskOutput, preferring the richest source."""
    if getattr(task_output, "pydantic", None):
        return task_output.pydantic.model_dump_json(indent=2)
    if getattr(task_output, "tool_output", None):
        return str(task_output.tool_output)
    if getattr(task_output, "output", None):
        return str(task_output.output)
    if getattr(task_output, "raw", None):
        return str(task_output.raw)
    return ""
