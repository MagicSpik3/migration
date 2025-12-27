import json
import requests
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Default Constants
DEFAULT_API_ENDPOINT = "http://localhost:11434/api/generate"
# You mentioned testing Qwen2.5-coder, but switch to "llama3.2:3b" if preferred
DEFAULT_MODEL = "qwen2.5-coder:latest" 

def get_ollama_response(
    prompt: str, 
    model: str = DEFAULT_MODEL, 
    endpoint: str = DEFAULT_API_ENDPOINT, 
    json_mode: bool = False
) -> str | None:
    """
    Sends a prompt to the Ollama API and returns the generated text response.

    Args:
        prompt (str): The input prompt for the LLM.
        model (str): The model tag to use (e.g., 'qwen2.5-coder:latest').
        endpoint (str): The URL of the Ollama API.
        json_mode (bool): If True, forces the model to respond in JSON format.
                          WARNING: Do NOT use this for generating SPSS code blocks,
                          as it forces the code into a string with escaped quotes.

    Returns:
        str | None: The text content of the response, or None if an error occurred.
    """
    logger.info(f"Sending request to Ollama (Model: {model}, JSON Mode: {json_mode})...")

    headers = {"Content-Type": "application/json"}

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,  # <--- CRITICAL FOR DETERMINISTIC CODE
            "num_predict": 1000   # Ensure we don't get cut off
        }
    }
    

    if json_mode:
        payload["format"] = "json"

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            # Long timeout because code generation on local CPU can be slow
            timeout=120 
        )
        response.raise_for_status()

        response_data = response.json()
        
        raw_text = response_data.get("response", "").strip()

        # --- NEW CLEANING LOGIC ---
        # Remove markdown code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            # Remove first line if it's a backtick fence (e.g., ```spss)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line if it's a backtick fence
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()
        # --------------------------

        return raw_text

    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API Request Failed: {e}")
        return None
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from Ollama API.")
        return None