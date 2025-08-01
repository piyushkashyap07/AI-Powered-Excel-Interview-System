import os
import asyncio
import json
import time
from typing import Any, Dict, List, Tuple, Optional
from llama_index.core.workflow import Workflow, step, Context, StartEvent, StopEvent, Event
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import FunctionAgent
import dotenv
from app.prompts.excel_interview_intro_prompt import get_excel_interview_intro_prompt
from app.prompts.excel_theory_prompt import get_excel_theory_prompt
from app.prompts.excel_practical_prompt import get_excel_practical_prompt
from app.prompts.excel_advanced_prompt import get_excel_advanced_prompt
from app.prompts.excel_evaluator_prompt import get_excel_evaluator_prompt
from datetime import datetime
import logging

# Load environment variables
dotenv.load_dotenv()



logger = logging.getLogger(__name__)



# Event stubs for Excel Interview workflow
class InterviewStartEvent(Event):
    user_query: str
    candidate_name: Optional[str] = None
    experience_level: Optional[str] = None

class IntroductionEvent(Event):
    user_query: str
    candidate_response: str

class TheoryQuestionEvent(Event):
    user_query: str
    candidate_response: str
    question_number: int

class PracticalQuestionEvent(Event):
    user_query: str
    candidate_response: str
    question_number: int

class AdvancedQuestionEvent(Event):
    user_query: str
    candidate_response: str
    question_number: int

class EvaluationEvent(Event):
    all_responses: Dict[str, Any]
    skill_areas: List[str]

class InterviewCompleteEvent(Event):
    evaluation_results: Dict[str, Any]
    final_feedback: str

# Configuration and initialization
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI LLM
llm = OpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

def extract_candidate_info(user_query: str) -> Tuple[str, str]:
    """
    Extract candidate name and experience level from user query.
    """
    # Simple extraction - can be enhanced with more sophisticated parsing
    experience_levels = ["basic", "intermediate", "advanced", "beginner", "expert"]
    
    query_lower = user_query.lower()
    level = "intermediate"  # default
    
    for exp_level in experience_levels:
        if exp_level in query_lower:
            level = exp_level
            break
    
    # Extract name if provided (simple pattern matching)
    name = None
    if "name" in query_lower or "i'm" in query_lower or "i am" in query_lower:
        # Basic name extraction - can be enhanced
        name = "Candidate"
    
    return name, level

