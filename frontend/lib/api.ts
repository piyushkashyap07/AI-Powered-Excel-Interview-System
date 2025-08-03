const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

const api = {
  async request(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`

    const config: RequestInit = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        throw new ApiError(response.status, `HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(0, "Network error or server unavailable")
    }
  },

  async get(endpoint: string) {
    return this.request(endpoint, { method: "GET" })
  },

  async post(endpoint: string, data: any) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    })
  },
}

export const conversationService = {
  async createConversation(email: string) {
    const response = await api.post("/", { email })
    return response
  },

  async startExcelInterview(conversationId: string, userMessage: string) {
    const response = await api.post("/excel-interview", {
      conversation_id: conversationId,
      user_message: userMessage,
    })
    return response
  },

  // Interactive Interview Functions
  async startInteractiveInterview(conversationId: string, userMessage: string) {
    const response = await api.post("/start-interactive-interview", {
      conversation_id: conversationId,
      user_message: userMessage,
    })
    return response
  },

  async processInterviewStep(conversationId: string, userResponse: string, currentStep: string) {
    const response = await api.post("/process-interview-step", {
      conversation_id: conversationId,
      user_response: userResponse,
      current_step: currentStep,
    })
    return response
  },

  async getInterviewState(conversationId: string) {
    const response = await api.get(`/interview-state/${conversationId}`)
    return response
  },

  async getConversations() {
    const response = await api.get("/get_conversations")
    return response
  },

  async healthCheck() {
    const response = await api.get("/server-check")
    return response
  },
}

export { ApiError }
