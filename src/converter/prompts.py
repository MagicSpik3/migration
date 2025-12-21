"""
This module contains the prompt templates used for R to SPSS conversion.
It separates the system persona from specific task templates to allow for
easier tuning and one-shot example injection.
"""

# ==============================================================================
# SYSTEM PERSONA
# ==============================================================================
SYSTEM_PROMPT = """You are an expert Statistical Programmer specialized in migrating legacy R code to IBM SPSS Syntax.
Your goal is to produce semantically equivalent SPSS code that runs in a strict environment (PSPP).
You prioritize standard commands (COMPUTE, AGGREGATE, SELECT IF) over complex macros.
"""

# ==============================================================================
# TEMPLATE 1: FACTOR LEVELS / VALUE LABELS
# ==============================================================================
# Optimized based on test failures. Includes a strict One-Shot example
# to prevent the "Label" = Value syntax inversion error.
VALUE_LABEL_TEMPLATE = """
{system_prompt}

TASK:
Convert the provided R list of categories into SPSS 'VALUE LABELS' commands.

CRITICAL SYNTAX RULES:
1. Syntax Format: VALUE LABELS varname value "Label".
   - CORRECT: VALUE LABELS gender 1 "Male" 2 "Female".
   - WRONG:   VALUE LABELS gender "Male" = 1.
2. Do NOT wrap the code in !IF blocks or !DEFINE macros unless explicitly asked.
3. Do NOT include defensive error checking (e.g., !GETDEFS, !ERROR).
4. End every command with a period (.).

R CODE INPUT:
{r_code}

OUTPUT:
Provide ONLY the SPSS Syntax block.
"""
# ==============================================================================
# TEMPLATE 2: DPLYR LOGIC TRANSLATION
# ==============================================================================
# specific mappings for dplyr verbs to SPSS commands to guide the LLM.
LOGIC_TRANSLATION_TEMPLATE = """
{system_prompt}

TASK:
Convert the provided R function logic into valid SPSS Syntax.

CRITICAL SYNTAX RULES (DO NOT IGNORE):

1. **Date Parsing (MANDATORY):**
   - R input dates like "20230101" are STRINGS.
   - You MUST convert them using: `COMPUTE var_new = NUMBER(var, YMD8).`
   - NEVER use `DATE.DMY` with `SUBSTR`. It causes type mismatches.
   - Always define the format: `FORMATS var_new (DATE11).`

2. **No Nesting:**
   - **NEVER** put `EXECUTE`, `AGGREGATE`, or `DATASET` commands inside a `DO IF` block.
   - SPSS is procedural. Calculate variables globally first, then use `SELECT IF` to filter.
   
3. **Error Handling:**
   - SPSS has no `STOP` command.
   - Instead of stopping, flag the bad data and filter it out.
   - Pattern:
     ```spss
     COMPUTE error_flag = (delay < 0).
     SELECT IF (error_flag = 0).
     ```

4. **Variables:**
   - Remember that `GET DATA` imports all columns as Strings (A50). You MUST explicitly convert them to numbers before doing math (e.g., subtraction).

R CODE INPUT:
{r_code}

OUTPUT:
Provide ONLY the SPSS Syntax.
"""


# ==============================================================================
# TEMPLATE 3: METADATA ANALYSIS
# ==============================================================================
# Used by the crawler to build the dependency graph.
ANALYSIS_TEMPLATE = """
Analyze the following R code chunk and extract its dependencies and I/O.

R CODE:
{r_code}

OUTPUT FORMAT (JSON):
{{
    "input_datasets": ["list", "of", "dataframes", "read", "or", "used"],
    "output_variables": ["list", "of", "new", "variables", "created"],
    "external_calls": ["functions", "called", "e.g.", "create_delay_summary"]
}}
"""


DATA_INFERENCE_PROMPT = """
You are a Data Engineer analyzing legacy R code. 
Your goal is to determine the input data structure required to run this function without errors.

Analyze the following R function code. 
Identify all arguments. If an argument is a dataframe, identify:
1. The likely column names used.
2. The data type of those columns.
3. CRITICAL: If a column is modified in place, it MUST be listed as an INPUT column.
4. DATE FORMATS: If a column is parsed as a date, provide "allowed_values" matching that format.

5. REVERSE ENGINEERING VALIDATION (HIGHEST PRIORITY):
   You must generate data that avoids `stop()` or error conditions.
   
   Pattern: `x = A - B` followed by `if (x < 0) stop(...)`
   Rule: This implies A must be >= B.
   Action: Assign a LATER date to A and an EARLIER date to B.
   
   Example from your current task:
   - If code has `delay = dor - dod` and fails if `delay < 0`.
   - Then `dor` (A) MUST be later than `dod` (B).
   - Correct Schema: "dor": ["20230105"], "dod": ["20230101"].

Return ONLY valid JSON in this format:
{{
    "arguments": {{
        "arg_name": {{
            "type": "dataframe",
            "columns": {{
                "dod": {{ "type": "string", "allowed_values": ["20230101"] }},
                "dor": {{ "type": "string", "allowed_values": ["20230105"] }}
            }}
        }}
    }}
}}

R Code:
{r_code}
"""

CANDIDATE_PROMPT_TEMPLATE = LOGIC_TRANSLATION_TEMPLATE