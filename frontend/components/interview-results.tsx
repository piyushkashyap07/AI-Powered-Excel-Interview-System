"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Download,
  Share2,
  RotateCcw,
  Trophy,
  TrendingUp,
  BookOpen,
  CheckCircle,
  AlertCircle,
  XCircle,
  MessageSquare,
  Target,
  Zap,
} from "lucide-react"
import ScoreChart from "@/components/score-chart"
import { useToast } from "@/hooks/use-toast"

interface InterviewResultsProps {
  results: {
    company_name: string
    report_date: string
    propensity_score: {
      score: number
      rationale: string
      visual_indicator: string
    }
    overall_summary: string
  }
  onRetry: () => void
  conversationId: string
}

interface ParsedInterviewData {
  questions: Array<{
    type: string
    question: string
    response: string
    score: number
    feedback: string
  }>
  strengths: string[]
  improvements: string[]
  overallScore: number
}

export default function InterviewResults({ results, onRetry, conversationId }: InterviewResultsProps) {
  const [showConfetti, setShowConfetti] = useState(false)
  const { toast } = useToast()

  const { propensity_score, overall_summary, report_date } = results
  const score = propensity_score.score

  // Parse the interview summary to extract structured data
  const parseInterviewSummary = (summary: string): ParsedInterviewData => {
    const questions: Array<{
      type: string
      question: string
      response: string
      score: number
      feedback: string
    }> = []
    
    const strengths: string[] = []
    const improvements: string[] = []
    let overallScore = score

    // Extract questions and responses
    const questionSections = summary.split(/(\d+\.\s+[A-Z\s&]+:)/g)
    
    for (let i = 1; i < questionSections.length; i += 2) {
      const questionType = questionSections[i]?.replace(/^\d+\.\s+/, '').replace(':', '') || ''
      const content = questionSections[i + 1] || ''
      
      // Extract question, response, score, and feedback
      const questionMatch = content.match(/Question:\s*(.*?)(?=Your Response:|$)/s)
      const responseMatch = content.match(/Your Response:\s*(.*?)(?=Score:|$)/s)
      const scoreMatch = content.match(/Score:\s*(\d+)\/10/)
      const feedbackMatch = content.match(/Feedback:\s*(.*?)(?=\n|$)/s)
      
      if (questionType && questionMatch) {
        questions.push({
          type: questionType,
          question: questionMatch[1]?.trim() || '',
          response: responseMatch?.[1]?.trim() || '',
          score: parseInt(scoreMatch?.[1] || '0'),
          feedback: feedbackMatch?.[1]?.trim() || ''
        })
      }
    }

    // Extract strengths and improvements
    const strengthsMatch = summary.match(/Strengths:\s*((?:-.*?\n?)*)/s)
    const improvementsMatch = summary.match(/Areas for Improvement:\s*((?:-.*?\n?)*)/s)
    
    if (strengthsMatch) {
      strengths.push(...strengthsMatch[1].split('\n').filter(line => line.trim().startsWith('-')).map(line => line.replace('-', '').trim()))
    }
    
    if (improvementsMatch) {
      improvements.push(...improvementsMatch[1].split('\n').filter(line => line.trim().startsWith('-')).map(line => line.replace('-', '').trim()))
    }

    return { questions, strengths, improvements, overallScore }
  }

  const interviewData = parseInterviewSummary(overall_summary)

  const getScoreColor = (score: number) => {
    if (score >= 8) return "text-green-600"
    if (score >= 6) return "text-yellow-600"
    if (score >= 4) return "text-orange-600"
    return "text-red-600"
  }

  const getScoreIcon = (score: number) => {
    if (score >= 8) return <CheckCircle className="h-5 w-5 text-green-600" />
    if (score >= 6) return <AlertCircle className="h-5 w-5 text-yellow-600" />
    if (score >= 4) return <AlertCircle className="h-5 w-5 text-orange-600" />
    return <XCircle className="h-5 w-5 text-red-600" />
  }

  const getScoreLabel = (score: number) => {
    if (score >= 8) return "Excellent"
    if (score >= 6) return "Good"
    if (score >= 4) return "Satisfactory"
    return "Needs Improvement"
  }

  const getQuestionTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'introduction':
        return <MessageSquare className="h-4 w-4" />
      case 'theory':
        return <BookOpen className="h-4 w-4" />
      case 'practical':
        return <Target className="h-4 w-4" />
      case 'advanced':
        return <Zap className="h-4 w-4" />
      default:
        return <MessageSquare className="h-4 w-4" />
    }
  }

  const handleExport = () => {
    const printContent = document.getElementById("results-content")
    if (printContent) {
      window.print()
    }
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: "My Excel Interview Results",
          text: `I scored ${score}/10 on my Excel skills assessment!`,
          url: window.location.href,
        })
      } catch (error) {
        console.log("Error sharing:", error)
      }
    } else {
      navigator.clipboard.writeText(`I scored ${score}/10 on my Excel skills assessment! ${window.location.href}`)
      toast({
        title: "Link Copied!",
        description: "Results link copied to clipboard",
      })
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Trophy className="h-12 w-12 text-yellow-500" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Interview Results</h1>
          <p className="text-gray-600 dark:text-gray-300">Completed on {new Date(report_date).toLocaleDateString()}</p>
        </div>

        <div id="results-content" className="max-w-4xl mx-auto space-y-6">
          {/* Score Overview */}
          <Card>
            <CardHeader className="text-center">
              <CardTitle className="flex items-center justify-center gap-2">
                {getScoreIcon(score)}
                Overall Score: {getScoreLabel(score)}
              </CardTitle>
              <CardDescription>Your Excel skills assessment results</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row items-center gap-8">
                <div className="flex-shrink-0">
                  <ScoreChart score={score} />
                </div>
                <div className="flex-1 space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Score Progress</span>
                      <span className={`text-sm font-bold ${getScoreColor(score)}`}>{score}/10</span>
                    </div>
                    <Progress value={score * 10} className="h-3" />
                  </div>

                  <Badge
                    variant={score >= 8 ? "default" : score >= 6 ? "secondary" : "destructive"}
                    className="text-sm"
                  >
                    {propensity_score.visual_indicator}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Interview Questions & Responses */}
          {interviewData.questions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Interview Breakdown
                </CardTitle>
                <CardDescription>Detailed analysis of each interview section</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {interviewData.questions.map((question, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-2 mb-3">
                      {getQuestionTypeIcon(question.type)}
                      <h4 className="font-semibold capitalize">{question.type}</h4>
                      <Badge variant={question.score >= 8 ? "default" : question.score >= 6 ? "secondary" : "destructive"}>
                        {question.score}/10
                      </Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <div>
                        <h5 className="font-medium text-sm text-gray-600 dark:text-gray-400">Question:</h5>
                        <p className="text-sm text-gray-700 dark:text-gray-300">{question.question}</p>
                      </div>
                      
                      <div>
                        <h5 className="font-medium text-sm text-gray-600 dark:text-gray-400">Your Response:</h5>
                        <p className="text-sm text-gray-700 dark:text-gray-300">{question.response}</p>
                      </div>
                      
                      <div>
                        <h5 className="font-medium text-sm text-gray-600 dark:text-gray-400">Feedback:</h5>
                        <p className="text-sm text-gray-700 dark:text-gray-300">{question.feedback}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Strengths & Improvements */}
          <div className="grid md:grid-cols-2 gap-6">
            {interviewData.strengths.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    Your Strengths
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {interviewData.strengths.map((strength, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-700 dark:text-gray-300">{strength}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {interviewData.improvements.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-orange-600">
                    <AlertCircle className="h-5 w-5" />
                    Areas for Improvement
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {interviewData.improvements.map((improvement, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <AlertCircle className="h-4 w-4 text-orange-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-700 dark:text-gray-300">{improvement}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Learning Resources */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Recommended Next Steps
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                {score < 6 && (
                  <div className="space-y-2">
                    <h4 className="font-semibold text-red-600">Areas for Improvement</h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                      <li>• Practice basic Excel functions (SUM, AVERAGE, COUNT)</li>
                      <li>• Learn data formatting and cell references</li>
                      <li>• Explore Excel templates and tutorials</li>
                    </ul>
                  </div>
                )}

                {score >= 6 && score < 8 && (
                  <div className="space-y-2">
                    <h4 className="font-semibold text-yellow-600">Enhancement Opportunities</h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                      <li>• Master advanced functions (VLOOKUP, INDEX/MATCH)</li>
                      <li>• Learn PivotTables and data analysis</li>
                      <li>• Practice with complex formulas and macros</li>
                    </ul>
                  </div>
                )}

                {score >= 8 && (
                  <div className="space-y-2">
                    <h4 className="font-semibold text-green-600">Advanced Skills</h4>
                    <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                      <li>• Explore Power Query and Power Pivot</li>
                      <li>• Learn VBA programming</li>
                      <li>• Consider Excel certification programs</li>
                    </ul>
                  </div>
                )}

                <div className="space-y-2">
                  <h4 className="font-semibold text-blue-600">Learning Resources</h4>
                  <ul className="text-sm space-y-1 text-gray-600 dark:text-gray-300">
                    <li>• Microsoft Excel Help Center</li>
                    <li>• Excel online courses (Coursera, Udemy)</li>
                    <li>• Practice with real datasets</li>
                    <li>• Join Excel communities and forums</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4 justify-center">
            <Button onClick={onRetry} variant="outline" className="flex items-center gap-2 bg-transparent">
              <RotateCcw className="h-4 w-4" />
              Take Another Interview
            </Button>

            <Button onClick={handleExport} variant="outline" className="flex items-center gap-2 bg-transparent">
              <Download className="h-4 w-4" />
              Export Results
            </Button>

            <Button onClick={handleShare} className="flex items-center gap-2">
              <Share2 className="h-4 w-4" />
              Share Results
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
