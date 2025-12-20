import re

def parse_spss_value_labels(spss_syntax):
    """
    Parses a string of SPSS syntax to extract Value Labels.
    Returns a dict: { 'var_name': { 1: 'Label', 2: 'Label' } }
    """
    labels_map = {}
    
    # Normalize: Remove markdown code blocks if they exist (just in case)
    spss_syntax = spss_syntax.replace("```spss", "").replace("```", "")
    
    # Split by period to get commands, but handle newlines flexibly
    commands = spss_syntax.split('.')
    
    for cmd in commands:
        cmd = cmd.strip()
        # Case-insensitive check
        if not cmd.upper().startswith("VALUE LABELS"):
            continue
            
        # Parse: VALUE LABELS varname 1 'Label'...
        # We replace newlines with spaces to make regex easier
        clean_cmd = cmd.replace("\n", " ")
        
        # Regex explanation:
        # 1. match "VALUE LABELS" (case insensitive)
        # 2. match the variable name (word chars)
        # 3. capture the rest of the string
        match = re.search(r"VALUE LABELS\s+(\w+)\s+(.*)", clean_cmd, re.IGNORECASE)
        
        if not match:
            continue
            
        var_name = match.group(1)
        content = match.group(2)
        
        # Extract pairs: 1 "Male" or 1 'Male'
        pairs = re.findall(r"(\d+)\s+['\"]([^'\"]+)['\"]", content)
        
        if pairs:
            # Convert to dictionary {1: 'Male', ...}
            var_labels = {int(k): v for k, v in pairs}
            labels_map[var_name] = var_labels
        
    return labels_map