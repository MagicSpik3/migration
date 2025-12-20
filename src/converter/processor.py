import json
import os
import logging
from src.utils.ollama_client import get_ollama_response
from src.converter.prompts import (
    SYSTEM_PROMPT,
    VALUE_LABEL_TEMPLATE,
    LOGIC_TRANSLATION_TEMPLATE,
    ANALYSIS_TEMPLATE
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_translation_tasks(code_data):
    """
    Analyzes the input R code and assigns the correct prompt template.
    Returns a list of task dictionaries.
    """
    tasks = []
    for item in code_data:
        func_name = item['function_name']
        code = item['code_chunk']

        # --- Heuristic: Choose the right Template ---
        # If the code immediately starts a list() definition, it's likely Value Labels.
        # We look at the first 200 chars to ignore function headers/comments.
        is_value_label_task = "list(" in code[:200] and "=" in code[:200]

        if is_value_label_task:
            prompt = VALUE_LABEL_TEMPLATE.format(
                system_prompt=SYSTEM_PROMPT,
                r_code=code
            )
            task_type = "value_labels"
        else:
            prompt = LOGIC_TRANSLATION_TEMPLATE.format(
                system_prompt=SYSTEM_PROMPT,
                r_code=code
            )
            task_type = "logic_translation"

        # 1. Translation Task
        tasks.append({
            'id': func_name,
            'type': task_type,
            'context': code,
            'prompt': prompt,
            'json_mode': False  # CRITICAL: False for code generation
        })

        # 2. Metadata Analysis Task (Dependency Graphing)
        tasks.append({
            'id': func_name,
            'type': 'metadata_analysis',
            'context': code,
            'prompt': ANALYSIS_TEMPLATE.format(r_code=code),
            'json_mode': True   # Optimization: Force JSON for data extraction
        })

    return tasks

def process_conversion(input_file, output_file):
    """
    Main processing loop: Reads R data -> Generates Prompts -> Calls LLM -> Saves Output.
    """
    # 1. Validate Input
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run the crawler first.")
        return

    # 2. Load Data
    with open(input_file, 'r') as f:
        r_data = json.load(f)

    # 3. Prepare Tasks
    tasks = generate_translation_tasks(r_data)
    logger.info(f"Generated {len(tasks)} tasks from {len(r_data)} functions.")

    # 4. Run LLM & Stream Output
    # We write line-by-line (jsonl) so we don't lose progress if it crashes.
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as outfile:
        for i, task in enumerate(tasks):
            logger.info(f"Processing {i+1}/{len(tasks)}: {task['id']} [{task['type']}]")

            response = get_ollama_response(
                prompt=task['prompt'], 
                json_mode=task.get('json_mode', False)
            )

            if response:
                result = {
                    "function_name": task['id'],
                    "task_type": task['type'],
                    "r_code": task['context'],
                    "llm_output": response
                }
                json.dump(result, outfile)
                outfile.write('\n')
            else:
                logger.warning(f"Skipping {task['id']} due to LLM error.")

    logger.info(f"Processing complete. Results saved to {output_file}")

if __name__ == "__main__":
    # Resolve paths relative to the project root
    # Assuming this script is in src/converter/processor.py
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Standard location for the crawler output
    INPUT_PATH = os.path.join(BASE_DIR, "data", "intermediate", "r_code_data.json")
    OUTPUT_PATH = os.path.join(BASE_DIR, "data", "output", "spss_conversion.jsonl")

    process_conversion(INPUT_PATH, OUTPUT_PATH)