import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from app.helpers.mongodb import mongodb
from app.workflows.Excel_Interview_workflow import run_excel_interview_workflow

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
                "interview_type": "excel",  # Track interview type
                "status": "active"
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
    
    async def start_excel_interview(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """
        Start an Excel interview and return the response
        
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
                interview_response = workflow_result.result.get("feedback", "Interview completed")
                evaluation = workflow_result.result.get("evaluation", {})
                candidate_info = workflow_result.result.get("candidate_info", {})
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