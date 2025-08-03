import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.workflows.Excel_Interview_workflow import run_excel_interview_workflow

# Load environment variables
load_dotenv()

async def test_workflow():
    """Test the Excel interview workflow"""
    try:
        print("Testing Excel interview workflow...")
        
        # Test data
        user_query = "Name: John Doe, Experience Level: Intermediate, Description: I have 3 years of experience with Excel, know basic formulas, VLOOKUP, and some pivot tables."
        user_id = "test_user_123"
        message_id = "test_message_456"
        
        # Run the workflow
        result = await run_excel_interview_workflow(user_query, user_id, message_id)
        
        print("Workflow completed successfully!")
        print("Result:", result)
        
        if hasattr(result, 'result'):
            print("Workflow result:", result.result)
        else:
            print("Direct result:", result)
            
    except Exception as e:
        print(f"Error testing workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow()) 