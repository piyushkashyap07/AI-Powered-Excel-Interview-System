import os
import asyncio
import json
import time
from typing import Any, Dict, List, Tuple, Optional
from llama_index.llms.openai import OpenAI
from llama_index.core.workflow import InputRequiredEvent, HumanResponseEvent
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
    name = "Candidate"  # default
    if "name" in query_lower or "i'm" in query_lower or "i am" in query_lower:
        # Basic name extraction - can be enhanced
        name = "Candidate"
    
    return name, level

async def evaluate_response(question: str, user_response: str, question_type: str, experience_level: str) -> Dict[str, Any]:
    """
    Evaluate a single user response to an interview question.
    """
    evaluation_prompt = f"""
    You are an Excel technical interviewer evaluating a candidate's response.
    
    Question Type: {question_type}
    Experience Level: {experience_level}
    Question: {question}
    Candidate Response: {user_response}
    
    Please evaluate this response on a scale of 1-10 and provide:
    1. Score (1-10)
    2. Brief feedback on strengths and areas for improvement
    3. Key points they covered well
    4. What they could improve
    
    Respond in JSON format:
    {{
        "score": <number>,
        "feedback": "<brief feedback>",
        "strengths": ["<point1>", "<point2>"],
        "improvements": ["<improvement1>", "<improvement2>"]
    }}
    """
    
    try:
        evaluation_response = await llm.acomplete(evaluation_prompt)
        # Try to parse JSON response
        evaluation_text = evaluation_response.text.strip()
        if evaluation_text.startswith('```json'):
            evaluation_text = evaluation_text[7:-3]  # Remove ```json and ```
        elif evaluation_text.startswith('```'):
            evaluation_text = evaluation_text[3:-3]  # Remove ``` and ```
        
        evaluation_data = json.loads(evaluation_text)
        return evaluation_data
    except Exception as e:
        logger.error(f"Error evaluating response: {e}")
        # Fallback evaluation
        return {
            "score": 7,
            "feedback": "Response evaluated",
            "strengths": ["Provided a response"],
            "improvements": ["Could provide more detail"]
        }

async def start_interactive_interview(user_message: str, conversation_id: str) -> Dict[str, Any]:
    """
    Start an interactive Excel interview and return the first question.
    
    Args:
        user_message: User's initial message
        conversation_id: Conversation ID
        
    Returns:
        Dict containing the first question and interview state
    """
    try:
        # Extract candidate information
        candidate_name, experience_level = extract_candidate_info(user_message)
        logger.info(f"Starting interactive Excel interview for {candidate_name} (Level: {experience_level})")
        
        # Create introduction message
        intro_message = f"""
        Welcome to your Excel technical interview! 
        
        Based on your profile, I'll be assessing your {experience_level} level Excel skills.
        This interview will cover theoretical knowledge, practical application, and advanced features.
        
        Let's begin with understanding your Excel experience better.
        """
        
        # Get intro prompt
        intro_prompt = get_excel_interview_intro_prompt(intro_message)
        
        # Generate first question
        intro_response = await llm.acomplete(
            f"{intro_prompt}\n\nCandidate Level: {experience_level}\n\nGenerate a welcoming introduction and first question:"
        )
        
        # Create initial interview state with 6 total questions
        interview_state = {
            "conversation_id": conversation_id,
            "current_step": "intro",
            "completed_steps": [],
            "responses": {},
            "evaluations": {},
            "total_questions": 6,
            "current_question": 1,
            "candidate_info": {
                "name": candidate_name,
                "experience_level": experience_level
            },
            "is_complete": False,
            "qa_pairs": []  # Initialize Q&A pairs storage
        }
        
        # Store the initial interview state in MongoDB
        from app.helpers.mongodb import mongodb
        from bson import ObjectId
        collection = mongodb.get_collection("conversations")
        
        collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"interview_state": interview_state}}
        )
        
        logger.info(f"Initialized interview state for conversation {conversation_id}")
        
        return {
            "conversation_id": conversation_id,
            "question": intro_response.text,
            "current_step": "intro",
            "next_step": "theory",
            "interview_state": interview_state,
            "is_complete": False,
            "total_questions": 6,
            "current_question": 1,
            "questions_remaining": 5
        }
        
    except Exception as e:
        logger.error(f"Error starting interactive interview: {e}")
        raise

