import json
import logging
import time
from pathlib import Path
from groq import Groq, RateLimitError

logger = logging.getLogger("nb2pdf.llm")

class APIKeyManager:
    def __init__(self, keys_file: str = "api_keys.json"):
        self.keys_file = Path(keys_file)
        if not self.keys_file.exists():
            raise FileNotFoundError(f"API keys file not found: {self.keys_file}")
        
        self.keys = self._load_keys()
        self.current_index = 0
        
        if not self.keys:
            raise ValueError(f"No API keys found in {self.keys_file}")
            
    def _load_keys(self) -> list[str]:
        with open(self.keys_file, "r") as f:
            return json.load(f)
            
    def get_current_key(self) -> str:
        return self.keys[self.current_index]
        
    def rotate_key(self):
        self.current_index = (self.current_index + 1) % len(self.keys)
        logger.info(f"Rotated API key. Now using key index {self.current_index} out of {len(self.keys)}.")

class GroqLLM:
    def __init__(self, keys_file: str = "api_keys.json"):
        self.key_manager = APIKeyManager(keys_file)
        self.client = self._create_client()
        
    def _create_client(self) -> Groq:
        return Groq(api_key=self.key_manager.get_current_key())
        
    def rotate_client(self):
        self.key_manager.rotate_key()
        self.client = self._create_client()

# Singleton service instance
try:
    llm_service = GroqLLM("api_keys.json")
except Exception as e:
    logger.error(f"Failed to initialize LLM service: {e}")
    llm_service = None

def call_llm(messages: list[dict], model: str = "llama-3.1-8b-instant", max_tokens: int = 1500) -> str:
    """
    Calls Groq LLM with automatic rate limit handling and key rotation.
    If limit is hit, shuffles to next key and retries seamlessly.
    """
    if not llm_service:
        raise RuntimeError("LLM service is not initialized.")
        
    max_retries = len(llm_service.key_manager.keys) * 2  # Allows full cycle twice
    retries = 0
    
    while retries < max_retries:
        try:
            response = llm_service.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.2
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            logger.warning(f"Rate limit hit! message: {e}. Rotating API key...")
            llm_service.rotate_client()
            retries += 1
            time.sleep(0.5) # Slight pause to allow rotation to settle
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            retries += 1
            time.sleep(2)
            if "authentication" in str(e).lower():
                 # Force rotation if authn error
                 llm_service.rotate_client()
            elif retries >= 3:
                 raise e
                 
    raise Exception("Max retries exceeded across all Groq API keys.")
