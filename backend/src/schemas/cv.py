from pydantic import BaseModel, Field
from typing import List, Optional

class CVProfile(BaseModel):
    name: Optional[str] = Field(default=None, description="Full name of the candidate")
    email: Optional[str] = Field(default=None, description="Email address of the candidate")
    skills: List[str] = Field(default_factory=list, description="Core technical and soft skills")
    experience_summary: str = Field(..., description="Concise summary of candidate's professional experience")
    target_roles: List[str] = Field(..., description="Target job titles")
    search_query: str = Field(..., description="Optimized query string for scraping job vacancies, e.g., 'React Developer remote'")
    location: Optional[str] = Field(default=None, description="Current location of the candidate (e.g. 'Spain' or 'Madrid, Spain')")

class JobMatchResult(BaseModel):
    match_score: int = Field(..., description="Affinity score from 1 to 10 based on CV matching")
    explanation: str = Field(..., description="Quick, actionable advice/tip for applying to this specific job")

class JobDetail(BaseModel):
    title: str = Field(..., description="Title of the job position")
    company: str = Field(..., description="Company name offering the job")
    location: str = Field(..., description="Location of the job (remote/city/country)")
    link: str = Field(..., description="Direct URL to the job posting")
    description: Optional[str] = Field(default=None, description="Short snippet of the job description")
    match_score: Optional[int] = Field(default=None, description="Calculated match score (1-10)")
    apply_tip: Optional[str] = Field(default=None, description="Actionable application advice from the AI")
    saved_to_notion: bool = Field(default=False, description="Whether the job has been saved to Notion")

class CVProcessResponse(BaseModel):
    profile: CVProfile = Field(..., description="Parsed professional profile from CV")
    jobs: List[JobDetail] = Field(default_factory=list, description="Found jobs with match analysis")
