from google import genai
from google.genai import types
import os
import json
from typing import Any
from src.schemas.cv import CVProfile, JobMatchResult

# Initialize the Gemini Client. 
# It will automatically pick up GEMINI_API_KEY from environment variables.
def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    return genai.Client(api_key=api_key)

def generate_content_with_fallback(client: genai.Client, contents: str, config: Any) -> Any:
    """Helper to try generating content with a chain of fallback models."""
    models = [
        os.getenv("GEMINI_MODEL", "gemma-4-31b-it"),
        os.getenv("GEMINI_MODEL_FALLBACK_1", "gemma-4-26b-a4b-it"),
        os.getenv("GEMINI_MODEL_FALLBACK_2", "gemini-3.1-flash-lite"),
    ]
    
    last_error = None
    for model_name in models:
        if not model_name:
            continue
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            return response
        except Exception as e:
            print(f"Model {model_name} failed: {e}. Trying next fallback...")
            last_error = e
            continue
            
    raise last_error if last_error else ValueError("No Gemini models configured in fallback chain.")

def parse_cv_with_gemma(cv_text: str) -> CVProfile:
    """Parse raw CV text using Gemini structured outputs to return CVProfile."""
    client = get_client()
    
    prompt = f"""
    Extract the professional profile from this CV text.
    Analyze the candidate's skills, experience, and target roles.
    Also generate an optimized search query string to find jobs for this profile.
    The query should be brief, target roles, and optionally add 'remote' or specific top technologies if relevant (e.g. 'React developer junior remote').
    
    CV Text:
    {cv_text}
    """
    
    response = generate_content_with_fallback(
        client=client,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CVProfile,
            temperature=0.1,
        )
    )
    
    if response.parsed:
        return response.parsed
    
    # Fallback to manual parsing
    try:
        data = json.loads(response.text)
        return CVProfile(**data)
    except Exception as e:
        raise ValueError(f"Failed to parse CV with Gemini: {str(e)}. Response was: {response.text}")

def evaluate_job_match(cv_profile: CVProfile, job_title: str, job_company: str, job_description: str) -> JobMatchResult:
    """Evaluate job affinity to return a match score and quick apply tip."""
    client = get_client()
    
    prompt = f"""
    Compare the following candidate profile with the job details to calculate a match score (1 to 10) and write a short, highly personalized recommendation/tip (1-2 sentences) on how this candidate can apply to stand out.
    
    Candidate Profile:
    - Skills: {', '.join(cv_profile.skills)}
    - Experience Summary: {cv_profile.experience_summary}
    - Target Roles: {', '.join(cv_profile.target_roles)}
    
    Job Details:
    - Title: {job_title}
    - Company: {job_company}
    - Description/Details: {job_description}
    """
    
    response = generate_content_with_fallback(
        client=client,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=JobMatchResult,
            temperature=0.2,
        )
    )
    
    if response.parsed:
        return response.parsed
        
    try:
        data = json.loads(response.text)
        return JobMatchResult(**data)
    except Exception as e:
        raise ValueError(f"Failed to evaluate job match with Gemini: {str(e)}")

def generate_chat_response(prompt: str) -> str:
    """Generate advisor chat response using the model fallback chain."""
    client = get_client()
    response = generate_content_with_fallback(
        client=client,
        contents=prompt,
        config=None
    )
    return response.text
