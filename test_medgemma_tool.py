#!/usr/bin/env python3
"""
Simple test for MedGemma Tool

Usage:
    python test_medgemma_tool.py
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.aether_2.tools.medgemma_tool import MedGemmaTool


def test_tool():
    """Test the MedGemma tool with a simple query."""
    
    print("\n" + "=" * 60)
    print("Testing MedGemma Tool")
    print("=" * 60)
    
    # Check endpoint
    endpoint_id = os.getenv("MEDGEMMA_ENDPOINT_ID", "")
    if not endpoint_id:
        print("\n⚠️  MEDGEMMA_ENDPOINT_ID not set!")
        print("   Set it with: export MEDGEMMA_ENDPOINT_ID='your-endpoint-id'")
        print("\n   Testing tool initialization only...\n")
    else:
        print(f"\n✅ Endpoint: {endpoint_id}\n")
    
    # Create tool
    tool = MedGemmaTool()
    print(f"Tool name: {tool.name}")
    print(f"Tool description: {tool.description[:100]}...")
    
    # Test queries (only if endpoint is set)
    if endpoint_id:
        test_queries = [
            "low vitamin D",
            "hypothyroidism",
            "chronic fatigue and low iron"
        ]
        
        for query in test_queries:
            print("\n" + "-" * 60)
            print(f"Query: '{query}'")
            print("-" * 60)
            result = tool._run(query=query)
            print(f"Response: {result}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_tool()
