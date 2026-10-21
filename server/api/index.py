import sys
from pathlib import Path

# Add the server directory (parent of api/) to sys.path so app modules are resolved
SERVER_DIR = Path(__file__).resolve().parent.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from app.main import app
