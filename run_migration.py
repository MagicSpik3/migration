import sys
import argparse
import os
from src.utils.manifest_manager import ManifestManager
from src.specs.analyst import SpecAnalyst
from src.specs.architect import RArchitect
from src.specs.validator import CodeValidator   # <--- NEW IMPORT
from src.specs.optimizer import CodeOptimizer
from src.specs.controller import PipelineController
from src.specs.qa_engineer import QAEngineer
from src.specs.package_manager import PackageManager

def run_full_migration(target_dir, force_optimize=False):
    print("🚀 STARTING MIGRATION PIPELINE 🚀")
    print("====================================")

    # 1. MANIFEST (The Map)
    print("\n[Step 1] 🗺️  Mapping Dependencies...")
    syntax_dir = os.path.join(target_dir, "syntax")
    manager = ManifestManager(syntax_dir)
    manager.generate_manifest()

    # 2. ANALYST (The Brain)
    print("\n[Step 2] 🧠 Analyzing Intent...")
    analyst = SpecAnalyst()
    analyst.run()

    # 3. ARCHITECT (The Builder)
    print("\n[Step 3] 🏗️  Drafting R Code...")
    # PASS THE TARGET DIR HERE!
    architect = RArchitect(project_root=target_dir) 
    architect.run()


    # --- NEW STEP: STATIC VALIDATION ---
    print("\n[Step 3.5] 🧐 Validating Draft Logic...")
    validator = CodeValidator()
    if not validator.run():
        print("\n🛑 PIPELINE HALTED: Critical Logic Errors detected in Draft.")
        print("   The Architect produced code that breaks the pipeline (e.g., missing returns).")
        sys.exit(1) # Fail fast so you don't optimize broken code
    # -----------------------------------

    # [Step 4] Optimizing & Testing...
    print("\n[Step 4] 🔧 Optimizing & Testing...")
    optimizer = CodeOptimizer()
    optimizer.run(force_all=force_optimize)
    
    # [Step 4.2] Packaging...
    print("\n[Step 4.2] 📦 Packaging...")
    pm = PackageManager(target_dir) 
    pm.generate_description()

    # [Step 4.5] QA Engineering...
    print("\n[Step 4.5] 🧪 QA Engineering (Comprehensive Unit Tests)...")
    qa = QAEngineer()
    qa_passed = qa.run()
    
    if not qa_passed:
        print("\n⚠️ WARNING: Some Unit Tests Failed.")

    # 5. CONTROLLER (The Orchestrator)
    print("\n[Step 5] 🎛️  Building Main Controller...")
    controller = PipelineController()
    controller.generate_main()

    print("\n✅ MIGRATION PIPELINE COMPLETE.")
    print(f"👉 Run: Rscript {target_dir}/main.R")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the SPSS to R Migration Pipeline")
    parser.add_argument("--target", default="~/git/dummy_spss_repo", help="Path to target repo")
    parser.add_argument("--force", action="store_true", help="Force re-optimization even if lint is clean")
    
    args = parser.parse_args()
    target_path = os.path.expanduser(args.target)
    
    run_full_migration(target_path, force_optimize=args.force)
