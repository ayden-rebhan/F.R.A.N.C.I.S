import requests
import json
import os
import glob
from typing import List, Dict

OLLAMA_BASE_URL = "http://localhost:11434/api"
MODEL_NAME = "qwen3:8b"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_file_content(file_path: str) -> str:
    """Read and return the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def search_files(pattern: str) -> List[str]:
    """Search for files in the project directory."""
    return glob.glob(os.path.join(PROJECT_ROOT, pattern), recursive=True)


def get_project_context(query: str = None) -> Dict[str, str]:
    """Get relevant project files and their contents based on query."""
    context = {}

    # Add README for project overview
    readme_path = os.path.join(PROJECT_ROOT, 'README.md')
    if os.path.exists(readme_path):
        context['README.md'] = get_file_content(readme_path)

    if query:
        # Search for relevant files based on query
        patterns = ['**/*.py', '**/*.md', '**/*.json']
        for pattern in patterns:
            files = search_files(pattern)
            for file in files:
                rel_path = os.path.relpath(file, PROJECT_ROOT)
                content = get_file_content(file)
                if query.lower() in content.lower():
                    context[rel_path] = content

    return context


def check_model_availability():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(model["name"] == MODEL_NAME for model in models)
        return False
    except Exception:
        return False


def generate_response(prompt: str, context: Dict[str, str] = None) -> str:
    headers = {
        "Content-Type": "application/json",
    }

    # Construct system message for coding assistance
    system_message = (
        "You are F.R.A.N.C.I.S (Facilitating Residential Assistance, Navigation, and Comfort with Intelligent Systems),\n"
        "an AI assistant with access to the local project files. You can help with coding tasks, file management, and project organization.\n"
        "When asked about code or files, refer to the provided context. If asked to make changes, explain what changes are needed and why."
    )

    # Build context message
    context_message = ""
    if context:
        context_message = "\n\nProject files:\n"
        for file_path, content in context.items():
            context_message += f"\n--- {file_path} ---\n{content}\n"

    # Combine messages
    full_prompt = f"{system_message}\n{context_message}\n\nUser: {prompt}\nF.R.A.N.C.I.S:"

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    try:
        # First check if model is available
        if not check_model_availability():
            return f"Error: Model '{MODEL_NAME}' not found. Please make sure it's pulled using 'ollama pull {MODEL_NAME}'"

        response = requests.post(
            f"{OLLAMA_BASE_URL}/generate",
            headers=headers,
            json=payload
        )

        if response.status_code == 404:
            return "Error: Cannot connect to Ollama. Make sure Ollama is running with 'ollama serve'"

        response.raise_for_status()
        data = response.json()
        return data.get("response", "[No response generated]")

    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Make sure Ollama is running with 'ollama serve'"
    except Exception as e:
        return f"Error: {str(e)}"
