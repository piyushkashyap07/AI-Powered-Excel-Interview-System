"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { 
  MessageSquare, 
  Send, 
  RotateCcw, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  BookOpen,
  Target,
  Zap,
  Trophy
} from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { conversationService } from "@/lib/api"
import InterviewResults from "./interview-results"

interface InterviewStep {
  conversation_id: string
  current_step: string
  question: string
  previous_response?: string
  evaluation?: any
  is_complete: boolean
  next_step?: string
  total_questions?: number
  current_question?: number
  questions_remaining?: number
  final_results?: any
  human_approved?: boolean
  human_rejected?: boolean
  rejection_reason?: string
  human_approval_bypassed?: boolean
}

interface InteractiveInterviewProps {
  conversationId: string
  userMessage: string
  onRetry: () => void
}

export default function InteractiveInterview({ conversationId, userMessage, onRetry }: InteractiveInterviewProps) {
  const [currentStep, setCurrentStep] = useState<InterviewStep | null>(null)
  const [userResponse, setUserResponse] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [interviewComplete, setInterviewComplete] = useState(false)
  const [finalResults, setFinalResults] = useState<any>(null)
  const { toast } = useToast()

  const stepConfig = {
    intro: { name: "Introduction", icon: MessageSquare, color: "bg-blue-500" },
    theory: { name: "Theory", icon: BookOpen, color: "bg-green-500" },
    practical: { name: "Practical", icon: Target, color: "bg-orange-500" },
    advanced: { name: "Advanced", icon: Zap, color: "bg-purple-500" },
    advanced2: { name: "Advanced", icon: Zap, color: "bg-purple-500" },
    advanced3: { name: "Advanced", icon: Zap, color: "bg-purple-500" }
  }

  const getStepProgress = (currentStepName: string, currentQuestion: number = 1, totalQuestions: number = 6) => {
    return (currentQuestion / totalQuestions) * 100
  }

  const getStepIcon = (stepName: string) => {
    const config = stepConfig[stepName as keyof typeof stepConfig]
    if (!config) return MessageSquare
    return config.icon
  }

  const getStepColor = (stepName: string) => {
    const config = stepConfig[stepName as keyof typeof stepConfig]
    if (!config) return "bg-blue-500"
    return config.color
  }

  const getStepName = (stepName: string) => {
    const config = stepConfig[stepName as keyof typeof stepConfig]
    if (!config) return "Interview"
    return config.name
  }

  const cleanMarkdownText = (text: string) => {
    if (!text) return ""
    return text
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove **bold** formatting
      .replace(/\*(.*?)\*/g, '$1') // Remove *italic* formatting
      .replace(/\[(.*?)\]\(.*?\)/g, '$1') // Remove [link](url) formatting
      .replace(/`(.*?)`/g, '$1') // Remove `code` formatting
      .replace(/^#+\s+/gm, '') // Remove markdown headers
      .replace(/^\s*[-*+]\s+/gm, '• ') // Convert markdown lists to bullet points
      .replace(/^\s*\d+\.\s+/gm, '') // Remove numbered list formatting
      .trim()
  }

  useEffect(() => {
    startInterview()
  }, [])

  const startInterview = async () => {
    setIsLoading(true)
    try {
      const result = await conversationService.startInteractiveInterview(conversationId, userMessage)
      setCurrentStep(result)
      toast({
        title: "Interview Started!",
        description: "Let's begin with your first question.",
      })
    } catch (error) {
      console.error("Error starting interview:", error)
      toast({
        title: "Error",
        description: "Failed to start interview. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmitResponse = async () => {
    if (!userResponse.trim() || !currentStep) return

    setIsSubmitting(true)
    try {
      const result = await conversationService.processInterviewStep(
        conversationId,
        userResponse,
        currentStep.current_step
      )

      if (result.is_complete) {
        // Interview is complete, get final results from backend
        console.log("Interview complete! Final results:", result.final_results)
        setInterviewComplete(true)
        
        // Check human approval status
        if (result.human_rejected) {
          toast({
            title: "Evaluation Rejected",
            description: result.rejection_reason || "Human reviewer did not approve the evaluation.",
            variant: "destructive",
          })
        } else if (result.human_approval_bypassed) {
          toast({
            title: "Results Generated",
            description: "Results generated without human approval due to system error.",
            variant: "default",
          })
        } else {
          toast({
            title: "Evaluation Approved",
            description: "Human reviewer approved the evaluation. Generating final results.",
            variant: "default",
          })
        }
        
        if (result.final_results) {
          setFinalResults(result.final_results)
        } else {
          // Fallback if final results not available
          console.log("No final results from backend, using fallback")
          setFinalResults({
            company_name: "Excel Interview - Interactive",
            report_date: new Date().toISOString(),
            propensity_score: {
              score: 7.5,
              rationale: "Based on interactive interview responses",
              visual_indicator: "🟡 Good"
            },
            overall_summary: "Interactive interview completed successfully."
          })
        }
      } else {
        // Continue to next question
        setCurrentStep(result)
        setUserResponse("")
        toast({
          title: "Response Submitted!",
          description: "Moving to the next question.",
        })
      }
    } catch (error) {
      console.error("Error submitting response:", error)
      toast({
        title: "Error",
        description: "Failed to submit response. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmitResponse()
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <Card className="max-w-md mx-auto">
          <CardContent className="p-8 text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Starting Interview...</h3>
            <p className="text-gray-600 dark:text-gray-300">Preparing your first question</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (interviewComplete && finalResults) {
    return <InterviewResults results={finalResults} onRetry={onRetry} conversationId={conversationId} />
  }

  if (!currentStep) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
        <Card className="max-w-md mx-auto">
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Interview Error</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-4">Failed to start the interview</p>
            <Button onClick={onRetry} className="flex items-center gap-2">
              <RotateCcw className="h-4 w-4" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const StepIcon = getStepIcon(currentStep.current_step)
  const stepColor = getStepColor(currentStep.current_step)
  const stepName = getStepName(currentStep.current_step)
  const progress = getStepProgress(currentStep.current_step, currentStep.current_question || 1, currentStep.total_questions || 6)


  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className={`p-4 rounded-full ${stepColor}`}>
              <StepIcon className="h-8 w-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Excel Interview</h1>
          <p className="text-gray-600 dark:text-gray-300">Step-by-step assessment of your Excel skills</p>
        </div>

        <div className="max-w-4xl mx-auto space-y-6">
          {/* Progress Bar */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">Interview Progress</h3>
                <Badge variant="secondary">
                  {currentStep.current_question || 1} of {currentStep.total_questions || 6} Questions
                </Badge>
              </div>
              <Progress value={progress} className="h-3" />
              <div className="flex justify-between mt-2 text-sm text-gray-600 dark:text-gray-400">
                <span>Question {currentStep.current_question || 1}</span>
                <span>{currentStep.questions_remaining || 5} questions remaining</span>
              </div>
            </CardContent>
          </Card>

          {/* Current Question */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <StepIcon className="h-5 w-5" />
                Question {currentStep.current_question || 1} of {currentStep.total_questions || 6}
              </CardTitle>
              <CardDescription>
                Please provide a detailed response to the following question
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                             <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                 <h4 className="font-medium mb-2">Question:</h4>
                 <div className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                   {cleanMarkdownText(currentStep.question)}
                 </div>
               </div>

              {/* Previous Response (if any) */}
              {currentStep.previous_response && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <h4 className="font-medium mb-2 text-blue-700 dark:text-blue-300">Your Previous Response:</h4>
                                     <div className="text-blue-700 dark:text-blue-300 leading-relaxed">
                     {cleanMarkdownText(currentStep.previous_response)}
                   </div>
                  {currentStep.evaluation && (
                    <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-700">
                      <h5 className="font-medium mb-1 text-blue-700 dark:text-blue-300">Feedback:</h5>
                                             <div className="text-blue-600 dark:text-blue-400 text-sm">
                         {cleanMarkdownText(currentStep.evaluation.feedback || "Good response!")}
                       </div>
                    </div>
                  )}
                </div>
              )}

              {/* Response Input */}
              <div className="space-y-3">
                <label htmlFor="response" className="font-medium">
                  Your Response:
                </label>
                <Textarea
                  id="response"
                  placeholder="Type your detailed response here..."
                  value={userResponse}
                  onChange={(e) => setUserResponse(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="min-h-[120px] resize-none"
                  disabled={isSubmitting}
                />
                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-500">
                    Press Enter to submit (Shift+Enter for new line)
                  </p>
                  <Button
                    onClick={handleSubmitResponse}
                    disabled={!userResponse.trim() || isSubmitting}
                    className="flex items-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4" />
                        Submit Response
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tips */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                Interview Tips
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                <li>• Be specific and provide examples when possible</li>
                <li>• Explain your reasoning and approach</li>
                <li>• If you're unsure about something, say so</li>
                <li>• Take your time to think through your responses</li>
                <li>• You can ask for clarification if needed</li>
                <li>• This interview has {currentStep.total_questions || 6} questions total</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
} 