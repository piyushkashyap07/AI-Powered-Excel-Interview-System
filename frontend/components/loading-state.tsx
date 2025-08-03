"use client"

import React from "react"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Loader2, Brain, FileSpreadsheet, CheckCircle } from "lucide-react"

export default function LoadingState() {
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState(0)

  const steps = [
    { icon: FileSpreadsheet, text: "Analyzing your Excel experience..." },
    { icon: Brain, text: "AI is processing your skills..." },
    { icon: CheckCircle, text: "Generating personalized feedback..." },
  ]

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + 1

        // Update current step based on progress
        if (newProgress < 33) setCurrentStep(0)
        else if (newProgress < 66) setCurrentStep(1)
        else setCurrentStep(2)

        return newProgress >= 100 ? 100 : newProgress
      })
    }, 1800) // Complete in ~3 minutes (180 seconds / 100 = 1.8s per percent)

    return () => clearInterval(timer)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center">
      <Card className="w-full max-w-md mx-4">
        <CardContent className="p-8">
          <div className="text-center space-y-6">
            {/* Animated Icon */}
            <div className="flex justify-center">
              <div className="relative">
                <Loader2 className="h-16 w-16 text-blue-600 animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  {React.createElement(steps[currentStep].icon, {
                    className: "h-6 w-6 text-blue-800",
                  })}
                </div>
              </div>
            </div>

            {/* Title */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Processing Your Interview</h2>
              <p className="text-gray-600 dark:text-gray-300">This usually takes 2-3 minutes</p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <p className="text-sm text-gray-500">{progress}% complete</p>
            </div>

            {/* Current Step */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <p className="text-sm text-blue-800 dark:text-blue-200 font-medium">{steps[currentStep].text}</p>
            </div>

            {/* Steps Indicator */}
            <div className="flex justify-center space-x-2">
              {steps.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index <= currentStep ? "bg-blue-600" : "bg-gray-300"
                  }`}
                />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
