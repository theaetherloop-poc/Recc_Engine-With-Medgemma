"""
Phase 3 QNA Extractor
Extracts question-answer pairs from Phase 3 data and organizes them into chunks.
"""

import json
from typing import Dict, List, Tuple


def extract_qna_pairs(phase3_data: Dict) -> Dict[str, Dict[str, str]]:
    """
    Extract question-answer pairs from Phase 3 data.
    
    Args:
        phase3_data: Phase 3 JSON data with 'questions' array
        
    Returns:
        Dict mapping question_id to {'question': str, 'answer': str}
        Example: {'q001': {'question': '...', 'answer': '...'}, ...}
    """
    qna_pairs = {}
    
    if not phase3_data or 'questions' not in phase3_data:
        return qna_pairs
    
    for item in phase3_data['questions']:
        question_id = item.get('id', '')  # Field is 'id' not 'question_id'
        question_text = item.get('question', '')
        answer_value = item.get('value', '')
        category = item.get('category', '')
        subcategory = item.get('subcategory', '')

        if question_id:
            qna_pairs[question_id] = {
                'question': question_text,
                'answer': str(answer_value),  # Convert to string for consistency
                'category': category,
                'subcategory': subcategory
            }
    
    return qna_pairs


def get_chunk_ranges() -> List[Tuple[str, str, str]]:
    """
    Define the 6 chunks of Phase 3 questions.
    
    Returns:
        List of tuples: (chunk_name, start_qid, end_qid)
    """
    return [
        ("chunk1", "q001", "q014"),  # Goals & Narrative
        ("chunk2", "q015", "q028"),  # Meds, Lifestyle, Sleep
        ("chunk3", "q029", "q045"),  # Nutrition, Stress & Support
        ("chunk4", "q046", "q063"),  # Childhood, Dental, Environment
        ("chunk5", "q064", "q075"),  # Pets, Systems Check
        ("chunk6", "q076", "q093"),  # Hormones, Pain, Headache, Skin
    ]


def extract_chunk_qna(qna_pairs: Dict[str, Dict[str, str]], start_qid: str, end_qid: str) -> Dict[str, Dict[str, str]]:
    """
    Extract QNA pairs for a specific chunk range.
    
    Args:
        qna_pairs: All QNA pairs from extract_qna_pairs()
        start_qid: Starting question ID (e.g., 'q001')
        end_qid: Ending question ID (e.g., 'q014')
        
    Returns:
        Dict of QNA pairs within the range
    """
    # Extract numeric parts for range comparison
    start_num = int(start_qid[1:])  # 'q001' -> 1
    end_num = int(end_qid[1:])      # 'q014' -> 14
    
    chunk_qna = {}
    for qid, qna in qna_pairs.items():
        if qid.startswith('q'):
            try:
                q_num = int(qid[1:])
                if start_num <= q_num <= end_num:
                    chunk_qna[qid] = qna
            except ValueError:
                continue
    
    return chunk_qna


def format_chunk_qna_for_agent(chunk_qna: Dict[str, Dict[str, str]]) -> str:
    """
    Format chunk QNA pairs into a readable string for agent consumption.
    
    Args:
        chunk_qna: QNA pairs for a specific chunk
        
    Returns:
        Formatted string with question-answer pairs
    """
    if not chunk_qna:
        return "No questions in this chunk."
    
    formatted_lines = []
    for qid in sorted(chunk_qna.keys()):
        qna = chunk_qna[qid]
        formatted_lines.append(f"{qid.upper()}: {qna['question']}")
        formatted_lines.append(f"Answer: {qna['answer']}")
        formatted_lines.append("")  # Blank line for readability
    
    return "\n".join(formatted_lines)


def get_all_chunks_qna(phase3_data: Dict) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Extract all 6 chunks of QNA pairs from Phase 3 data.
    
    Args:
        phase3_data: Phase 3 JSON data
        
    Returns:
        Dict mapping chunk_name to QNA pairs
        Example: {'chunk1': {'q001': {...}, 'q002': {...}}, 'chunk2': {...}, ...}
    """
    # Extract all QNA pairs
    all_qna = extract_qna_pairs(phase3_data)
    
    # Get chunk ranges
    chunk_ranges = get_chunk_ranges()
    
    # Extract each chunk
    chunks = {}
    for chunk_name, start_qid, end_qid in chunk_ranges:
        chunk_qna = extract_chunk_qna(all_qna, start_qid, end_qid)
        chunks[chunk_name] = chunk_qna
    
    return chunks


def get_chunk_summary(chunk_qna: Dict[str, Dict[str, str]]) -> str:
    """
    Get a summary of a chunk (number of questions, question IDs).
    
    Args:
        chunk_qna: QNA pairs for a specific chunk
        
    Returns:
        Summary string
    """
    if not chunk_qna:
        return "Empty chunk"
    
    qids = sorted(chunk_qna.keys())
    return f"{len(qids)} questions ({qids[0]} to {qids[-1]})"

