import os
import subprocess
import tempfile
import sys
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# Workspace for the agent's file operations
WORKSPACE_DIR = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
os.makedirs(WORKSPACE_DIR, exist_ok=True)

def _get_safe_path(filename: str) -> str:
    """Ensure the path is within the workspace."""
    # Prevent directory traversal
    base_name = os.path.basename(filename)
    safe_path = os.path.abspath(os.path.join(WORKSPACE_DIR, base_name))
    if not safe_path.startswith(WORKSPACE_DIR):
        raise ValueError("Invalid path: Access denied.")
    return safe_path

def search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo."""
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        formatted_results = []
        for r in results:
            formatted_results.append(f"Title: {r.get('title')}\nLink: {r.get('href')}\nSnippet: {r.get('body')}\n")
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Error executing search: {str(e)}"

def run_code(code: str) -> str:
    """Execute Python code in a sandboxed subprocess with a timeout."""
    temp_path = None
    try:
        # Create a temporary file to hold the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        # Run the code using a subprocess with a timeout (e.g., 5 seconds)
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=10.0,
            cwd=WORKSPACE_DIR # Run in the workspace directory
        )
        
        # Clean up
        os.remove(temp_path)

        output = result.stdout
        if result.stderr:
            output += f"\nStderr:\n{result.stderr}"
        
        if not output.strip():
            return "Code executed successfully with no output."
        return output
    except subprocess.TimeoutExpired:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return "Error: Code execution timed out after 10 seconds."
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return f"Error executing code: {str(e)}"

def read_file(filename: str) -> str:
    """Read a file from the workspace."""
    try:
        safe_path = _get_safe_path(filename)
        if not os.path.exists(safe_path):
            return f"Error: File '{filename}' not found."
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(filename: str, content: str) -> str:
    """Write a file to the workspace."""
    try:
        safe_path = _get_safe_path(filename)
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to '{filename}'."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def list_dir() -> str:
    """List all files in the workspace directory."""
    try:
        files = os.listdir(WORKSPACE_DIR)
        if not files:
            return "Workspace is empty."
        return "Files in workspace:\n" + "\n".join(f"- {f}" for f in files)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def fetch_url(url: str) -> str:
    """Fetch and extract plain text from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        # Limit to first 10,000 characters to avoid huge context sizes
        return text[:10000]
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

# Register tools for the agent
AVAILABLE_TOOLS = {
    "search": search,
    "run_code": run_code,
    "read_file": read_file,
    "write_file": write_file,
    "list_dir": list_dir,
    "fetch_url": fetch_url
}

# Define schema for the LLM
TOOLS_SCHEMA = [
    {
        "name": "search",
        "description": "Search the web for information using DuckDuckGo.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "run_code",
        "description": "Execute Python code in a sandboxed subprocess and get the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The Python code to execute. Must be valid Python code."}
            },
            "required": ["code"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file from the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The name of the file to read."}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "write_file",
        "description": "Write contents to a file in the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "The name of the file to write to."},
                "content": {"type": "string", "description": "The content to write to the file."}
            },
            "required": ["filename", "content"]
        }
    }
]
