import argparse
import sys
from src.pipeline.orchestrator import MigrationOrchestrator

def main():
    parser = argparse.ArgumentParser(description="SPSS to R Migration Pipeline")
    parser.add_argument("--force", action="store_true", help="Force regeneration of all steps")
    parser.add_argument("--path", type=str, default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    try:
        orchestrator = MigrationOrchestrator(args.path)
        success = orchestrator.run(force=args.force)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"🔥 CRITICAL FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()