from pydantic import BaseModel, Field

from typing import Dict, List, Any, Optional

class ExperienceEntry(BaseModel):
    job_title: str = Field(..., description="The job title, e.g., 'Software Engineer'")
    company: str = Field(..., description="The company name, e.g., 'ABC Corp'")
    start_date: str = Field(..., description="The start date in format DD/MM/YYYY or Month YYYY")
    end_date: Optional[str] = Field(None, description="The end date if available, otherwise 'Present'")

class EducationEntry(BaseModel):
    degree: str = Field(..., description="The degree, e.g., 'B.Tech in Computer Science'")
    institution: str = Field(..., description="The institution name, e.g., 'XYZ University'")
    start_date: Optional[str] = Field(None, description="The start date in format DD/MM/YYYY or Month YYYY")
    end_date: Optional[str] = Field(None, description="The end date if available, otherwise 'Present'")

class ResumeData(BaseModel):
    name: str
    email: str
    phone: str
    skills: List[str]
    education: List[EducationEntry]
    experience: List[ExperienceEntry]
    
class FraudIndicator(BaseModel):
    status: str
    reasoning: str
    flags: Optional[List[str]] = None  # accepts multiple flags if needed


class FraudReport(BaseModel):
    fraud_indicators: List[FraudIndicator] = Field(
        ..., description="List of fraud indicators with reasoning and flags"
    )
    plagiarism_summary: str = Field(
        ..., description="Summary message of plagiarism detection instead of raw matches"
    )
    resume_vs_jd_similarity: str = Field(
        ..., description="Conclusion about resume vs JD similarity"
    )
    education_anomalies: Optional[List[str]] = Field(
        default=None, description="Any anomalies in education"
    )
    final_recommendation: str = Field(
        ..., description="Short final recommendation"
    )
