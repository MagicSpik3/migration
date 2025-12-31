import os
import time
import shutil
import json
from src.specs.architect import RArchitect
from src.specs.optimizer import CodeOptimizer
from src.specs.qa_engineer import QAEngineer
from src.specs.doc_generator import DocumentationEngine
from src.utils.manifest_manager import ManifestManager
from src.specs.package_manager import PackageManager

class MigrationOrchestrator:
    def __init__(self, project_root="."):
        self.project_root = os.path.abspath(project_root)
        self.manifest_manager = ManifestManager(self.project_root)
        self.architect = RArchitect(self.project_root)
        self.optimizer = CodeOptimizer(self.project_root)
        self.qa_engineer = QAEngineer(self.project_root)
        self.doc_engine = DocumentationEngine(self.project_root)
        self.pkg_manager = PackageManager(self.project_root)

    def run(self, force=False):
        print(f"🚀 Starting Migration Pipeline for: {self.project_root}")
        start_time = time.time()

        # Step 1: Manifest
        print("\n[Step 1] 📋 Scanning & Manifesting...")
        if force or not os.path.exists(self.manifest_manager.manifest_path):
            self.manifest_manager.discover_legacy_files()
            print("   ✅ Manifest generated.")
        else:
            print("   ⏩ Using existing manifest.")

        # Step 2: Architect (SPSS -> R)
        print("\n[Step 2] 🏛️  Architecting R Solution...")
        self.architect.run()

        # Step 3: Optimization (Refactoring & Logic Check)
        print("\n[Step 3] 🔧 Optimization & Refactoring...")
        # Force optimization if requested to ensure state is fresh
        self.optimizer.run(force_all=force)

        # Step 4: Packaging
        print("\n[Step 4] 📦 Packaging...")
        self.pkg_manager.create_description()

        # Step 5: QA Engineering (Unit Tests)
        print("\n[Step 5] 🧪 QA Engineering...")
        qa_passed = self.qa_engineer.run()
        
        if not qa_passed:
            print("\n⚠️  WARNING: Some Unit Tests Failed.")
        else:
            print("\n✅ All Unit Tests Passed.")

        # Step 6: Documentation
        print("\n[Step 6] 📚 Generating Documentation...")
        self.doc_engine.run()

        # Step 7: Final Report
        duration = round(time.time() - start_time, 2)
        print(f"\n✨ Migration Complete in {duration}s.")
        return qa_passed

if __name__ == "__main__":
    # Allow running directly for testing
    orchestrator = MigrationOrchestrator()
    orchestrator.run()