"""
Compile MedGemma questions from log files for evaluation.
Extracts queries from medgemma_tool_calls.log and medgemma_dosage_calls.log
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Profile directories
PROFILES = [
    "outputs/tusharmhatre2424_at_gmail_com",
    "outputs/geetahj_at_gmail_com"
]

LOG_FILES = [
    "medgemma_tool_calls.log",
    "medgemma_dosage_calls.log"
]

def parse_log_file(log_path, profile_name):
    """Parse a MedGemma log file and extract all queries."""

    if not os.path.exists(log_path):
        print(f"  ⚠️  Log file not found: {log_path}")
        return []

    with open(log_path, 'r') as f:
        content = f.read()

    # Find all entries using regex pattern that captures the full block
    # Pattern: header line with timestamp and tool name, followed by content until next header or end
    pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] MEDGEMMA TOOL CALL: (\w+)\s*\n={80}\nINPUT:\n(.*?)(?=\n={80}\n\[|\Z)'

    matches = re.findall(pattern, content, re.DOTALL)

    questions = []

    for match in matches:
        timestamp = match[0]
        tool_name = match[1]
        entry_content = match[2]

        # Extract query from INPUT section
        input_fields = {}
        input_match = re.search(r'^(.*?)\n\nPROMPT SENT:', entry_content, re.DOTALL)
        if input_match:
            input_text = input_match.group(1).strip()
            for line in input_text.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    input_fields[key.strip()] = value.strip()

        # Extract RAW RESPONSE
        raw_response_match = re.search(r'RAW RESPONSE:\n(.*?)\n\nPARSED OUTPUT:', entry_content, re.DOTALL)
        raw_response = raw_response_match.group(1).strip() if raw_response_match else ""

        # Extract PARSED OUTPUT
        parsed_output_match = re.search(r'PARSED OUTPUT:\n(.*?)$', entry_content, re.DOTALL)
        parsed_output = parsed_output_match.group(1).strip() if parsed_output_match else ""

        # Create question entry
        question = {
            "profile": profile_name,
            "timestamp": timestamp,
            "tool": tool_name,
            "input_fields": input_fields,
            "raw_response": raw_response,
            "parsed_output": parsed_output
        }

        questions.append(question)

    return questions

def categorize_query(query_text):
    """Categorize query type based on content."""
    query_lower = query_text.lower()
    
    # Biomarker patterns
    biomarker_patterns = [
        r'low \w+', r'high \w+', r'elevated \w+', 
        r'\w+ deficiency', r'\w+ level'
    ]
    
    # Symptom patterns
    symptom_patterns = [
        'fatigue', 'stress', 'anxiety', 'sleep', 'pain',
        'digestive', 'bloating', 'constipation', 'insomnia'
    ]
    
    # Condition patterns
    condition_patterns = [
        'hypothyroidism', 'hyperthyroidism', 'diabetes',
        'hypertension', 'cholesterol', 'menopause'
    ]
    
    if any(re.search(pattern, query_lower) for pattern in biomarker_patterns):
        return "biomarker_specific"
    elif any(symptom in query_lower for symptom in symptom_patterns):
        return "symptom_specific"
    elif any(condition in query_lower for condition in condition_patterns):
        return "condition_specific"
    elif "dosage" in query_lower or "supplement_name" in query_lower:
        return "dosage_query"
    else:
        return "general"

def format_question_for_evaluation(question):
    """Format question for evaluation benchmark."""
    
    tool = question["tool"]
    
    if tool == "medgemma_query":
        # Ingredient discovery question
        query = question["input_fields"].get("query", "")
        
        return {
            "query_type": "ingredient_discovery",
            "question": f"What supplements are recommended for: {query}?",
            "query_text": query,
            "expected_format": "2-3 supplement names, comma-separated",
            "medgemma_answer": question["parsed_output"],
            "category": categorize_query(query)
        }
    
    elif tool == "medgemma_dosage":
        # Dosage recommendation question
        supplement = question["input_fields"].get("supplement_name", "")
        context = question["input_fields"].get("patient_context", "")
        
        return {
            "query_type": "dosage_recommendation",
            "question": f"What is the recommended dosage for {supplement} in a patient with {context}?",
            "supplement_name": supplement,
            "patient_context": context,
            "expected_format": "Dosage: [amount] | Frequency: [timing]",
            "medgemma_answer": question["parsed_output"],
            "category": "dosage_query"
        }
    
    else:
        return None

def deduplicate_questions(questions):
    """Remove duplicate questions, keep unique query variations."""
    
    seen = {}
    unique_questions = []
    
    for q in questions:
        # Create key based on query content
        if q["query_type"] == "ingredient_discovery":
            key = q["query_text"].lower().strip()
        else:
            key = f"{q['supplement_name']}_{q['patient_context']}".lower().strip()
        
        if key not in seen:
            seen[key] = True
            unique_questions.append(q)
    
    return unique_questions

def compile_all_questions():
    """Main compilation function."""
    
    all_questions = []
    stats = defaultdict(int)
    
    print("=" * 80)
    print("COMPILING MEDGEMMA QUESTIONS FROM LOGS")
    print("=" * 80)
    print()
    
    for profile_dir in PROFILES:
        profile_name = Path(profile_dir).name.replace("_at_", "@").replace("_com", ".com")
        
        print(f"📂 Processing: {profile_name}")
        print("-" * 80)
        
        for log_file in LOG_FILES:
            log_path = os.path.join(profile_dir, log_file)
            
            print(f"  📄 Reading: {log_file}")
            
            # Parse log file
            raw_questions = parse_log_file(log_path, profile_name)
            
            print(f"     Found {len(raw_questions)} log entries")
            
            # Format for evaluation
            for raw_q in raw_questions:
                formatted = format_question_for_evaluation(raw_q)
                if formatted:
                    formatted["profile"] = profile_name
                    formatted["source_log"] = log_file
                    all_questions.append(formatted)
                    stats[formatted["category"]] += 1
        
        print()
    
    # Deduplicate
    print(f"📊 Total questions before deduplication: {len(all_questions)}")
    unique_questions = deduplicate_questions(all_questions)
    print(f"📊 Unique questions after deduplication: {len(unique_questions)}")
    print()
    
    # Add IDs
    for i, q in enumerate(unique_questions, 1):
        q["id"] = f"q{i:03d}"
        q["ground_truth"] = None
        q["gemini_answer"] = None
        q["notes"] = ""
    
    # Create output structure
    output = {
        "metadata": {
            "compiled_date": datetime.now().isoformat(),
            "source_profiles": [p.replace("outputs/", "").replace("_at_", "@").replace("_com", ".com") for p in PROFILES],
            "total_questions": len(unique_questions),
            "categories": dict(stats)
        },
        "questions": unique_questions
    }
    
    # Save to JSON
    output_path = "evaluation/compiled_medgemma_questions.json"
    os.makedirs("evaluation", exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("=" * 80)
    print(f"✅ COMPILATION COMPLETE")
    print("=" * 80)
    print(f"📁 Output file: {output_path}")
    print(f"📊 Total unique questions: {len(unique_questions)}")
    print()
    print("Questions by Category:")
    for category, count in sorted(stats.items()):
        print(f"  • {category}: {count}")
    print()
    
    # Print sample questions
    print("Sample Questions:")
    print("-" * 80)
    for q in unique_questions[:5]:
        print(f"\n[{q['id']}] {q['category']}")
        print(f"Q: {q['question']}")
        print(f"MedGemma: {q['medgemma_answer']}")
    
    return output

if __name__ == "__main__":
    compile_all_questions()