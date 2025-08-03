from pydantic import BaseModel, Field
from typing import  Any, Optional, List, Dict
from datetime import datetime

class ApiResponse(BaseModel):
    status_code: int
    message: str
    data: Any

class ConversationCreate(BaseModel):
    email: str = Field(..., example="user@example.com", description="User's email address")

class MessageCreate(BaseModel):
    conversation_id: str = Field(..., example="507f1f77bcf86cd799439011", description="MongoDB ObjectId of the conversation")
    user_message: str = Field(..., example="I have intermediate Excel skills and work with data analysis", description="User's message for Excel interview")

# New models for interactive interview
class InterviewStepCreate(BaseModel):
    conversation_id: str = Field(..., example="507f1f77bcf86cd799439011", description="MongoDB ObjectId of the conversation")
    user_response: str = Field(..., example="I would use Excel's Remove Duplicates feature", description="User's response to the current question")
    current_step: str = Field(..., example="theory", description="Current interview step: intro, theory, practical, advanced")

class InterviewStepResponse(BaseModel):
    conversation_id: str = Field(..., example="507f1f77bcf86cd799439011", description="MongoDB ObjectId of the conversation")
    current_step: str = Field(..., example="theory", description="Current interview step")
    question: str = Field(..., example="How would you handle duplicate data?", description="Current question being asked")
    previous_response: Optional[str] = Field(None, example="I would use Remove Duplicates", description="User's previous response")
    evaluation: Optional[Dict[str, Any]] = Field(None, description="Evaluation of previous response")
    is_complete: bool = Field(..., example=False, description="Whether the interview is complete")
    next_step: Optional[str] = Field(None, example="practical", description="Next step in the interview")

class InterviewState(BaseModel):
    conversation_id: str
    current_step: str
    completed_steps: List[str]
    responses: Dict[str, str]
    evaluations: Dict[str, Dict[str, Any]]
    overall_score: Optional[float] = None
    is_complete: bool = False

class PropensityScore(BaseModel):
    """Represents the Excel skill score with visual indicator"""
    score: float = Field(..., ge=0, le=10, example=7.0, description="Excel skill score from 0-10")
    rationale: str = Field(..., example="Based on comprehensive Excel skill assessment covering theoretical knowledge, practical application, and advanced features", description="Explanation for the score")
    visual_indicator: str = Field(..., example="🟡 Good", description="Visual indicator: 🟢 Excellent, 🟡 Good, 🟠 Satisfactory, 🔴 Needs Improvement")

class CleanBusinessReportResponse(BaseModel):
    """Clean Excel interview response structure that excludes null fields"""
    company_name: str = Field(..., example="Excel Interview - John Doe (Intermediate)", description="Interview identifier with candidate name and level")
    report_date: datetime = Field(..., example="2025-07-08T05:13:25Z", description="Timestamp of the interview")
    propensity_score: PropensityScore = Field(..., description="Excel skill score with detailed assessment")
    overall_summary: str = Field(..., example="Candidate demonstrated strong Excel skills...", description="Overall interview summary and feedback")
    
    class Config:
        # Exclude fields that are None
        exclude_none = True

class MessageResponse(BaseModel):
    conversation_id: str = Field(..., example="507f1f77bcf86cd799439011", description="MongoDB ObjectId of the conversation")
    response: str = Field(..., example="Analysis completed...", description="Response content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, example="2025-07-08T05:13:25Z", description="Response timestamp")

class ConversationResponse(BaseModel):
    conversation_id: str = Field(..., example="507f1f77bcf86cd799439011", description="MongoDB ObjectId of the conversation")
    email: str = Field(..., example="user@example.com", description="User's email address")
    created_at: datetime = Field(default_factory=datetime.utcnow, example="2025-07-08T05:13:25Z", description="Conversation creation timestamp")
    status: str = Field(default="active", example="active", description="Conversation status")


