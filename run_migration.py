import sys
import argparse
import os
from src.utils.manifest_manager import ManifestManager
from src.specs.analyst import SpecAnalyst
from src.specs.architect import RArchitect
# Removed validator import
from src.specs.optimizer import CodeOptimizer
from src.specs.controller import PipelineController
from src.specs.qa_engineer import QAEngineer
from src.specs.package_manager import PackageManager

def run_full_migration(target_dir, force_optimize=False):
    print("🚀 STARTING MIGRATION PIPELINE 🚀")
    print("====================================")

    # 1. MANIFEST
    print("\n[Step 1] 🗺️  Mapping Dependencies...")
    syntax_dir = os.path.join(target_dir, "syntax")
    manager = ManifestManager(syntax_dir)
    manager.generate_manifest()

    # 2. ANALYST
    print("\n[Step 2] 🧠 Analyzing Intent...")
    analyst = SpecAnalyst()
    analyst.run()

    # 3. ARCHITECT
    print("\n[Step 3] 🏗️  Drafting R Code...")
    architect = RArchitect(project_root=target_dir) 
    architect.run()

    # [Step 4] Optimizing (Includes Validation & Safety Latch)
    print("\n[Step 4] 🔧 Optimizing & Testing (With Safety Latch)...")
    optimizer = CodeOptimizer(project_root=target_dir)
    optimizer.run(force_all=force_optimize)
    
    # [Step 4.2] Packaging
    print("\n[Step 4.2] 📦 Packaging...")
    pm = PackageManager(target_dir) 
    pm.generate_description()

    # [Step 4.5] QA Engineering
    print("\n[Step 4.5] 🧪 QA Engineering (Comprehensive Unit Tests)...")
    qa = QAEngineer()
    qa_passed = qa.run()
    
    if not qa_passed:
        print("\n⚠️ WARNING: Some Unit Tests Failed.")

    # 5. CONTROLLER
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