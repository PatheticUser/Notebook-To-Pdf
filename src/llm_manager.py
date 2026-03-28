import json
import logging
from pathlib import Path
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq

logger = logging.getLogger("nb2pdf.llm")

def get_keys(keys_file: str = "api_keys.json") -> list[str]:
    keys_path = Path(keys_file)
    if not keys_path.exists():
        raise FileNotFoundError(f"API keys file not found: {keys_path}")
    
    with open(keys_path, "r") as f:
        keys = json.load(f)
        
    if not keys:
        raise ValueError(f"No API keys found in {keys_path}")
        
    return keys

def get_llm(model: str = "llama-3.1-8b-instant", temperature: float = 0.2) -> BaseChatModel:
    """
    Returns a LangChain ChatGroq model configured with fallbacks for rate limit handling.
    """
    try:
        keys = get_keys()
    except Exception as e:
        logger.error(f"Failed to initialize LLM keys: {e}")
        raise
    
    # Create a ChatGroq instance for each key
    llms = [
        ChatGroq(model=model, temperature=temperature, api_key=key, max_retries=1)
        for key in keys
    ]
    
    if len(llms) == 1:
        return llms[0]
        
    # Set the first key's LLM as primary, and the rest as fallbacks
    primary_llm = llms[0]
    fallbacks = llms[1:]
    
    return primary_llm.with_fallbacks(fallbacks)
