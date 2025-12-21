import os
import shutil
import re
from src.utils.ollama_client import get_ollama_response
# We use the verification script as a library now
from tests.verification.verify_refactor import RefactorVerifier

# A list of specific refactoring "missions"
PATTERNS = [
    {
        "name": "Fix Date Math",
        "description": "Replace manual substring math (substr * 10000) with lubridate::ymd()",
        "prompt": """
        Check this code for "SPSS Date Math" (e.g. `as.numeric(substr(var, 1, 4)) * 10000`).
        If found, replace ONLY that logic with `lubridate::ymd(var)`.
        
        CRITICAL: 
        - Do NOT wrap ymd() in as.Date().
        - Do NOT keep the 'trunc' or 'paste0' logic. 
        - Just use `ymd(var_name)`.
        
        CODE:
        {code}
        """
    },
    {
        "name": "Fix Invalid Output",
        "description": "Replace cat(head(df)) with print(head(df)) to prevent crashes",
        "prompt": """
        Check if the code uses `cat(head(df))`. This causes R to crash.
        Replace it with `print(head(df))` or simply remove it.
        
        CODE:
        {code}
        """
    }
]

class AtomicRefactorer:
    def __init__(self, target_dir):
        self.target_dir = target_dir

    def verify_safe(self, original_path, candidate_path):
        """
        Runs the Twin-R verification. 
        Returns True ONLY if the logic is identical and it runs without error.
        """
        # We assume the 'ugly' v1 file is still in the sibling folder 'r_migrated'
        # Construct path to the original 'trusted' (but ugly) logic
        filename = os.path.basename(original_path)
        v1_path = original_path.replace("r_refactored", "r_migrated")
        
        if not os.path.exists(v1_path):
            print(f"      ⚠️  Cannot verify: Original 'r_migrated' file not found at {v1_path}")
            return False # Fail safe

        print(f"      🧪 Verifying against {os.path.basename(v1_path)}...")
        verifier = RefactorVerifier(v1_path, candidate_path)
        
        # Suppress standard output from verifier to keep logs clean
        try:
            return verifier.verify()
        except Exception as e:
            print(f"      ❌ Verification Exception: {e}")
            return False

    def apply_refactor(self, file_path, pattern):
        with open(file_path, 'r') as f:
            code = f.read()

        # Ask LLM if pattern exists and to fix it
        full_prompt = f"{pattern['prompt'].format(code=code)}\n\nIf the pattern is NOT present, return exactly: NO_CHANGE"
        
        response = get_ollama_response(full_prompt)
        
        if "NO_CHANGE" in response or len(response) < 10:
            return False # No changes needed

        # Extract code block
        if "```r" in response:
            candidate_code = response.split("```r")[1].split("```")[0].strip()
        elif "```" in response:
            candidate_code = response.split("```")[1].split("```")[0].strip()
        else:
            candidate_code = response.strip()

        # Save Candidate
        candidate_path = file_path + ".candidate"
        with open(candidate_path, 'w') as f:
            f.write(candidate_code)

        # Verify
        if self.verify_safe(file_path, candidate_path):
            print(f"      ✅ Verified! Committing '{pattern['name']}'")
            shutil.move(candidate_path, file_path)
            return True
        else:
            print(f"      ❌ Verification Failed for '{pattern['name']}'. Reverting.")
            os.remove(candidate_path)
            return False

    def run(self):
        for root, dirs, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".R"):
                    full_path = os.path.join(root, file)
                    print(f"\n📂 Processing {file}...")
                    
                    # Run through all patterns sequentially
                    for pattern in PATTERNS:
                        changed = self.apply_refactor(full_path, pattern)
                        if changed:
                            print("      (Saved change)")

if __name__ == "__main__":
    # Ensure this points to where your "Bad Refactor" (or the copy of Migrated code) lives
    # For this to work, reset r_refactored to match r_migrated first!
    MIGRATED_DIR = os.path.expanduser("~/git/dummy_spss_repo/r_migrated")
    REFACTOR_DIR = os.path.expanduser("~/git/dummy_spss_repo/r_refactored")
    
    # Reset: Copy the ugly (but working) code to the refactor folder
    # This ensures we start with valid logic before applying atomic fixes
    if os.path.exists(REFACTOR_DIR):
        shutil.rmtree(REFACTOR_DIR)
    shutil.copytree(MIGRATED_DIR, REFACTOR_DIR)
    
    agent = AtomicRefactorer(REFACTOR_DIR)
    agent.run()