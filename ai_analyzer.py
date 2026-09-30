import os
import time
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors
from prompts import SYSTEM_PROMPT, RESPONSE_SCHEMA, get_user_prompt
from response_validator import validate_ai_response, RequirementAnalysis, ResponseValidationError

# Locate and load environment variables from .env
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Supported default and fallback models
DEFAULT_MODEL = os.getenv("AI_MODEL", "gemini-3.5-flash")
FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-3.5-flash-lite")

class AIAnalyzerError(Exception):
    """Base exception for user-friendly AI analysis errors."""
    pass

class MissingAPIKeyError(AIAnalyzerError):
    """Raised when the Gemini API key is missing."""
    pass

class AuthenticationError(AIAnalyzerError):
    """Raised when the Gemini API key is invalid."""
    pass

class RateLimitError(AIAnalyzerError):
    """Raised when rate limits or quotas are exceeded."""
    pass

class ServiceUnavailableError(AIAnalyzerError):
    """Raised when the AI model is temporarily overloaded."""
    pass

class NetworkError(AIAnalyzerError):
    """Raised on connection failures."""
    pass

def get_ai_client() -> genai.Client:
    """
    Initializes and returns the Google GenAI client using GEMINI_API_KEY.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY")
    if not api_key or not api_key.strip():
        raise MissingAPIKeyError("Missing Gemini API Key. Please set GEMINI_API_KEY in your .env file.")
    
    return genai.Client(api_key=api_key.strip())

def _execute_gemini_request(client: genai.Client, model: str, prompt: str) -> str:
    """
    Internal call to Gemini API with strict JSON schema configuration.
    """
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=RESPONSE_SCHEMA,
        temperature=0.2,
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    if not response or not response.text:
        raise AIAnalyzerError("The AI returned an empty response. Please try again.")
    return response.text.strip()

def analyze_requirement(requirement: str, model_name: Optional[str] = None) -> RequirementAnalysis:
    """
    Sends a software requirement to Google Gemini and returns parsed analysis data
    including gaps, missing details, and ambiguity detection.
    """
    clean_req = requirement.strip()
    if not clean_req:
        raise AIAnalyzerError("Please enter a software requirement to analyze.")

    client = get_ai_client()
    selected_model = model_name or DEFAULT_MODEL
    user_prompt = get_user_prompt(clean_req)

    raw_response_text = None

    try:
        raw_response_text = _execute_gemini_request(client, selected_model, user_prompt)
    except errors.ServerError as se:
        # Automatic fallback on temporary traffic spike
        if selected_model != FALLBACK_MODEL:
            try:
                time.sleep(0.5)
                raw_response_text = _execute_gemini_request(client, FALLBACK_MODEL, user_prompt)
            except Exception:
                raise ServiceUnavailableError("The AI service is temporarily experiencing high traffic. Please try again in a few moments.") from se
        else:
            raise ServiceUnavailableError("The AI service is temporarily experiencing high traffic. Please try again in a few moments.") from se
    except errors.ClientError as ce:
        err_msg = str(ce)
        if "401" in err_msg or "403" in err_msg or "API_KEY_INVALID" in err_msg:
            raise AuthenticationError("Invalid Gemini API key provided. Please check GEMINI_API_KEY in your .env file.") from ce
        elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            raise RateLimitError("AI API rate limit or quota exceeded. Please wait a moment and try again.") from ce
        else:
            raise AIAnalyzerError("Unable to analyze the requirement at the moment. Please try again.") from ce
    except errors.APIError as ae:
        raise AIAnalyzerError("AI service error encountered. Please try again later.") from ae
    except (ConnectionError, TimeoutError, OSError) as net_err:
        raise NetworkError("Network error occurred while connecting to the AI service. Please check your internet connection.") from net_err
    except Exception as e:
        if isinstance(e, AIAnalyzerError):
            raise
        raise AIAnalyzerError("Unable to analyze the requirement at the moment. Please try again.") from e

    # Validate and parse using Pydantic validator
    try:
        return validate_ai_response(raw_response_text)
    except ResponseValidationError as rve:
        raise AIAnalyzerError(f"Response validation failed: {str(rve)}") from rve
