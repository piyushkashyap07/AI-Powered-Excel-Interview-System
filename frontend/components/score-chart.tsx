"use client"

import { useEffect, useState } from "react"

interface ScoreChartProps {
  score: number
}

export default function ScoreChart({ score }: ScoreChartProps) {
  const [animatedScore, setAnimatedScore] = useState(0)

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedScore(score)
    }, 500)

    return () => clearTimeout(timer)
  }, [score])

  const circumference = 2 * Math.PI * 45
  const strokeDasharray = circumference
  const strokeDashoffset = circumference - (animatedScore / 10) * circumference

  const getColor = (score: number) => {
    if (score >= 8) return "#10b981" // green
    if (score >= 6) return "#f59e0b" // yellow
    if (score >= 4) return "#f97316" // orange
    return "#ef4444" // red
  }

  return (
    <div className="relative w-32 h-32">
      <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
        {/* Background circle */}
        <circle cx="50" cy="50" r="45" stroke="#e5e7eb" strokeWidth="8" fill="none" />

        {/* Progress circle */}
        <circle
          cx="50"
          cy="50"
          r="45"
          stroke={getColor(animatedScore)}
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>

      {/* Score text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold" style={{ color: getColor(animatedScore) }}>
            {animatedScore.toFixed(1)}
          </div>
          <div className="text-xs text-gray-500">out of 10</div>
        </div>
      </div>
    </div>
  )
}
