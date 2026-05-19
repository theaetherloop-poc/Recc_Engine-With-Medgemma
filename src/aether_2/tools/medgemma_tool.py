"""
MedGemma Tool - Concise supplement query tool for CrewAI agents.
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

# System prompt to constrain output - ONLY 2-3 supplements per query
SYSTEM_PROMPT = """You are a medical supplement advisor. Return ONLY 2-3 top supplements as a comma-separated list.
No explanations, no dosages, no disclaimers. Just 2-3 supplement names.

Example query: "low vitamin D"
Example response: Vitamin D3, Vitamin K2

Example query: "hypothyroidism"
Example response: Selenium, Iodine, Ashwagandha

Example query: "high iron and ferritin"
Example response: Milk Thistle, IP6

Query:
"""


class MedGemmaInput(BaseModel):
    """Input schema for MedGemma tool."""
    query: str = Field(..., description="Health issue to get supplements for (e.g., 'low vitamin D', 'hypothyroidism', 'chronic fatigue')")


class MedGemmaTool(BaseTool):
    """Query MedGemma for supplement recommendations. Returns only supplement names."""
    
    name: str = "medgemma_query"
    description: str = (
        "Get supplement recommendations from MedGemma medical AI. "
        "Pass a health issue (e.g., 'low iron', 'anxiety', 'high cholesterol') "
        "and receive a list of recommended supplement names."
    )
    args_schema: Type[BaseModel] = MedGemmaInput
    
    def _run(self, query: str) -> str:
        """Query MedGemma with constrained prompt for concise output."""
        try:
            if not ENDPOINT_ID:
                return "Error: MEDGEMMA_ENDPOINT_ID not set"
            
            # Initialize Vertex AI
            aiplatform.init(project=PROJECT_ID, location=REGION)
            
            # Get endpoint
            endpoint = aiplatform.Endpoint(ENDPOINT_ID)
            
            # Wrap query with system prompt for concise output
            full_prompt = f"{SYSTEM_PROMPT}{query}"
            
            # Query payload - minimal tokens for 2-3 supplements only
            instance = {
                "prompt": full_prompt,
                "max_tokens": 50,  # Only need ~2-3 supplement names
                "temperature": 0,
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
