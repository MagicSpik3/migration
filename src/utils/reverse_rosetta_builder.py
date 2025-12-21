import pandas as pd
import sys
import os
import re
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.utils.ollama_client import get_ollama_response
from src.utils.spss_scanner import SPSSCommandScanner

ROSETTA_PROMPT_SPSS_TO_R = """
You are an expert in migrating legacy SPSS syntax to R (tidyverse).
I will give you an SPSS command. Your task is to provide the best R equivalent.

Rules:
1. Prioritize `dplyr`, `lubridate`, and `tidyr`.
2. For `COMPUTE`, suggest `mutate()`.
3. For `SELECT IF`, suggest `filter()`.
4. For `AGGREGATE`, suggest `group_by() %>% summarise()`.
5. For `RECODE`, suggest `case_when()`.
6. For `GET DATA` or `GET`, suggest `readr::read_csv()` or `haven::read_sav()`.

SPSS Command: {spss_cmd}

Return ONLY a JSON object:
{{
    "spss_command": "{spss_cmd}",
    "r_equivalent": "The R function (e.g. dplyr::mutate)",
    "usage_example": "Brief R code snippet"
}}
"""

def extract_json(text):
    """Robust JSON extractor"""
    try:
        # Try finding the first { and last }
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            json_str = text[start:end]
            return json.loads(json_str)
    except Exception as e:
        return None
    return None

def build_reverse_rosetta(repo_path):
    scanner = SPSSCommandScanner()
    counts = scanner.scan_directory(repo_path)
    commands = [cmd for cmd, count in counts.most_common()]
    
    results = []
    print(f"--- Building Reverse Rosetta Stone for {len(commands)} commands ---")
    
    for cmd in commands:
        print(f"Mapping: {cmd}...")
        prompt = ROSETTA_PROMPT_SPSS_TO_R.format(spss_cmd=cmd)
        response = get_ollama_response(prompt)
        
        data = extract_json(response)
        
        if data:
            results.append(data)
        else:
            print(f"⚠️ Failed to parse JSON for {cmd}. LLM Output:\n{response[:100]}...")
            # Fallback entry so we don't lose the row
            results.append({
                "spss_command": cmd, 
                "r_equivalent": "MANUAL_CHECK_REQUIRED", 
                "usage_example": response
            })

    df = pd.DataFrame(results)
    output_path = "r_rosetta_stone.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✅ Reverse Rosetta Stone saved to '{output_path}'")
    print(df.to_markdown())

if __name__ == "__main__":
    repo_path = os.path.expanduser("~/git/dummy_spss_repo")
    build_reverse_rosetta(repo_path)