import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from app.helpers.mongodb import mongodb
from app.workflows.Excel_Interview_workflow import run_excel_interview_workflow, start_interactive_interview, process_interview_step

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self):
        self.collection_name = "conversations"
    
    def create_conversation(self, email: str) -> Dict[str, Any]:
        """
        Create a new conversation
        
        Args:
            email: User's email address
            
        Returns:
            Dict containing conversation_id, email, and created_at
        """
        try:
            collection = mongodb.get_collection(self.collection_name)
            conversation_data = {
                "email": email,
                "created_at": datetime.utcnow(),
                "messages": [],
                "interview_type": "excel",
                "status": "active",
                "interview_state": {
                    "current_step": "intro",
                    "completed_steps": [],
                    "responses": {},
                    "evaluations": {},
                    "is_complete": False
                }
            }
            
            result = collection.insert_one(conversation_data)
            conversation_id = str(result.inserted_id)
            
            logger.info(f"Created new conversation: {conversation_id} for email: {email}")
            
            return {
                "conversation_id": conversation_id,
                "email": email,
                "created_at": conversation_data["created_at"],
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def start_interactive_interview(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """
        Start an interactive Excel interview
        
        Args:
            conversation_id: Conversation ID
            user_message: User's initial message
            
        Returns:
            Dict containing the first question and interview state
        """
        try:
            # Verify that the conversation exists
            collection = mongodb.get_collection(self.collection_name)
            conversation = collection.find_one({"_id": ObjectId(conversation_id)})
            
            if not conversation:
                raise ValueError(f"Conversation with ID {conversation_id} not found")
            
            # Start the interactive interview
            logger.info(f"Starting interactive Excel interview for conversation: {conversation_id}")
            interview_result = await start_interactive_interview(user_message, conversation_id)
            
            # Update conversation with interview state
            collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$set": {
                        "interview_state": interview_result["interview_state"],
                        "interview_started": True,
                        "started_at": datetime.utcnow()
                    },
                    "$push": {"messages": {
                        "role": "assistant",
                        "content": interview_result["question"],
                        "timestamp": datetime.utcnow(),
                        "step": "intro"
                    }}
                }
            )
            
            return interview_result
            
        except Exception as e:
            logger.error(f"Error starting interactive interview: {e}")
            raise
    
    async def process_interview_step(self, conversation_id: str, user_response: str, current_step: str) -> Dict[str, Any]:
        """
        Process a user's response to an interview question and get the next question
        
        Args:
            conversation_id: Conversation ID
            user_response: User's response to the current question
            current_step: Current interview step (intro, theory, practical, advanced)
            
        Returns:
            Dict containing evaluation, next question, and updated state
        """
        try:
            # Verify that the conversation exists
            collection = mongodb.get_collection(self.collection_name)
            conversation = collection.find_one({"_id": ObjectId(conversation_id)})
            
            if not conversation:
                raise ValueError(f"Conversation with ID {conversation_id} not found")
            
            # Process the interview step
            logger.info(f"Processing interview step {current_step} for conversation: {conversation_id}")
            step_result = await process_interview_step(conversation_id, user_response, current_step)
            
            # Update conversation with new state
            collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$set": {
                        "interview_state": step_result["interview_state"],
                        "last_updated": datetime.utcnow()
                    },
                    "$push": {"messages": {
                        "role": "user",
                        "content": user_response,
                        "timestamp": datetime.utcnow(),
                        "step": current_step
                    }}
                }
            )
            
            # If there's a next question, add it to messages
            if not step_result["is_complete"] and step_result.get("next_question"):
                collection.update_one(
                    {"_id": ObjectId(conversation_id)},
                    {"$push": {"messages": {
                        "role": "assistant",
                        "content": step_result["next_question"],
                        "timestamp": datetime.utcnow(),
                        "step": step_result["next_step"]
                    }}}
                )
            
            return step_result
            
        except Exception as e:
            logger.error(f"Error processing interview step: {e}")
            raise
    
    async def start_excel_interview(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """
        Start an Excel interview and return the response (legacy method for backward compatibility)
        
        Args:
            conversation_id: Conversation ID
            user_message: User's message containing interview details
            
        Returns:
            Dict containing interview results and conversation updates
        """
        try:
            # Verify that the conversation exists
            collection = mongodb.get_collection(self.collection_name)
            conversation = collection.find_one({"_id": ObjectId(conversation_id)})
            
            if not conversation:
                raise ValueError(f"Conversation with ID {conversation_id} not found")
            
            # Store the user message in the conversation history
            timestamp = datetime.utcnow()
            collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$push": {"messages": {
                    "role": "user",
                    "content": user_message,
                    "timestamp": timestamp
                }}}
            )
            
            # Run the Excel interview workflow
            logger.info(f"Starting Excel interview for conversation: {conversation_id}")
            workflow_result = await run_excel_interview_workflow(
                user_message, 
                conversation_id, 
                "1"
            )
            
            # Extract the response from workflow result
            if hasattr(workflow_result, 'result') and workflow_result.result:
                # Handle workflow object with result attribute
                interview_response = workflow_result.result.get("feedback", "Interview completed")
                evaluation = workflow_result.result.get("evaluation", {})
                candidate_info = workflow_result.result.get("candidate_info", {})
            elif isinstance(workflow_result, dict):
                # Handle direct dictionary result
                interview_response = workflow_result.get("feedback", "Interview completed")
                evaluation = workflow_result.get("evaluation", {})
                candidate_info = workflow_result.get("candidate_info", {})
            else:
                interview_response = str(workflow_result) if workflow_result else "Interview completed"
                evaluation = {}
                candidate_info = {}
            
            # Store the AI response in the conversation history
            collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$push": {"messages": {
                    "role": "assistant",
                    "content": interview_response,
                    "timestamp": timestamp
                }},
                "$set": {
                    "interview_completed": True,
                    "evaluation": evaluation,
                    "candidate_info": candidate_info,
                    "completed_at": timestamp
                }}
            )
            
            logger.info(f"Excel interview completed for conversation: {conversation_id}")
            
            return {
                "conversation_id": conversation_id,
                "response": interview_response,
                "evaluation": evaluation,
                "candidate_info": candidate_info,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error in Excel interview: {e}")
            raise
    
    def get_interview_state(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get the current interview state for a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dict containing interview state
        """
        try:
            collection = mongodb.get_collection(self.collection_name)
            conversation = collection.find_one({"_id": ObjectId(conversation_id)})
            
            if not conversation:
                raise ValueError(f"Conversation with ID {conversation_id} not found")
            
            return conversation.get("interview_state", {
                "current_step": "intro",
                "completed_steps": [],
                "responses": {},
                "evaluations": {},
                "is_complete": False
            })
            
        except Exception as e:
            logger.error(f"Error getting interview state: {e}")
            raise
    
    def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation history and details
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dict containing conversation details and message history
        """
        try:
            collection = mongodb.get_collection(self.collection_name)
            conversation = collection.find_one({"_id": ObjectId(conversation_id)})
            
            if not conversation:
                raise ValueError(f"Conversation with ID {conversation_id} not found")
            
            return {
                "conversation_id": str(conversation["_id"]),
                "email": conversation.get("email"),
                "created_at": conversation.get("created_at"),
                "status": conversation.get("status", "active"),
                "interview_type": conversation.get("interview_type"),
                "interview_completed": conversation.get("interview_completed", False),
                "interview_state": conversation.get("interview_state", {}),
                "evaluation": conversation.get("evaluation", {}),
                "candidate_info": conversation.get("candidate_info", {}),
                "messages": conversation.get("messages", [])
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            raise
    
    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """
        Get all conversations
        
        Returns:
            List of conversation summaries
        """
        try:
            collection = mongodb.get_collection(self.collection_name)
            conversations = list(collection.find().sort("created_at", -1))
            
            result = []
            for conv in conversations:
                result.append({
                    "conversation_id": str(conv["_id"]),
                    "email": conv.get("email"),
                    "created_at": conv.get("created_at"),
                    "status": conv.get("status", "active"),
                    "interview_type": conv.get("interview_type"),
                    "interview_completed": conv.get("interview_completed", False),
                    "interview_state": conv.get("interview_state", {}),
                    "message_count": len(conv.get("messages", []))
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all conversations: {e}")
            raise
    
    def update_conversation_status(self, conversation_id: str, status: str) -> bool:
        """
        Update conversation status
        
        Args:
            conversation_id: Conversation ID
            status: New status (active, completed, archived)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = mongodb.get_collection(self.collection_name)
            result = collection.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": {"status": status}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating conversation status: {e}")
            return False

# Singleton instance
conversation_service = ConversationService() 