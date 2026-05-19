#!/usr/bin/env python3
"""
Generate Excel file from a patient JSON and a protocol JSON.

Usage:
    python generate_excel_from_protocol.py inputs/test_user17.json protocol.json
    python generate_excel_from_protocol.py inputs/test_user17.json  # uses inline protocol
"""

import json
import sys
import os
import pandas as pd


def create_nested_excel_data(data, parent_paths=[], skip_phase_prefix=True):
    """Create nested structure for Excel export"""
    items = []
    if isinstance(data, dict):
        for k, v in data.items():
            readable_key = k.replace('_', ' ').title()
            if skip_phase_prefix and readable_key in ['Phase1 Basic Intake', 'Phase2 Detailed Intake']:
                current_paths = parent_paths.copy()
            else:
                current_paths = parent_paths + [readable_key]
            
            if isinstance(v, dict):
                items.extend(create_nested_excel_data(v, current_paths, skip_phase_prefix))
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            for sub_k, sub_v in item.items():
                                sub_readable_key = sub_k.replace('_', ' ').title()
                                item_paths = current_paths + [f"Item {i+1}", sub_readable_key]
                                while len(item_paths) < 4:
                                    item_paths.append('')
                                item_paths.append(sub_v)
                                items.append(tuple(item_paths))
                else:
                    list_value = ', '.join(map(str, v)) if v else ''
                    item_paths = current_paths.copy()
                    while len(item_paths) < 4:
                        item_paths.append('')
                    item_paths.append(list_value)
                    items.append(tuple(item_paths))
            else:
                item_paths = current_paths.copy()
                while len(item_paths) < 4:
                    item_paths.append('')
                item_paths.append(v)
                items.append(tuple(item_paths))
    return items


def generate_excel(input_json_path: str, protocol_data: dict, output_path: str = None):
    """Generate Excel from patient JSON and protocol dict"""
    
    # Load patient data
    with open(input_json_path, 'r') as f:
        data = json.load(f)
    
    user_data = data[0]["user_full_data"]
    patient_data = user_data["patient_data"]
    biomarkers = user_data["latest_biomarker_results"]
    user_email = user_data["metadata"].get("email", "unknown@example.com")
    user_id = user_email.replace("@", "_at_").replace(".", "_")
    
    # Output path
    if not output_path:
        output_path = f"outputs/{user_id}/{user_id}.xlsx"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet 1: Patient Data
        nested_patient_data = create_nested_excel_data(patient_data)
        patient_df = pd.DataFrame(nested_patient_data, columns=['Category', 'Subcategory', 'Field', 'Detail', 'Value'])
        patient_df.to_excel(writer, sheet_name='Patient_Data', index=False)
        
        # Sheet 2: Biomarkers
        biomarkers_df = pd.DataFrame(list(biomarkers.items()), columns=['Biomarker', 'Value'])
        biomarkers_df.to_excel(writer, sheet_name='Biomarkers', index=False)
        
        # Sheet 3: Recommendations
        recommendations = protocol_data.get('supplement_recommendations', [])
        if recommendations:
            rec_data = []
            for rec in recommendations:
                rec_data.append({
                    'User Email': user_email,
                    'Supplement': rec.get('ingredient_name', ''),
                    'Dosage': rec.get('recommended_dosage', ''),
                    'Frequency': rec.get('frequency', ''),
                    'Why': rec.get('why', ''),
                    'Core Focus Area': ', '.join(rec.get('focus_area', [])) if isinstance(rec.get('focus_area'), list) else rec.get('focus_area', ''),
                    'Additional Comments': ''
                })
            recommendations_df = pd.DataFrame(rec_data)
            recommendations_df.to_excel(writer, sheet_name='Recommendations', index=False)
    
    print(f"✅ Excel created: {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_excel_from_protocol.py <input_json> [protocol_json]")
        sys.exit(1)
    
    input_json = sys.argv[1]
    
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'r') as f:
            protocol = json.load(f)
    else:
        print("No protocol JSON provided. Please provide protocol as second argument.")
        sys.exit(1)
    
    generate_excel(input_json, protocol)