class ExcelInterviewWorkflow(Workflow):
    """
    Excel Interview Workflow using LlamaIndex multi-agent system.
    Conducts a comprehensive Excel technical interview with evaluation.
    """
    

    
    @step(pass_context=True)
    async def start_interview(self, ctx: Context, ev: StartEvent) -> InterviewStartEvent:
        """
        Initialize the interview and extract candidate information.
        """
        user_query = ev.user_query
        
        # Extract candidate information
        candidate_name, experience_level = extract_candidate_info(user_query)
        
        # Store in context for use throughout the interview
        ctx.interview_data = {
            "candidate_name": candidate_name,
            "experience_level": experience_level,
            "responses": [],
            "current_question": 1,
            "total_questions": 6  # 2 theory + 2 practical + 2 advanced
        }
        
        logger.info(f"Starting Excel interview for {candidate_name} (Level: {experience_level})")
        
        return InterviewStartEvent(
            user_query=user_query,
            candidate_name=candidate_name,
            experience_level=experience_level
        )
    
    @step(pass_context=True)
    async def introduction_agent(self, ctx: Context, ev: InterviewStartEvent) -> IntroductionEvent:
        """
        Conduct the interview introduction and first question.
        """
        intro_prompt = get_excel_interview_intro_prompt()
        
        # Create introduction message
        intro_message = f"""
        Welcome to your Excel technical interview! 
        
        Based on your profile, I'll be assessing your {ev.experience_level} level Excel skills.
        This interview will cover theoretical knowledge, practical application, and advanced features.
        
        Let's begin with understanding your Excel experience better.
        """
        
        # Generate introduction using LLM
        response = await llm.complete(
            f"{intro_prompt}\n\nCandidate Level: {ev.experience_level}\n\nGenerate a welcoming introduction and first question:"
        )
        
        return IntroductionEvent(
            user_query=ev.user_query,
            candidate_response=response.text
        )
    
    @step(pass_context=True)
    async def theory_question_agent(self, ctx: Context, ev: IntroductionEvent) -> TheoryQuestionEvent:
        """
        Ask theory-based Excel questions.
        """
        theory_prompt = get_excel_theory_prompt()
        
        # Generate theory question based on experience level
        question = await llm.complete(
            f"{theory_prompt}\n\nExperience Level: {ctx.interview_data['experience_level']}\n\nGenerate a theory question appropriate for this level:"
        )
        
        return TheoryQuestionEvent(
            user_query=ev.user_query,
            candidate_response=ev.candidate_response,
            question_number=ctx.interview_data['current_question']
        )
    
    @step(pass_context=True)
    async def practical_question_agent(self, ctx: Context, ev: TheoryQuestionEvent) -> PracticalQuestionEvent:
        """
        Ask practical Excel scenario questions.
        """
        practical_prompt = get_excel_practical_prompt()
        
        # Generate practical question
        question = await llm.complete(
            f"{practical_prompt}\n\nExperience Level: {ctx.interview_data['experience_level']}\n\nGenerate a practical scenario question:"
        )
        
        return PracticalQuestionEvent(
            user_query=ev.user_query,
            candidate_response=ev.candidate_response,
            question_number=ctx.interview_data['current_question'] + 1
        )
    
    @step(pass_context=True)
    async def advanced_question_agent(self, ctx: Context, ev: PracticalQuestionEvent) -> AdvancedQuestionEvent:
        """
        Ask advanced Excel feature questions.
        """
        advanced_prompt = get_excel_advanced_prompt()
        
        # Generate advanced question
        question = await llm.complete(
            f"{advanced_prompt}\n\nExperience Level: {ctx.interview_data['experience_level']}\n\nGenerate an advanced Excel question:"
        )
        
        return AdvancedQuestionEvent(
            user_query=ev.user_query,
            candidate_response=ev.candidate_response,
            question_number=ctx.interview_data['current_question'] + 2
        )
    
    @step(pass_context=True)
    async def evaluation_agent(self, ctx: Context, ev: AdvancedQuestionEvent) -> EvaluationEvent:
        """
        Evaluate all candidate responses and generate comprehensive feedback.
        """
        evaluator_prompt = get_excel_evaluator_prompt()
        
        # Compile all responses for evaluation
        all_responses = {
            "theory_responses": ctx.interview_data.get('theory_responses', []),
            "practical_responses": ctx.interview_data.get('practical_responses', []),
            "advanced_responses": ctx.interview_data.get('advanced_responses', []),
            "experience_level": ctx.interview_data['experience_level']
        }
        
        # Generate evaluation
        evaluation = await llm.complete(
            f"{evaluator_prompt}\n\nCandidate Responses: {json.dumps(all_responses, indent=2)}\n\nGenerate comprehensive evaluation:"
        )
        
        return EvaluationEvent(
            all_responses=all_responses,
            skill_areas=["theoretical_knowledge", "practical_application", "advanced_skills", "communication_problem_solving"]
        )
    
    @step(pass_context=True)
    async def final_feedback_agent(self, ctx: Context, ev: EvaluationEvent) -> InterviewCompleteEvent:
        """
        Generate final interview summary and recommendations.
        """
        try:
            # Parse evaluation results
            evaluation_data = json.loads(ev.all_responses.get('evaluation', '{}'))
            
            # Generate final summary
            summary = f"""
            INTERVIEW COMPLETE
            
            Overall Score: {evaluation_data.get('overall_score', 'N/A')}/10
            
            Summary: {evaluation_data.get('summary', 'Evaluation completed')}
            
            Key Recommendations:
            {chr(10).join(evaluation_data.get('recommendations', ['No specific recommendations']))}
            
            Learning Resources:
            {chr(10).join(evaluation_data.get('learning_resources', ['No specific resources provided']))}
            """
            
            return InterviewCompleteEvent(
                evaluation_results=evaluation_data,
                final_feedback=summary
            )
            
        except Exception as e:
            logger.error(f"Error in final feedback: {e}")
            return InterviewCompleteEvent(
                evaluation_results={},
                final_feedback="Interview completed. Evaluation results will be provided separately."
            )
    
    @step
    async def end_interview(self, ctx: Context, ev: InterviewCompleteEvent) -> StopEvent:
        """
        End the interview and return final results.
        """
        logger.info("Excel interview completed successfully")
        
        return StopEvent(
            result={
                "interview_complete": True,
                "evaluation": ev.evaluation_results,
                "feedback": ev.final_feedback,
                "candidate_info": {
                    "name": ctx.interview_data.get('candidate_name'),
                    "experience_level": ctx.interview_data.get('experience_level')
                }
            }
        )

async def run_excel_interview_workflow(user_query: str, user_id: str, message_id: str):
    """
    Run the complete Excel interview workflow.
    
    Args:
        user_query: Initial user query containing candidate information
        user_id: Unique identifier for the user
        message_id: Unique identifier for the message
    
    Returns:
        Workflow result containing interview evaluation and feedback
    """
    try:
        # Create workflow instance
        workflow = ExcelInterviewWorkflow()
        
        # Run the workflow
        result = await workflow.run(
            StartEvent(user_query=user_query),
            user_id=user_id,
            message_id=message_id
        )
        
        logger.info(f"Excel interview workflow completed for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in Excel interview workflow: {e}")
        return {
            "error": str(e),
            "interview_complete": False,
            "feedback": "An error occurred during the interview. Please try again."
        } 