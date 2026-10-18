"""Main entrypoint for trajectory generation service.

Run with: uvicorn trajgen.main:app --reload
Or: python -m trajgen.main
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present (must be before other imports that use os.environ)
# override=False ensures existing environment variables (e.g. from Railway) are not overwritten
load_dotenv(override=False)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from trajgen.api import app


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("DEMO TRAJECTORY GENERATOR SERVICE")
    print("=" * 80)
    print("WARNING: All vehicle parameters and simulation results are")
    print("         NOTIONAL DEMO VALUES ONLY for demonstration purposes.")
    print("         They do NOT represent any real vehicle or system.")
    print("=" * 80)
    print()
    
    uvicorn.run(
        "trajgen.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
