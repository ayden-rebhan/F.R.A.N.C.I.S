# Main entry point for F.R.A.N.C.I.S AI Assistant using Ollama Qwen3
import requests
import json
import sys
import os
import glob
from typing import List, Dict

OLLAMA_BASE_URL = "http://localhost:11434/api"
MODEL_NAME = "qwen3:8b"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import sys


def _run_gui():
    try:
        # Import Tk GUI
        from gui_tk import main as gui_main
    except Exception:
        from src.gui_tk import main as gui_main
    gui_main()


if __name__ == "__main__":
    _run_gui()
