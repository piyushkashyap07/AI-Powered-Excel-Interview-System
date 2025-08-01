# The corrected code:
import logging
from app.services.conversation_service import conversation_service
from app.workflows.Excel_Interview_workflow import run_excel_interview_workflow
import pytz
from datetime import datetime
from app.models.schema import (
    ApiResponse,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    CleanBusinessReportResponse,
    PropensityScore
)
from fastapi import APIRouter

# Configure logger
logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/server-check")
def health_check():
    try:
        # Get current time in IST
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Server check endpoint hit at {current_time}")

        return ApiResponse(
            status_code=200,
            message="Server check successful. Welcome to AI Excel Interview System!",
            data={
                "serverName": "AI Excel Interview System",
                "timestamp": current_time
            }
        )

    except Exception as e:
        print(e)
        logger.error(f"An ERROR occurred in the Server check: {e}")
        return ApiResponse(
            status_code=500,
            message="Server check failed.",
            data={}
        )


@router.post("/", response_model=ConversationResponse)
async def create_conversation(conversation_data: ConversationCreate):
    """
    Create a new conversation
    Takes a user's email and creates a new conversation with a unique ID.
    """
    logger.info("Create conversations endpoint accessed !")
    try:
        result = conversation_service.create_conversation(conversation_data.email)
        response = ConversationResponse(
            conversation_id=result["conversation_id"],
            email=result["email"],
            created_at=result["created_at"],
            status=result["status"]
        )
        logger.info(f"API logs fetched successfully. Response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise




@router.get("/get_conversations")
async def get_conversation_history():
    logger.info("Get conversation history endpoint accessed !")
    try:
        conversations = conversation_service.get_all_conversations()
        response = ApiResponse(
            status_code=200,
            message="Conversations retrieved successfully",
            data=conversations
        )
        logger.info(f"API logs fetched successfully. Response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return ApiResponse(
            status_code=500,
            message="Error retrieving conversations",
            data=[]
        )


@router.post("/excel-interview", response_model=CleanBusinessReportResponse)
async def start_excel_interview(message_data: MessageCreate):
    """
    Start an Excel technical interview
    Takes a conversation ID and user message, returns interview results.
    
    Returns a comprehensive Excel skill assessment including:
    - Theoretical knowledge evaluation
    - Practical application assessment
    - Advanced skills evaluation
    - Overall score and recommendations
    """
    logger.info("Excel interview endpoint accessed !")
    try:
        # Use the conversation service to handle the interview
        result = await conversation_service.start_excel_interview(
            message_data.conversation_id, 
            message_data.user_message
        )
        
        # Extract data from result
        response_text = result.get("response", "Interview completed")
        evaluation = result.get("evaluation", {})
        candidate_info = result.get("candidate_info", {})
        timestamp = result.get("timestamp", datetime.utcnow())
        
        # Extract overall score from evaluation
        overall_score = evaluation.get('overall_score', 7) if evaluation else 7
        
        # Determine visual indicator based on score
        if overall_score >= 8:
            visual_indicator = "🟢 Excellent"
        elif overall_score >= 6:
            visual_indicator = "🟡 Good"
        elif overall_score >= 4:
            visual_indicator = "🟠 Satisfactory"
        else:
            visual_indicator = "🔴 Needs Improvement"
        
        candidate_name = candidate_info.get('name', 'Candidate') if candidate_info else 'Candidate'
        experience_level = candidate_info.get('experience_level', 'Intermediate') if candidate_info else 'Intermediate'
        
        return CleanBusinessReportResponse(
            company_name=f"Excel Interview - {candidate_name} ({experience_level})",
            report_date=timestamp,
            propensity_score=PropensityScore(
                score=overall_score,
                rationale=f"Based on comprehensive Excel skill assessment covering theoretical knowledge, practical application, and advanced features",
                visual_indicator=visual_indicator
            ),
            overall_summary=response_text
        )
        
    except Exception as e:
        logger.error(f"Error in Excel interview endpoint: {e}")
        return CleanBusinessReportResponse(
            company_name="Excel Interview - Error",
            report_date=datetime.utcnow(),
            propensity_score=PropensityScore(
                score=0,
                rationale="Error occurred during interview",
                visual_indicator="🔴 Error"
            ),
            overall_summary=f"Error: {str(e)}"
        )
