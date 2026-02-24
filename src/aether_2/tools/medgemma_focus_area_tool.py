"""
MedGemma Focus Area Tool - Assigns health focus areas to supplements.
Uses MedGemma for clinical reasoning, Gemini for JSON structuring.
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


class MedGemmaFocusAreaInput(BaseModel):
    """Input schema for MedGemma Focus Area tool."""
    supplements_with_reasoning: str = Field(
        ..., 
        description="JSON string of supplements with their clinical reasoning (ingredient_name, rank, why)"
    )
    focus_areas: str = Field(
        ..., 
        description="Patient's health focus areas with scores"
    )


class MedGemmaFocusAreaTool(BaseTool):
    """
    Query MedGemma to assign health focus areas to each supplement.
    Takes supplements with reasoning, returns focus area assignments.
    """
    
    name: str = "medgemma_focus_area"
    description: str = (
        "Assign health focus area codes to supplements using MedGemma medical AI. "
        "Provide supplements with their clinical reasoning. "
        "Returns 1-2 most relevant focus area codes for each supplement based on mechanism of action."
    )
    args_schema: Type[BaseModel] = MedGemmaFocusAreaInput
    
    def _clean_json_input(self, raw_input: str) -> str:
        """Strip markdown code fences if present, return clean JSON string."""
        cleaned = raw_input.strip()
        if cleaned.startswith("```"):
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3].rstrip()
        return cleaned

    def _build_prompt(self, supplements_with_reasoning: str, focus_areas: str) -> str:
        """Build prompt for MedGemma focus area assignment."""
        
        # Parse supplements
        try:
            clean_json = self._clean_json_input(supplements_with_reasoning)
            supplements_data = json.loads(clean_json)
            
            # Handle both formats
            if isinstance(supplements_data, dict):
                supplements_list = supplements_data.get("final_recommendations", [])
            elif isinstance(supplements_data, list):
                supplements_list = supplements_data
            else:
                supplements_list = []
        except:
            supplements_list = []
        
        # Build supplements text
        supplement_lines = []
        for i, supp in enumerate(supplements_list, 1):
            name = supp.get("ingredient_name", "Unknown")
            why = supp.get("why", "")
            supplement_lines.append(f"{i}. {name}: {why}")
        
        supplements_text = "\n".join(supplement_lines)
        
        prompt = f"""SUPPLEMENTS TO CATEGORIZE:
{supplements_text}

PATIENT FOCUS AREAS (higher score = higher priority):
{focus_areas}

FOCUS AREA CODES:
- CM: Cardiometabolic & Metabolic Health (cholesterol, blood sugar, heart, insulin)
- COG: Cognitive & Mental Health (brain function, mood, memory, focus)
- DTX: Detoxification & Biotransformation (liver function, toxin clearance)
- IMM: Immune Function & Inflammation (immune support, reducing inflammation)
- MITO: Mitochondrial & Energy Metabolism (cellular energy, fatigue, ATP)
- SKN: Skin & Barrier Function (skin health, wound healing, collagen)
- STR: Stress-Axis & Nervous System Resilience (stress response, adrenals, HPA axis)
- HRM: Hormonal Health (thyroid, sex hormones, hormone transport, SHBG)
- GA: Gut Health and Assimilation (digestion, nutrient absorption, microbiome)

TASK: For each supplement, assign 1-2 most relevant focus area codes based on:
1. The supplement's mechanism of action
2. The specific reason it was recommended for this patient

Format your response as:
1. [Supplement Name]: [CODE1], [CODE2]
2. [Supplement Name]: [CODE1]
...

Be precise. Each supplement should have 1-2 codes only."""

        return prompt
    
    def _run(self, supplements_with_reasoning: str, focus_areas: str) -> str:
        """Query MedGemma for focus area assignments."""
        try:
            if not ENDPOINT_ID:
                return "Error: MEDGEMMA_ENDPOINT_ID not set"
            
            prompt = self._build_prompt(supplements_with_reasoning, focus_areas)
            
            aiplatform.init(project=PROJECT_ID, location=REGION)
            endpoint = aiplatform.Endpoint(ENDPOINT_ID)
            
            instance = {
                "prompt": prompt,
                "max_tokens": 512,
                "temperature": 0.1,  # Low temperature for consistent categorization
                "top_p": 0.9,
                "top_k": 40
            }
            
            response = endpoint.predict(instances=[instance])
            
            if not response.predictions:
                return "Error: No response from MedGemma"
            
            result = response.predictions[0]
            if isinstance(result, dict):
                output = result.get("text", result.get("generated_text", str(result)))
            else:
                output = str(result)
            
            if "Output:" in output:
                output = output.split("Output:")[-1].strip()

            log_medgemma_call(
                tool_name="medgemma_focus_area",
                inputs={"supplements": supplements_with_reasoning[:300], "focus_areas": focus_areas[:200]},
                prompt=prompt,
                raw_response=output,
                parsed_output=output
            )

            return output

        except Exception as e:
            return f"Error querying MedGemma: {str(e)}"

