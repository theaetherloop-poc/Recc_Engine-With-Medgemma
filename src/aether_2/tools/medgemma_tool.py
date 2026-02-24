"""
MedGemma Tool - Concise supplement query tool for CrewAI agents.
"""

import re
import os
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from google.cloud import aiplatform
from src.aether_2.tools.medgemma_logger import log_medgemma_call


# Configuration from environment
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gemini-med-lit-review")
REGION = os.getenv("GCP_REGION", "us-central1")
ENDPOINT_ID = os.getenv("MEDGEMMA_ENDPOINT_ID", "")

# Strict system prompt - ONLY supplement names, nothing else
SYSTEM_PROMPT = """Return ONLY 2-3 supplement names. No explanations. No dosages. No disclaimers.

Query: low vitamin D
Response: Vitamin D3, Vitamin K2

Query: hypothyroidism
Response: Selenium, Iodine

Query: high stress and anxiety
Response: Ashwagandha, L-Theanine, Magnesium

Query: """


class MedGemmaInput(BaseModel):
    """Input schema for MedGemma tool."""
    query: str = Field(..., description="Health issue to get supplements for (e.g., 'low vitamin D', 'hypothyroidism', 'chronic fatigue')")


class MedGemmaTool(BaseTool):
    """Query MedGemma for supplement recommendations. Returns only supplement names."""
    
    name: str = "medgemma_query"
    description: str = (
        "Get supplement recommendations from MedGemma medical AI. "
        "Pass a health issue (e.g., 'low iron', 'anxiety', 'high cholesterol') "
        "and receive 2-3 supplement names only."
    )
    args_schema: Type[BaseModel] = MedGemmaInput

    def _extract_supplement_names(self, raw_output: str) -> str:
        """Extract only supplement names from MedGemma output, limit to 3."""
        if not raw_output or raw_output.startswith("Error"):
            return raw_output

        # Remove common noise patterns
        noise_patterns = [
            r'\([^)]*\)',  # Remove parentheses content (dosages)
            r'\d+\s*(mg|mcg|IU|g|ml)',  # Remove dosage numbers
            r'daily|twice|once|with meals|before bed',  # Remove frequency
            r'Note:.*',  # Remove notes
            r'Important:.*',  # Remove disclaimers
            r'\*+.*',  # Remove asterisk notes
        ]

        cleaned = raw_output
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Split by common delimiters and extract supplement names
        # Handle numbered lists, bullet points, commas, newlines
        cleaned = re.sub(r'^\d+[\.\)]\s*', '', cleaned, flags=re.MULTILINE)  # Remove numbering
        cleaned = re.sub(r'^[-•]\s*', '', cleaned, flags=re.MULTILINE)  # Remove bullets

        # Split by comma, newline, or "and"
        parts = re.split(r'[,\n]|\band\b', cleaned)

        # Clean each part and filter valid supplement names
        supplements = []
        for part in parts:
            name = part.strip().strip('.-•*')
            # Valid supplement name: 2-40 chars, starts with letter
            if name and 2 <= len(name) <= 40 and name[0].isalpha():
                # Skip if it looks like a sentence (has too many words)
                if len(name.split()) <= 4:
                    supplements.append(name)

        # Limit to 3 supplements
        supplements = supplements[:3]

        if supplements:
            return ", ".join(supplements)

        # Fallback: return first 50 chars of raw output if parsing failed
        return raw_output[:50].strip() if raw_output else "No supplements found"

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
                "max_tokens": 30,  # Reduced: only need 2-3 supplement names
                "temperature": 0,
                "top_p": 0.9,
                "top_k": 40,
                "stop": ["\nQuery:", "Query:", "\n\n"]  # Stop before generating next query
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

            # Extract just the output (after "Output:" or "Response:" if present)
            for marker in ["Output:", "Response:"]:
                if marker in output:
                    output = output.split(marker)[-1].strip()
                    break

            # Strip out any "Query:" text that leaked through (causes infinite loops)
            if "Query:" in output:
                output = output.split("Query:")[0].strip()

            # Parse and clean the output to extract only supplement names
            parsed_output = self._extract_supplement_names(output)

            # Log the call
            log_medgemma_call(
                tool_name="medgemma_query",
                inputs={"query": query},
                prompt=full_prompt,
                raw_response=output,
                parsed_output=parsed_output
            )

            return parsed_output

        except Exception as e:
            return f"Error: {str(e)}"
