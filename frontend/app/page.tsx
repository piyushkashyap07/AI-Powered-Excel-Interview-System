"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FileSpreadsheet, Target, TrendingUp } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { conversationService } from "@/lib/api"
import InterviewResults from "@/components/interview-results"
import InteractiveInterview from "@/components/interactive-interview"
import LoadingState from "@/components/loading-state"

export default function HomePage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    experienceLevel: "",
    description: "",
  })
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [conversationId, setConversationId] = useState(null)
  const [userMessage, setUserMessage] = useState("")
  const [interviewMode, setInterviewMode] = useState<"simulated" | "interactive" | null>(null)
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.email || !formData.experienceLevel || !formData.description) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)

    try {
      // Create conversation
      const conversation = await conversationService.createConversation(formData.email)
      setConversationId(conversation.conversation_id)

      // Prepare user message
      const message = `Name: ${formData.name || "Not provided"}, Experience Level: ${formData.experienceLevel}, Description: ${formData.description}`
      setUserMessage(message)

      // Start interactive interview
      setInterviewMode("interactive")

      toast({
        title: "Interview Started!",
        description: "You'll be asked questions one by one. Please answer each question thoroughly.",
      })
    } catch (error) {
      console.error("Interview error:", error)
      toast({
        title: "Interview Failed",
        description: "There was an error starting your interview. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const resetInterview = () => {
    setResults(null)
    setConversationId(null)
    setUserMessage("")
    setInterviewMode(null)
    setFormData({
      name: "",
      email: "",
      experienceLevel: "",
      description: "",
    })
  }

  if (isLoading) {
    return <LoadingState />
  }

  if (interviewMode === "interactive" && conversationId && userMessage) {
    return <InteractiveInterview conversationId={conversationId} userMessage={userMessage} onRetry={resetInterview} />
  }

  if (results) {
    return <InterviewResults results={results} onRetry={resetInterview} conversationId={conversationId} />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <div className="p-4 bg-blue-600 rounded-full">
              <FileSpreadsheet className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">AI-Powered Excel Interview System</h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Get comprehensive feedback on your Excel skills with our AI-powered assessment system
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <Card>
            <CardHeader className="text-center">
              <Target className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <CardTitle className="text-lg">Interactive Assessment</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 dark:text-gray-300 text-center">
                Answer 6 questions one by one and get real-time feedback on your responses
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <TrendingUp className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <CardTitle className="text-lg">Detailed Feedback</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 dark:text-gray-300 text-center">
                Get personalized recommendations and learning resources based on your performance
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="text-center">
              <FileSpreadsheet className="h-8 w-8 text-purple-600 mx-auto mb-2" />
              <CardTitle className="text-lg">Progress Tracking</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 dark:text-gray-300 text-center">
                Track your progress through each interview section with visual indicators
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Interview Form */}
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>Start Your Excel Interview</CardTitle>
            <CardDescription>
              Fill out the form below to begin your personalized Excel skills assessment
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name (Optional)</Label>
                  <Input
                    id="name"
                    placeholder="Your name"
                    value={formData.name}
                    onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="your.email@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="experience">Experience Level *</Label>
                <Select
                  value={formData.experienceLevel}
                  onValueChange={(value) => setFormData((prev) => ({ ...prev, experienceLevel: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select your experience level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Basic">Basic - New to Excel</SelectItem>
                    <SelectItem value="Intermediate">Intermediate - Some experience</SelectItem>
                    <SelectItem value="Advanced">Advanced - Extensive experience</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Describe Your Excel Experience *</Label>
                <Textarea
                  id="description"
                  placeholder="Tell us about your Excel experience, what functions you know, projects you've worked on, etc."
                  value={formData.description}
                  onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
                  className="min-h-[120px]"
                  required
                />
              </div>

              <Button type="submit" className="w-full" size="lg">
                Start Interactive Interview
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
