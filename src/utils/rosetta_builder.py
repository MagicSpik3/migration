import pandas as pd
from src.utils.ollama_client import get_ollama_response
from src.utils.function_scanner import RFunctionScanner
from src.specs.prompts import ROSETTA_PROMPT

def build_rosetta_stone(r_file_path):
    scanner = RFunctionScanner()
    funcs = scanner.scan_file(r_file_path)
    
    results = []
    print(f"--- Building Rosetta Stone for {len(funcs)} functions ---")
    
    for func in funcs:
        print(f"Mapping: {func}...")
        prompt = ROSETTA_PROMPT.format(r_func=func)
        response = get_ollama_response(prompt)
        
        # Simple parsing (assuming LLM returns clean JSON or we clean it)
        try:
            # Strip markdown if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            import json
            data = json.loads(response)
            results.append(data)
        except:
            print(f"Failed to parse response for {func}")
            results.append({"r_function": func, "spss_equivalent": "ERROR", "notes": response})

    # Save to CSV
    df = pd.DataFrame(results)
    df.to_csv("spss_rosetta_stone.csv", index=False)
    print("\n✅ Rosetta Stone saved to 'spss_rosetta_stone.csv'")
    print(df.to_markdown())

if __name__ == "__main__":
    r_file = "/home/jonny/git/weekly_deaths_rap/weekly.deaths/R/registration_delays.R"
    build_rosetta_stone(r_file)