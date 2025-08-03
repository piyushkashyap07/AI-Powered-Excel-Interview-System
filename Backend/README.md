# AI-Powered Excel Interview System - Backend

This backend API provides a comprehensive multi-agent system for conducting automated Excel technical interviews with intelligent evaluation and feedback.

---

## 🎯 Key Features

- **Multi-Agent Interview System**: 5 specialized agents for comprehensive Excel assessment
- **Intelligent Evaluation**: Weighted scoring across multiple skill dimensions
- **OpenAI GPT-4o-mini Integration**: Advanced AI capabilities for natural conversations
- **MongoDB Storage**: Conversation history and interview results persistence
- **FastAPI Framework**: Modern, fast web framework with automatic API documentation
- **Comprehensive Logging**: Application monitoring and debugging

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   AI Workflow   │
│   (Next.js)     │◄──►│   (FastAPI)      │◄──►│   (LlamaIndex)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   MongoDB        │
                        │   (Data Store)   │
                        └──────────────────┘
```

---

## 🔧 API Keys Required

This application requires the following API keys:

- **OpenAI API Key**: For GPT-4o-mini LLM integration

- **MongoDB URI**: For database connection

#### Getting API Keys

1. **OpenAI API Key**: Visit [OpenAI Platform](https://platform.openai.com/api-keys) to get your OpenAI API key for GPT-4o-mini

3. **MongoDB URI**: Set up MongoDB locally or use MongoDB Atlas

Set these keys in your environment variables or `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
MONGODB_URI=your_mongodb_connection_string
```

---

## 📁 Project Structure

```
Backend/
│
├── app/
│   ├── __init__.py                # FastAPI app setup and metadata
│   ├── log_config.py              # Logging configuration
│   ├── services/                  # Business logic for conversation management
│   │   └── conversation_service.py
│   ├── workflows/                 # Multi-agent interview workflow
│   │   └── Excel_Interview_workflow.py
│   ├── prompts/                   # Agent prompt templates
│   │   ├── excel_interview_intro_prompt.py
│   │   ├── excel_theory_prompt.py
│   │   ├── excel_practical_prompt.py
│   │   ├── excel_advanced_prompt.py
│   │   └── excel_evaluator_prompt.py
│   ├── helpers/                   # Utility modules
│   │   ├── mongodb.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── chat_utils.py
│   ├── models/                    # Pydantic models and schemas
│   └── routes/                    # API route definitions
│
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker support for containerized deployment
├── main.py                        # App entry point (runs FastAPI)
├── logs/                          # Application logs (e.g., app.log)
└── README.md                      # This file
```

---

## 🚀 Installation & Setup

#### 1. **Clone the Repository**
```bash
git clone <repository-url>
cd coding-ninjas/Backend
```

#### 2. **Create and Activate a Virtual Environment**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

#### 3. **Install Dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. **Environment Configuration**
Create a `.env` file in the `Backend` directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
MONGODB_URI=your_mongodb_connection_string
```

#### 5. **Run the Application**
```bash
python main.py
# The API will be available at http://localhost:8000
```

---

## 📊 Multi-Agent Interview System

The system uses 5 specialized agents for comprehensive Excel assessment:

### 1. **Introduction Agent**
- Welcomes candidates and explains the interview process
- Assesses initial experience level and sets expectations

### 2. **Theory Agent** (25% weight)
- Tests conceptual Excel knowledge and best practices
- Evaluates understanding of Excel functions and concepts

### 3. **Practical Agent** (40% weight)
- Evaluates hands-on skills through scenario-based questions
- Tests formula writing, problem-solving, and real-world application

### 4. **Advanced Agent** (20% weight)
- Assesses advanced features like VBA, Power Query, and complex formulas
- Tests advanced Excel capabilities and optimization knowledge

### 5. **Evaluator Agent** (15% weight)
- Provides comprehensive scoring and constructive feedback
- Generates detailed assessment with learning recommendations

---

## 🚀 API Endpoints

### Core Endpoints
- `POST /` - Create new conversation
- `POST /excel-interview` - Start Excel interview workflow
- `GET /get_conversations` - Retrieve conversation history
- `GET /server-check` - Health check

### Example Usage

#### Start an Excel Interview
```bash
curl -X POST "http://localhost:8000/excel-interview" \
     -H "Content-Type: application/json" \
     -d '{
       "user_message": "I am an intermediate Excel user with 3 years of experience",
       "conversation_id": "unique_conversation_id"
     }'
```

#### Create New Conversation
```bash
curl -X POST "http://localhost:8000/" \
     -H "Content-Type: application/json" \
     -d '{"user_message": "Start Excel interview"}'
```

---

## 📈 Evaluation Criteria

### Scoring Rubric
- **Excellent (9-10)**: Demonstrates mastery, provides detailed explanations
- **Good (7-8)**: Shows solid knowledge, explains concepts well
- **Satisfactory (5-6)**: Basic understanding, can handle simple tasks
- **Needs Improvement (3-4)**: Limited knowledge, struggles with concepts
- **Poor (1-2)**: Minimal understanding, major knowledge gaps

### Skill Areas (Weighted)
1. **Theoretical Knowledge** (25%)
2. **Practical Application** (40%)
3. **Advanced Skills** (20%)
4. **Communication & Problem-Solving** (15%)

---

## 🔍 Monitoring & Logging

### Application Logs
- **Location**: `Backend/logs/app.log`
- **Level**: INFO, WARNING, ERROR
- **Format**: Timestamp, Level, Module, Message

### MongoDB Storage
- **Conversations**: Complete interview history
- **Results**: Detailed evaluation and scoring
- **Metadata**: Timestamps, user information, session data

---

## 🛠️ Development

### Adding New Question Types
1. Create new prompt files in `Backend/app/prompts/`
2. Add corresponding agents to the workflow in `Backend/app/workflows/Excel_Interview_workflow.py`
3. Update the evaluation criteria in the evaluator prompt

### Modifying Evaluation Weights
Edit the evaluation criteria in `Backend/app/prompts/excel_evaluator_prompt.py`:
```python
SKILL AREAS TO ASSESS:
1. Theoretical Knowledge (25% weight)
2. Practical Application (40% weight)
3. Advanced Skills (20% weight)
4. Communication & Problem-Solving (15% weight)
```

---

## 🚀 Deployment

### Local Development
```bash
cd Backend
python main.py
```

### Production Deployment
1. **Environment Variables**: Set production API keys and MongoDB URI
2. **Docker**: Use the provided Dockerfile for containerized deployment
3. **Cloud Platforms**: Deploy to AWS, GCP, Azure, or Heroku
4. **Database**: Use managed MongoDB service (Atlas, DocumentDB, etc.)

---

## 🤝 Contributing

1. Fork the repository and create a feature branch
2. Make your changes and add tests if needed
3. Submit a pull request with a clear description

---

## 📞 Support

For questions or issues:
1. Check the logs in `Backend/logs/app.log`
2. Review the API documentation at `http://localhost:8000/docs`
3. Open an issue in the repository

---

**Note**: This system is designed for educational and assessment purposes. For production use in hiring decisions, additional validation and human oversight are recommended.
