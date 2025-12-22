import sys
import argparse
from src.utils.manifest_manager import ManifestManager
from src.specs.analyst import SpecAnalyst
from src.specs.architect import RArchitect
from src.specs.optimizer import CodeOptimizer
from src.specs.controller import PipelineController
import os

def run_full_migration(target_dir, force_optimize=False):
    print("🚀 STARTING MIGRATION PIPELINE 🚀")
    print("====================================")

    # 1. MANIFEST (The Map)
    print("\n[Step 1] 🗺️  Mapping Dependencies...")
    # Point to the 'syntax' folder inside the target repo
    syntax_dir = os.path.join(target_dir, "syntax")
    manager = ManifestManager(syntax_dir)
    manager.generate_manifest()

    # 2. ANALYST (The Brain)
    print("\n[Step 2] 🧠 Analyzing Intent...")
    analyst = SpecAnalyst()
    analyst.run()

    # 3. ARCHITECT (The Builder)
    print("\n[Step 3] 🏗️  Drafting R Code...")
    architect = RArchitect()
    architect.run()

    # 4. OPTIMIZER (The QA)
    print("\n[Step 4] 🔧 Optimizing & Testing...")
    optimizer = CodeOptimizer()
    # Runs with FORCE if requested, to catch logic bugs in "clean" code
    optimizer.run(force_all=force_optimize)

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