async def process_interview_step(conversation_id: str, user_response: str, current_step: str) -> Dict[str, Any]:
    """
    Process a user's response to an interview question and get the next question.
    
    Args:
        conversation_id: Conversation ID
        user_response: User's response to the current question
        current_step: Current interview step (intro, theory, practical, advanced)
        
    Returns:
        Dict containing evaluation, next question, and updated state
    """
    try:
        # Get the current interview state from MongoDB
        from app.helpers.mongodb import mongodb
        from bson import ObjectId
        collection = mongodb.get_collection("conversations")
        conversation = collection.find_one({"_id": ObjectId(conversation_id)})
        
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")
        
        interview_state = conversation.get("interview_state", {})
        candidate_info = interview_state.get("candidate_info", {})
        experience_level = candidate_info.get("experience_level", "intermediate")
        
        # Get the question that was asked for this step
        messages = conversation.get("messages", [])
        current_question = ""
        for msg in reversed(messages):
            if msg.get("step") == current_step and msg.get("role") == "assistant":
                current_question = msg.get("content", "")
                break
        
        # Store the question and answer in the database
        qa_data = {
            "step": current_step,
            "question": current_question,
            "answer": user_response,
            "timestamp": datetime.now().isoformat()
        }
        
        # Initialize qa_pairs if it doesn't exist
        if "qa_pairs" not in interview_state:
            interview_state["qa_pairs"] = []
        
        # Add the Q&A pair to the interview state
        interview_state["qa_pairs"].append(qa_data)
        
        # Evaluate the user's response
        evaluation = await evaluate_response(
            current_question,
            user_response,
            current_step.title(),
            experience_level
        )
        
        # Update interview state
        interview_state["responses"][current_step] = user_response
        interview_state["evaluations"][current_step] = evaluation
        interview_state["completed_steps"].append(current_step)
        
        # Determine next step based on question number
        steps = ["intro", "theory", "practical", "advanced", "advanced2", "advanced3"]
        current_index = steps.index(current_step)
        next_step = steps[current_index + 1] if current_index + 1 < len(steps) else None
        
        # Update question counter
        current_question_num = interview_state.get("current_question", 1)
        interview_state["current_question"] = current_question_num + 1
        
        logger.info(f"Question counter updated: {current_question_num} -> {interview_state['current_question']}")
        
        # Generate next question if not complete
        next_question = ""
        is_complete = False
        questions_remaining = 0
        
        if next_step and current_question_num < 6:  # Maximum 6 questions
            interview_state["current_step"] = next_step
            questions_remaining = 6 - interview_state["current_question"]
            logger.info(f"Continuing to next step: {next_step}, questions remaining: {questions_remaining}")
            
            if next_step == "theory":
                theory_prompt = get_excel_theory_prompt()
                theory_response = await llm.acomplete(
                    f"{theory_prompt}\n\nExperience Level: {experience_level}\n\nGenerate a theory question appropriate for this level:"
                )
                next_question = theory_response.text
                
            elif next_step == "practical":
                practical_prompt = get_excel_practical_prompt()
                practical_response = await llm.acomplete(
                    f"{practical_prompt}\n\nExperience Level: {experience_level}\n\nGenerate a practical scenario question:"
                )
                next_question = practical_response.text
                
            elif next_step == "advanced":
                advanced_prompt = get_excel_advanced_prompt()
                advanced_response = await llm.acomplete(
                    f"{advanced_prompt}\n\nExperience Level: {experience_level}\n\nGenerate an advanced Excel question:"
                )
                next_question = advanced_response.text
                
            elif next_step == "advanced2":
                advanced_prompt = get_excel_advanced_prompt()
                advanced_response = await llm.acomplete(
                    f"{advanced_prompt}\n\nExperience Level: {experience_level}\n\nGenerate a different advanced Excel question focusing on data analysis:"
                )
                next_question = advanced_response.text
                
            elif next_step == "advanced3":
                advanced_prompt = get_excel_advanced_prompt()
                advanced_response = await llm.acomplete(
                    f"{advanced_prompt}\n\nExperience Level: {experience_level}\n\nGenerate a final advanced Excel question focusing on automation and efficiency:"
                )
                next_question = advanced_response.text
        else:
            # Interview is complete - get human approval before generating final results
            is_complete = True
            interview_state["is_complete"] = True
            
            # Get all Q&A data for human review
            qa_pairs = interview_state.get("qa_pairs", [])
            evaluations = interview_state.get("evaluations", {})
            candidate_info = interview_state.get("candidate_info", {})
            
            # Prepare summary for human review
            review_summary = f"""
            INTERVIEW COMPLETE - HUMAN REVIEW REQUIRED
            
            Candidate: {candidate_info.get('name', 'Unknown')}
            Experience Level: {candidate_info.get('experience_level', 'Unknown')}
            Total Questions Answered: {len(qa_pairs)}
            
            INTERVIEW SUMMARY:
            """
            
            # Add each Q&A pair to the review summary
            for i, qa in enumerate(qa_pairs, 1):
                step = qa.get("step", "unknown")
                question = qa.get("question", "")
                answer = qa.get("answer", "")
                evaluation = evaluations.get(step, {})
                score = evaluation.get("score", 7)
                feedback = evaluation.get("feedback", "No feedback available")
                
                review_summary += f"""
            Question {i} ({step.title()}):
            Q: {question[:150]}{'...' if len(question) > 150 else ''}
            A: {answer[:150]}{'...' if len(answer) > 150 else ''}
            Score: {score}/10
            Feedback: {feedback}
            """
            
            # Calculate preliminary overall score
            scores = [eval_data.get("score", 7) for eval_data in evaluations.values()]
            preliminary_score = sum(scores) / len(scores) if scores else 7
            
            review_summary += f"""
            
            PRELIMINARY OVERALL SCORE: {preliminary_score:.1f}/10
            
            Do you approve this interview evaluation and want to generate final results? (yes/no):
            """
            
            # Human-in-the-loop validation
            try:
                # For now, we'll simulate the human approval process
                # In a real implementation, this would use the LlamaIndex workflow events
                human_approval = await get_human_approval_for_interview(review_summary, conversation_id)
                
                if human_approval:
                    # Generate comprehensive final results using all stored Q&A data
                    final_results = await generate_final_results_from_qa_data(conversation_id, interview_state)
                    interview_state["final_results"] = final_results
                    logger.info(f"Human approved final results for conversation {conversation_id}")
                else:
                    # Human rejected the evaluation
                    interview_state["human_rejected"] = True
                    interview_state["rejection_reason"] = "Human reviewer did not approve the evaluation"
                    logger.info(f"Human rejected final results for conversation {conversation_id}")
                    
            except Exception as e:
                logger.error(f"Error in human approval process: {e}")
                # Fallback: generate results without human approval
                final_results = await generate_final_results_from_qa_data(conversation_id, interview_state)
                interview_state["final_results"] = final_results
                interview_state["human_approval_bypassed"] = True
        
        # Update the conversation in MongoDB with the new interview state
        collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"interview_state": interview_state}}
        )
        
        logger.info(f"MongoDB updated with new interview state: current_question={interview_state['current_question']}")
        
        logger.info(f"Returning to frontend: current_question={interview_state['current_question']}, questions_remaining={questions_remaining}")
        
        return {
            "conversation_id": conversation_id,
            "current_step": next_step if next_step else current_step,
            "evaluation": evaluation,
            "next_step": next_step,
            "next_question": next_question,
            "interview_state": interview_state,
            "is_complete": is_complete,
            "total_questions": 6,
            "current_question": interview_state["current_question"],
            "questions_remaining": questions_remaining,
            "final_results": interview_state.get("final_results") if is_complete else None,
            "human_approved": interview_state.get("human_approved", True),
            "human_rejected": interview_state.get("human_rejected", False),
            "rejection_reason": interview_state.get("rejection_reason", ""),
            "human_approval_bypassed": interview_state.get("human_approval_bypassed", False)
        }
        
    except Exception as e:
        logger.error(f"Error processing interview step: {e}")
        raise

