from pydantic import BaseModel, Field
from typing import List

class CandidateAnalysis(BaseModel):
    candidate_name: str
    ats_match_score: int = Field(ge=0, le=100)
    strengths: List[str]
    red_flags: List[str]
    interview_questions: List[str]

class BatchAnalysisResponse(BaseModel):
    job_description: str
    results: List[CandidateAnalysis]

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str


    