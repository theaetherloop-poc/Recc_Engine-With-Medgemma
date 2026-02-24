"""
MedGemma Logger - Centralized logging for all MedGemma tool calls.
Logs to outputs/<user_id>/ folder with separate files per tool.
"""

import os
from datetime import datetime

OUTPUTS_DIR = "outputs"

def _get_user_id():
    """Get user_id from Aether2 kickoff_inputs."""
    try:
        from src.aether_2.crew import Aether2
        return Aether2.kickoff_inputs.get("user_id", "unknown_user")
    except Exception:
        return "unknown_user"

def _ensure_user_dir(user_id: str) -> str:
    """Ensure user-specific outputs directory exists."""
    user_dir = os.path.join(OUTPUTS_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def log_medgemma_call(tool_name: str, inputs: dict, prompt: str, raw_response: str, parsed_output: str):
    """
    Log a MedGemma tool call to user-specific folder.

    Args:
        tool_name: Name of the tool (medgemma_query, medgemma_recommender, medgemma_dosage)
        inputs: Dictionary of input parameters
        prompt: Full prompt sent to MedGemma
        raw_response: Raw response from MedGemma
        parsed_output: Cleaned/parsed output returned to agent
    """
    try:
        user_id = _get_user_id()
        user_dir = _ensure_user_dir(user_id)

        # Map tool name to log file
        log_files = {
            "medgemma_query": "medgemma_tool_calls.log",
            "medgemma_recommender": "medgemma_recommender_calls.log",
            "medgemma_dosage": "medgemma_dosage_calls.log"
        }

        log_file = log_files.get(tool_name, "medgemma_calls.log")
        log_path = os.path.join(user_dir, log_file)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Format inputs
        inputs_str = "\n".join(f"  {k}: {v}" for k, v in inputs.items())

        # Build log entry (no truncation for full observability)
        log_entry = f"""
{'='*80}
[{timestamp}] MEDGEMMA TOOL CALL: {tool_name}
{'='*80}
INPUT:
{inputs_str}

PROMPT SENT:
{prompt}

RAW RESPONSE:
{raw_response}

PARSED OUTPUT:
{parsed_output}
{'='*80}

"""

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)

    except Exception:
        # Silent fail - logging should never break the pipeline
        pass

