"""
MedGemma Ranking Tool - Ranks and prioritizes supplements based on patient profile.
"""

import json
import os
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from google.cloud import aiplatform


# Configuration from environment
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gemini-med-lit-review")
REGION = os.getenv("GCP_REGION", "us-central1")
ENDPOINT_ID = os.getenv("MEDGEMMA_ENDPOINT_ID", "")

# System prompt for ranking - strict format
RANKING_PROMPT = """Task: Rank supplements for patient. Reply ONLY with numbered list, nothing else.

Patient: {patient_context}
Supplements: {supplements}

Example format:
1. Supplement Name - 2-3 line explanation of why this ingredient is necessary for this specific patient refering to their profile
2. Supplement Name - same as above
....


Your ranked list (top 8-12 only):"""


class MedGemmaRankingInput(BaseModel):
    """Input schema for MedGemma ranking tool."""
    patient_context: str = Field(..., description="Patient's health issues: flagged biomarkers, conditions, symptoms")
    supplements: str = Field(..., description="Comma-separated list of supplements to rank")


class MedGemmaRankingTool(BaseTool):
    """Rank supplements by clinical priority for a specific patient using MedGemma."""
    
    name: str = "medgemma_rank_supplements"
    description: str = (
        "Rank supplements by clinical priority for a patient. "
        "Provide patient_context (health issues) and supplements (comma-separated list). "
        "Returns top 8-10 ranked supplements with brief reasons."
    )
    args_schema: Type[BaseModel] = MedGemmaRankingInput
    
    def _run(self, patient_context: str, supplements: str) -> str:
        """Query MedGemma to rank supplements."""
        try:
            if not ENDPOINT_ID:
                return "Error: MEDGEMMA_ENDPOINT_ID not set"
            
            # Initialize Vertex AI
            aiplatform.init(project=PROJECT_ID, location=REGION)
            
            # Get endpoint
            endpoint = aiplatform.Endpoint(ENDPOINT_ID)
            
            # Build prompt
            full_prompt = RANKING_PROMPT.format(
                patient_context=patient_context,
                supplements=supplements
            )
            
            # Query payload - limited tokens for concise output
            instance = {
                "prompt": full_prompt,
                "max_tokens": 1024,
                "temperature": 0.1,
                "top_p": 0.9,
                "top_k": 40
            }
            
            # Make prediction
            response = endpoint.predict(instances=[instance])
            
            if not response.predictions:
                return "No response"
            
            result = response.predictions[0]
            if isinstance(result, dict):
                output = result.get("text", result.get("generated_text", str(result)))
            else:
                output = str(result)
            
            # Extract just the output (after "Output:" if present)
            if "Output:" in output:
                output = output.split("Output:")[-1].strip()
            
            return output
            
        except Exception as e:
            return f"Error: {str(e)}"
