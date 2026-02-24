"""
MedGemma Dosage Tool - Query MedGemma for supplement dosage and frequency recommendations.
"""

import os
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from google.cloud import aiplatform
from src.aether_2.tools.medgemma_logger import log_medgemma_call


PROJECT_ID = os.getenv("GCP_PROJECT_ID", "gemini-med-lit-review")
REGION = os.getenv("GCP_REGION", "us-central1")
ENDPOINT_ID = os.getenv("MEDGEMMA_ENDPOINT_ID", "")

DOSAGE_SYSTEM_PROMPT = """You are a clinical pharmacist. Provide ONLY the recommended dosage and frequency for the supplement.

Format: [dosage] [frequency]

Examples:
Query: Vitamin D3 dosage for adult with level 21 ng/mL
Response: 2000-4000 IU once daily with fatty meal

Query: Magnesium Glycinate for sleep and stress
Response: 200-400 mg once daily before bedtime

Query: Omega-3 Fish Oil for cardiovascular health
Response: 1000-2000 mg twice daily with meals

Query: """


class MedGemmaDosageInput(BaseModel):
    """Input schema for MedGemma Dosage tool."""
    supplement_name: str = Field(..., description="Name of the supplement (e.g., 'Vitamin D3', 'Magnesium Glycinate')")
    patient_context: str = Field(..., description="Brief patient context (e.g., 'adult female with low vitamin D level 21 ng/mL')")


class MedGemmaDosageTool(BaseTool):
    """Query MedGemma for evidence-based dosage and frequency recommendations."""
    
    name: str = "medgemma_dosage"
    description: str = (
        "Get evidence-based dosage and frequency for a supplement from MedGemma medical AI. "
        "Provide supplement_name and patient_context. "
        "Returns recommended dosage with units and optimal frequency/timing."
    )
    args_schema: Type[BaseModel] = MedGemmaDosageInput

    def _parse_dosage_response(self, raw_output: str) -> dict:
        """Parse MedGemma response into dosage and frequency components."""
        if not raw_output or raw_output.startswith("Error"):
            return {"dosage": "Standard dose", "frequency": "Once daily"}

        output = raw_output.strip()

        # Truncate at markers that indicate MedGemma is generating extra content
        for marker in ["\n\n", "\nQuery:", "Query:"]:
            if marker in output:
                output = output.split(marker)[0].strip()

        # Remove common prefixes
        for prefix in ["Response:", "Answer:", "Recommended:"]:
            if output.startswith(prefix):
                output = output[len(prefix):].strip()

        # Try to split into dosage and frequency
        # Common patterns: "X mg once daily", "X IU twice daily with meals"
        frequency_keywords = ["once", "twice", "daily", "weekly", "morning", "evening",
                            "bedtime", "with meals", "empty stomach", "before", "after"]

        dosage = output
        frequency = ""

        # Find where frequency starts
        output_lower = output.lower()
        for keyword in frequency_keywords:
            idx = output_lower.find(keyword)
            if idx > 0:
                dosage = output[:idx].strip()
                frequency = output[idx:].strip()
                break

        # Clean up
        dosage = dosage.strip(" -,")
        frequency = frequency.strip(" -,") if frequency else "once daily"

        if not dosage:
            dosage = "Standard dose"

        return {"dosage": dosage, "frequency": frequency}

    def _clean_patient_context(self, patient_context: str) -> str:
        """Clean conversational phrases from patient context for better queries."""
        cleaned = patient_context
        # Remove conversational prefixes
        prefixes_to_remove = [
            "You reported ",
            "You have ",
            "Patient reported ",
            "Patient has ",
            "The patient reported ",
            "The patient has ",
        ]
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
            cleaned = cleaned.replace(prefix.lower(), "")
            cleaned = cleaned.replace(prefix, "")

        # Clean up any leading/trailing whitespace and punctuation
        cleaned = cleaned.strip(" .,")
        return cleaned

    def _run(self, supplement_name: str, patient_context: str) -> str:
        """Query MedGemma for dosage and frequency recommendation."""
        try:
            if not ENDPOINT_ID:
                return "Error: MEDGEMMA_ENDPOINT_ID not set"

            aiplatform.init(project=PROJECT_ID, location=REGION)
            endpoint = aiplatform.Endpoint(ENDPOINT_ID)

            # Clean patient context for better query construction
            clean_context = self._clean_patient_context(patient_context)
            query = f"{supplement_name} dosage for {clean_context}"
            full_prompt = f"{DOSAGE_SYSTEM_PROMPT}{query}"

            instance = {
                "prompt": full_prompt,
                "max_tokens": 50,
                "temperature": 0,
                "top_p": 0.9,
                "top_k": 40,
                "stop": ["\nQuery:", "Query:", "\n\n"]  # Stop before generating next query
            }

            response = endpoint.predict(instances=[instance])

            if not response.predictions:
                return f"Dosage: Standard dose | Frequency: Once daily"

            result = response.predictions[0]
            if isinstance(result, dict):
                output = result.get("text", result.get("generated_text", str(result)))
            else:
                output = str(result)

            # Extract output after markers
            for marker in ["Output:", "Response:"]:
                if marker in output:
                    output = output.split(marker)[-1].strip()
                    break

            parsed = self._parse_dosage_response(output)
            parsed_output = f"Dosage: {parsed['dosage']} | Frequency: {parsed['frequency']}"

            # Log the call
            log_medgemma_call(
                tool_name="medgemma_dosage",
                inputs={"supplement_name": supplement_name, "patient_context": patient_context},
                prompt=full_prompt,
                raw_response=output,
                parsed_output=parsed_output
            )

            return parsed_output

        except Exception as e:
            return f"Error: {str(e)}"

