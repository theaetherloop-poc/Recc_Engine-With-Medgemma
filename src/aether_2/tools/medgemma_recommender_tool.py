"""
MedGemma Recommender Tool - Clinical reasoning for supplement recommendations.
Uses MedGemma for clinical analysis, returns unstructured recommendations.
"""

import json
import os
from typing import Type, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from google.cloud import aiplatform
from src.aether_2.tools.medgemma_logger import log_medgemma_call


# Configuration from environment
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gemini-med-lit-review")
REGION = os.getenv("GCP_REGION", "us-central1")
ENDPOINT_ID = os.getenv("MEDGEMMA_ENDPOINT_ID", "")


class MedGemmaRecommenderInput(BaseModel):
    """Input schema for MedGemma Recommender tool."""
    patient_summary: str = Field(..., description="Natural language User summary with demographics, biomarkers, symptoms")
    candidate_ingredients: str = Field(..., description="JSON string of discovered ingredients with reasons from MedGemma discovery phase")


class MedGemmaRecommenderTool(BaseTool):
    """
    Query MedGemma for clinical reasoning on supplement recommendations.
    Takes User summary + candidate ingredients, returns prioritized recommendations with clinical reasoning.
    """
    
    name: str = "medgemma_recommender"
    description: str = (
        "Get clinical reasoning and supplement recommendations from MedGemma medical AI. "
        "Provide user summary and candidate ingredients. "
        "Returns prioritized supplement recommendations with user-specific clinical reasoning."
        "The supplements should not overlap with other supplements which cover the same health issues."
        "But take into account the user's current supplements and they can be included relevant with the current issues"
        "Also consider if a pair of supplement complement each other and can be recommended together.Use you own clinical Judgement"
    )
    args_schema: Type[BaseModel] = MedGemmaRecommenderInput
    
    def _clean_json_input(self, raw_input: str) -> str:
        """Strip markdown code fences if present, return clean JSON string."""
        cleaned = raw_input.strip()
        # Remove markdown code fences (```json ... ``` or ``` ... ```)
        if cleaned.startswith("```"):
            # Find end of first line (```json or ```)
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            # Remove closing ```
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3].rstrip()
        return cleaned

    def _build_prompt(self, patient_summary: str, candidate_ingredients: str) -> str:
        """Build concise, optimized prompt for MedGemma clinical reasoning."""

        # Parse candidate ingredients
        try:
            # Clean markdown formatting if present
            clean_json = self._clean_json_input(candidate_ingredients)
            ingredients_data = json.loads(clean_json)

            # Handle both formats:
            # 1. {"discovered_ingredients": [...]} - wrapper format from task output
            # 2. [...] - raw array format (when Gemini extracts just the array)
            if isinstance(ingredients_data, dict):
                ingredients_list = ingredients_data.get("discovered_ingredients", [])
            elif isinstance(ingredients_data, list):
                ingredients_list = ingredients_data
            else:
                ingredients_list = []
        except:
            # Fallback if parsing fails
            ingredients_list = []
        
        # Use full patient summary for complete context
        patient_context = patient_summary

        # Build ingredient list (no cap - pass all discovered ingredients with all reasons)
        ingredient_lines = []
        for i, ing in enumerate(ingredients_list, 1):
            name = ing.get("ingredient_name", "Unknown")
            reasons = ing.get("reasons", [])
            reason_str = ", ".join(reasons) if reasons else "general health"
            ingredient_lines.append(f"{i}. {name} - {reason_str}")
        
        ingredients_text = "\n".join(ingredient_lines)
        
        # Build concise prompt with example format
        prompt = f"""User Summary:
{patient_context}

CANDIDATE SUPPLEMENTS (from medical literature):
{ingredients_text}

TASK: Select 8-12 most important supplements from the candidate list above. Rank by clinical priority for THIS user.

RULE: Do NOT select supplements that cover the exact same problems unless they complement each other with positive interactions (e.g., Vitamin D + K2). Maximize coverage across different health issues.

FORMAT (follow exactly):
1. [Supplement Name]
   Why: [2-3 lines explaining why this matters for THIS user's specific biomarkers/symptoms]

EXAMPLE (structure only - do not copy content):
1. Vitamin D3
   Why: You reported low 25-(OH) Vitamin D at 25.8 ng/mL. Given your limited sun exposure and family history of osteoporosis, supplementing D3 supports bone health and immune function.

2. Omega-3
   Why: Your HDL is low at 34 mg/dL and triglyceride ratio is elevated. Omega-3 fatty acids help improve lipid profile and reduce cardiovascular risk markers.

NOW LIST YOUR 8-12 RECOMMENDATIONS FOR THIS USER:
1."""

        return prompt
    
    def _run(self, patient_summary: str, candidate_ingredients: str) -> str:
        """Query MedGemma for clinical reasoning on supplement recommendations."""
        try:
            if not ENDPOINT_ID:
                return "Error: MEDGEMMA_ENDPOINT_ID not set"
            
            # Build optimized prompt
            prompt = self._build_prompt(patient_summary, candidate_ingredients)
            
            # Initialize Vertex AI
            aiplatform.init(project=PROJECT_ID, location=REGION)
            
            # Get endpoint
            endpoint = aiplatform.Endpoint(ENDPOINT_ID)
            
            # Query payload - longer output for clinical reasoning
            instance = {
                "prompt": prompt,
                "max_tokens": 2048,  # Need space for 8-12 recommendations with reasoning
                "temperature": 0.1,  # Balanced creativity/consistency
                "top_p": 0.9,
                "top_k": 40,
                "stop": ["15.", "Constraints:", "Note:", "**", "---", "DISCLAIMER"]  # Stop after 12 items or if model starts meta-commentary
            }
            
            # Make prediction
            response = endpoint.predict(instances=[instance])
            
            if not response.predictions:
                return "Error: No response from MedGemma"
            
            result = response.predictions[0]
            if isinstance(result, dict):
                output = result.get("text", result.get("generated_text", str(result)))
            else:
                output = str(result)
            
            # Extract output (after "Output:" if present)
            if "Output:" in output:
                output = output.split("Output:")[-1].strip()

            # Prepend "1." since prompt ends with "1." and model continues from there
            if output and not output.strip().startswith("1."):
                output = "1." + output

            # Log the call
            log_medgemma_call(
                tool_name="medgemma_recommender",
                inputs={"patient_summary": patient_summary[:200], "candidate_ingredients": candidate_ingredients[:200]},
                prompt=prompt,
                raw_response=output,
                parsed_output=output
            )

            # Return MedGemma's clinical reasoning (unstructured)
            return output

        except Exception as e:
            return f"Error querying MedGemma: {str(e)}"