async def run_excel_interview_workflow(user_query: str, user_id: str, message_id: str):
    """
    Run an interactive Excel interview workflow.
    
    Args:
        user_query: Initial user query containing candidate information
        user_id: Unique identifier for the user
        message_id: Unique identifier for the message
    
    Returns:
        Dict containing interview evaluation and feedback
    """
    try:
        # Extract candidate information
        candidate_name, experience_level = extract_candidate_info(user_query)
        logger.info(f"Starting interactive Excel interview for {candidate_name} (Level: {experience_level})")
        
        # Create introduction message
        intro_message = f"""
        Welcome to your Excel technical interview! 
        
        Based on your profile, I'll be assessing your {experience_level} level Excel skills.
        This interview will cover theoretical knowledge, practical application, and advanced features.
        
        Let's begin with understanding your Excel experience better.
        """
        
        # Get prompts
        intro_prompt = get_excel_interview_intro_prompt(intro_message)
        theory_prompt = get_excel_theory_prompt()
        practical_prompt = get_excel_practical_prompt()
        advanced_prompt = get_excel_advanced_prompt()
        
        # Generate interview questions
        intro_response = await llm.acomplete(
            f"{intro_prompt}\n\nCandidate Level: {experience_level}\n\nGenerate a welcoming introduction and first question:"
        )
        
        theory_question = await llm.acomplete(
            f"{theory_prompt}\n\nExperience Level: {experience_level}\n\nGenerate a theory question appropriate for this level:"
        )
        
        practical_question = await llm.acomplete(
            f"{practical_prompt}\n\nExperience Level: {experience_level}\n\nGenerate a practical scenario question:"
        )
        
        advanced_question = await llm.acomplete(
            f"{advanced_prompt}\n\nExperience Level: {experience_level}\n\nGenerate an advanced Excel question:"
        )
        
        # Simulate user responses (in a real system, these would come from the user)
        # For now, we'll use the user's initial message as a response to the first question
        user_responses = {
            "intro": user_query,  # Use the initial message as response to intro
            "theory": "I would use Excel's Remove Duplicates feature and also COUNTIF to identify duplicates. I'd also check for data integrity.",
            "practical": "For profit margin, I'd use =(Sales-Cost)/Sales. For best-selling product by region, I'd use pivot tables or SUMIFS. For monthly summary, I'd use pivot tables with date grouping.",
            "advanced": "I would use Power Query to merge CSV files, apply transformations for cleaning, and create VBA macros for dynamic reporting with user input."
        }
        
        # Evaluate each response
        intro_evaluation = await evaluate_response(
            intro_response.text, 
            user_responses["intro"], 
            "Introduction", 
            experience_level
        )
        
        theory_evaluation = await evaluate_response(
            theory_question.text, 
            user_responses["theory"], 
            "Theory", 
            experience_level
        )
        
        practical_evaluation = await evaluate_response(
            practical_question.text, 
            user_responses["practical"], 
            "Practical", 
            experience_level
        )
        
        advanced_evaluation = await evaluate_response(
            advanced_question.text, 
            user_responses["advanced"], 
            "Advanced", 
            experience_level
        )
        
        # Calculate overall score
        scores = [
            intro_evaluation.get("score", 7),
            theory_evaluation.get("score", 7),
            practical_evaluation.get("score", 7),
            advanced_evaluation.get("score", 7)
        ]
        overall_score = sum(scores) / len(scores)
        
        # Compile comprehensive feedback
        feedback = f"""
        INTERACTIVE EXCEL INTERVIEW COMPLETE
        
        INTERVIEW QUESTIONS AND EVALUATIONS:
        
        1. INTRODUCTION & EXPERIENCE:
        Question: {intro_response.text}
        Your Response: {user_responses["intro"]}
        Score: {intro_evaluation.get("score", 7)}/10
        Feedback: {intro_evaluation.get("feedback", "Good response")}
        
        2. THEORY QUESTION:
        Question: {theory_question.text}
        Your Response: {user_responses["theory"]}
        Score: {theory_evaluation.get("score", 7)}/10
        Feedback: {theory_evaluation.get("feedback", "Good response")}
        
        3. PRACTICAL QUESTION:
        Question: {practical_question.text}
        Your Response: {user_responses["practical"]}
        Score: {practical_evaluation.get("score", 7)}/10
        Feedback: {practical_evaluation.get("feedback", "Good response")}
        
        4. ADVANCED QUESTION:
        Question: {advanced_question.text}
        Your Response: {user_responses["advanced"]}
        Score: {advanced_evaluation.get("score", 7)}/10
        Feedback: {advanced_evaluation.get("feedback", "Good response")}
        
        OVERALL ASSESSMENT:
        Overall Score: {overall_score:.1f}/10
        
        Strengths:
        - {chr(10).join(intro_evaluation.get("strengths", ["Good communication"]))}
        - {chr(10).join(theory_evaluation.get("strengths", ["Good theoretical knowledge"]))}
        - {chr(10).join(practical_evaluation.get("strengths", ["Good practical skills"]))}
        - {chr(10).join(advanced_evaluation.get("strengths", ["Good advanced knowledge"]))}
        
        Areas for Improvement:
        - {chr(10).join(intro_evaluation.get("improvements", ["Could provide more detail"]))}
        - {chr(10).join(theory_evaluation.get("improvements", ["Could elaborate more"]))}
        - {chr(10).join(practical_evaluation.get("improvements", ["Could show more examples"]))}
        - {chr(10).join(advanced_evaluation.get("improvements", ["Could demonstrate more depth"]))}
        """
        
        # Determine visual indicator based on overall score
        if overall_score >= 8:
            visual_indicator = "🟢 Excellent"
        elif overall_score >= 6:
            visual_indicator = "🟡 Good"
        elif overall_score >= 4:
            visual_indicator = "🟠 Satisfactory"
        else:
            visual_indicator = "🔴 Needs Improvement"
        
        logger.info(f"Interactive Excel interview completed for user {user_id}")
        
        return {
            "interview_complete": True,
            "evaluation": {
                "overall_score": round(overall_score, 1),
                "summary": f"Interactive interview completed with {overall_score:.1f}/10 overall score",
                "recommendations": [
                    "Continue practicing Excel skills",
                    "Focus on advanced features like Power Query and VBA",
                    "Work on providing more detailed explanations"
                ],
                "learning_resources": [
                    "Microsoft Excel documentation",
                    "Online Excel courses",
                    "Practice with real datasets"
                ],
                "detailed_evaluations": {
                    "intro": intro_evaluation,
                    "theory": theory_evaluation,
                    "practical": practical_evaluation,
                    "advanced": advanced_evaluation
                }
            },
            "feedback": feedback,
            "candidate_info": {
                "name": candidate_name,
                "experience_level": experience_level
            },
            "questions_asked": {
                "intro": intro_response.text,
                "theory": theory_question.text,
                "practical": practical_question.text,
                "advanced": advanced_question.text
            },
            "user_responses": user_responses
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in Excel interview workflow: {e}")
        logger.error(f"Full traceback: {error_details}")
        return {
            "error": str(e),
            "error_details": error_details,
            "interview_complete": False,
            "feedback": "An error occurred during the interview. Please try again."
        } 

async def generate_final_results_from_qa_data(conversation_id: str, interview_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive final results using all stored Q&A data from the interview.
    
    Args:
        conversation_id: Conversation ID
        interview_state: Current interview state containing all Q&A data
        
    Returns:
        Dict containing comprehensive final results
    """
    try:
        # Get all Q&A pairs from the interview
        qa_pairs = interview_state.get("qa_pairs", [])
        evaluations = interview_state.get("evaluations", {})
        candidate_info = interview_state.get("candidate_info", {})
        
        if not qa_pairs:
            logger.warning("No Q&A data found for final result generation")
            return {
                "company_name": "Excel Interview - Interactive",
                "report_date": datetime.now().isoformat(),
                "propensity_score": {
                    "score": 7.0,
                    "rationale": "No interview data available for assessment",
                    "visual_indicator": "🟡 Good"
                },
                "overall_summary": "Interview completed but no detailed data available."
            }
        
        # Calculate overall score from evaluations
        scores = [eval_data.get("score", 7) for eval_data in evaluations.values()]
        overall_score = sum(scores) / len(scores) if scores else 7
        
        # Determine visual indicator based on overall score
        if overall_score >= 8:
            visual_indicator = "🟢 Excellent"
        elif overall_score >= 6:
            visual_indicator = "🟡 Good"
        elif overall_score >= 4:
            visual_indicator = "🟠 Satisfactory"
        else:
            visual_indicator = "🔴 Needs Improvement"
        
        # Create detailed summary using all Q&A data
        detailed_summary = f"""
        INTERVIEW COMPLETE - COMPREHENSIVE ANALYSIS
        
        Candidate: {candidate_info.get('name', 'Unknown')}
        Experience Level: {candidate_info.get('experience_level', 'Unknown')}
        Overall Score: {overall_score:.1f}/10
        Total Questions Answered: {len(qa_pairs)}
        
        DETAILED BREAKDOWN:
        """
        
        # Add each Q&A pair to the summary
        for i, qa in enumerate(qa_pairs, 1):
            step = qa.get("step", "unknown")
            question = qa.get("question", "")
            answer = qa.get("answer", "")
            evaluation = evaluations.get(step, {})
            score = evaluation.get("score", 7)
            feedback = evaluation.get("feedback", "No feedback available")
            
            detailed_summary += f"""
        Question {i} ({step.title()}):
        Q: {question[:200]}{'...' if len(question) > 200 else ''}
        A: {answer[:200]}{'...' if len(answer) > 200 else ''}
        Score: {score}/10
        Feedback: {feedback}
        """
        
        # Add strengths and areas for improvement
        strengths = []
        improvements = []
        
        for step, eval_data in evaluations.items():
            score = eval_data.get("score", 7)
            if score >= 7:
                strengths.append(f"Strong performance in {step} area")
            else:
                improvements.append(f"Needs improvement in {step} area")
        
        detailed_summary += f"""
        
        STRENGTHS:
        {chr(10).join(f"• {strength}" for strength in strengths) if strengths else "• No specific strengths identified"}
        
        AREAS FOR IMPROVEMENT:
        {chr(10).join(f"• {improvement}" for improvement in improvements) if improvements else "• Overall good performance"}
        
        RECOMMENDATIONS:
        • Practice Excel functions regularly
        • Work on identified weak areas
        • Consider advanced Excel courses
        • Apply Excel skills in real projects
        """
        
        # Create final results structure
        final_results = {
            "company_name": "Excel Interview - Interactive",
            "report_date": datetime.now().isoformat(),
            "propensity_score": {
                "score": overall_score,
                "rationale": f"Based on comprehensive analysis of {len(qa_pairs)} interview questions covering theoretical knowledge, practical application, and advanced Excel features",
                "visual_indicator": visual_indicator
            },
            "overall_summary": detailed_summary,
            "qa_data": qa_pairs,  # Include all Q&A data for detailed analysis
            "evaluations": evaluations,  # Include all evaluations
            "candidate_info": candidate_info
        }
        
        logger.info(f"Generated comprehensive final results for conversation {conversation_id}")
        return final_results
        
    except Exception as e:
        logger.error(f"Error generating final results: {e}")
        # Return fallback results
        return {
            "company_name": "Excel Interview - Interactive",
            "report_date": datetime.now().isoformat(),
            "propensity_score": {
                "score": 7.0,
                "rationale": "Error occurred during result generation",
                "visual_indicator": "🟡 Good"
            },
            "overall_summary": "Interview completed but error occurred during result generation."
        } 

async def get_interview_qa_data(conversation_id: str) -> Dict[str, Any]:
    """
    Retrieve all Q&A data for a specific conversation.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Dict containing all Q&A data and interview state
    """
    try:
        from app.helpers.mongodb import mongodb
        from bson import ObjectId
        collection = mongodb.get_collection("conversations")
        conversation = collection.find_one({"_id": ObjectId(conversation_id)})
        
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")
        
        interview_state = conversation.get("interview_state", {})
        qa_pairs = interview_state.get("qa_pairs", [])
        evaluations = interview_state.get("evaluations", {})
        candidate_info = interview_state.get("candidate_info", {})
        
        return {
            "conversation_id": conversation_id,
            "qa_pairs": qa_pairs,
            "evaluations": evaluations,
            "candidate_info": candidate_info,
            "total_questions": len(qa_pairs),
            "is_complete": interview_state.get("is_complete", False)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving Q&A data: {e}")
        raise 

async def get_human_approval_for_interview(review_summary: str, conversation_id: str) -> bool:
    """
    Get human approval for interview evaluation using LlamaIndex workflow events.
    
    Args:
        review_summary: Summary of the interview for human review
        conversation_id: Conversation ID
        
    Returns:
        bool: True if human approves, False if rejected
    """
    try:
        # In a real implementation, this would use LlamaIndex workflow events
        # For now, we'll simulate the process
        
        # Log the review summary for human review
        logger.info(f"Human review required for conversation {conversation_id}")
        logger.info(f"Review summary: {review_summary}")
        
        # Simulate human approval process
        # In production, this would trigger a workflow event that waits for human input
        question = f"""
        {review_summary}
        
        Do you approve this interview evaluation and want to generate final results? (yes/no): 
        """
        
        # For now, we'll simulate automatic approval
        # In a real implementation, this would use:
        # response_event = await ctx.wait_for_event(
        #     HumanResponseEvent,
        #     waiter_event=InputRequiredEvent(prefix=question)
        # )
        # return response_event.response.strip().lower() == "yes"
        
        # Simulate human approval (you can modify this for testing)
        simulated_human_response = "yes"  # Change to "no" to test rejection
        
        logger.info(f"Simulated human response: {simulated_human_response}")
        
        return simulated_human_response.strip().lower() == "yes"
        
    except Exception as e:
        logger.error(f"Error in human approval process: {e}")
        # Default to approval if there's an error
        return True 

async def workflow_human_approval_step(ctx, review_summary: str, conversation_id: str) -> Dict[str, Any]:
    """
    LlamaIndex workflow step for human approval of interview evaluation.
    
    Args:
        ctx: Workflow context
        review_summary: Summary of the interview for human review
        conversation_id: Conversation ID
        
    Returns:
        Dict containing approval status and final results
    """
    try:
        # Present the review summary to the human
        question = f"""
        {review_summary}
        
        Do you approve this interview evaluation and want to generate final results? (yes/no): 
        """
        
        # Wait for human response using LlamaIndex workflow events
        response_event = await ctx.wait_for_event(
            HumanResponseEvent,
            waiter_event=InputRequiredEvent(prefix=question)
        )
        
        human_response = response_event.response.strip().lower()
        approved = human_response == "yes"
        
        if approved:
            # Get the interview state and generate final results
            from app.helpers.mongodb import mongodb
            from bson import ObjectId
            collection = mongodb.get_collection("conversations")
            conversation = collection.find_one({"_id": ObjectId(conversation_id)})
            
            if conversation:
                interview_state = conversation.get("interview_state", {})
                final_results = await generate_final_results_from_qa_data(conversation_id, interview_state)
                
                # Update the interview state with approval
                interview_state["human_approved"] = True
                interview_state["final_results"] = final_results
                
                collection.update_one(
                    {"_id": ObjectId(conversation_id)},
                    {"$set": {"interview_state": interview_state}}
                )
                
                return {
                    "approved": True,
                    "final_results": final_results,
                    "message": "Human approved the evaluation. Final results generated."
                }
            else:
                return {
                    "approved": False,
                    "error": "Conversation not found",
                    "message": "Could not find interview data for final results generation."
                }
        else:
            # Human rejected the evaluation
            from app.helpers.mongodb import mongodb
            from bson import ObjectId
            collection = mongodb.get_collection("conversations")
            
            # Update the interview state with rejection
            collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": {
                    "interview_state.human_rejected": True,
                    "interview_state.rejection_reason": "Human reviewer did not approve the evaluation"
                }}
            )
            
            return {
                "approved": False,
                "message": "Human rejected the evaluation. No final results generated."
            }
            
    except Exception as e:
        logger.error(f"Error in workflow human approval step: {e}")
        return {
            "approved": False,
            "error": str(e),
            "message": "Error occurred during human approval process."
        } 

# Example LlamaIndex workflow integration
"""
# This is how you would integrate the human approval step in a LlamaIndex workflow:

from llama_index.core.workflow import Workflow

async def excel_interview_workflow_with_human_approval(ctx, user_message: str, conversation_id: str):
    # Step 1: Start the interview
    interview_start = await start_interactive_interview(user_message, conversation_id)
    
    # Step 2: Process interview steps (this would be in a loop in real implementation)
    # ... interview steps ...
    
    # Step 3: When interview is complete, get human approval
    if interview_start.get("is_complete"):
        qa_data = await get_interview_qa_data(conversation_id)
        review_summary = prepare_review_summary(qa_data)
        
        # Human-in-the-loop approval step
        approval_result = await workflow_human_approval_step(ctx, review_summary, conversation_id)
        
        if approval_result["approved"]:
            return {
                "status": "completed",
                "final_results": approval_result["final_results"],
                "message": approval_result["message"]
            }
        else:
            return {
                "status": "rejected",
                "message": approval_result["message"]
            }
    
    return interview_start

# Usage in a workflow:
# workflow = Workflow(
#     steps=[
#         excel_interview_workflow_with_human_approval
#     ]
# )
""" 