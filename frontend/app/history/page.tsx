"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Calendar, TrendingUp, Download, Eye, Filter, FileSpreadsheet } from "lucide-react"
import { conversationService } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface Conversation {
  conversation_id: string
  email: string
  created_at: string
  status: string
  interview_type: string
  interview_completed: boolean
  message_count: number
}

export default function HistoryPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [filteredConversations, setFilteredConversations] = useState<Conversation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [dateFilter, setDateFilter] = useState("all")
  const { toast } = useToast()

  useEffect(() => {
    loadConversations()
  }, [])

  useEffect(() => {
    filterConversations()
  }, [conversations, searchTerm, statusFilter, dateFilter])

  const loadConversations = async () => {
    try {
      const response = await conversationService.getConversations()
      if (response.status_code === 200) {
        setConversations(response.data)
      }
    } catch (error) {
      console.error("Error loading conversations:", error)
      toast({
        title: "Error",
        description: "Failed to load interview history",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const filterConversations = () => {
    let filtered = conversations

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (conv) =>
          conv.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
          conv.conversation_id.toLowerCase().includes(searchTerm.toLowerCase()),
      )
    }

    // Status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((conv) => {
        if (statusFilter === "completed") return conv.interview_completed
        if (statusFilter === "pending") return !conv.interview_completed
        return conv.status === statusFilter
      })
    }

    // Date filter
    if (dateFilter !== "all") {
      const now = new Date()
      filtered = filtered.filter((conv) => {
        const convDate = new Date(conv.created_at)
        const diffTime = now.getTime() - convDate.getTime()
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

        if (dateFilter === "today") return diffDays <= 1
        if (dateFilter === "week") return diffDays <= 7
        if (dateFilter === "month") return diffDays <= 30
        return true
      })
    }

    setFilteredConversations(filtered)
  }

  const getStatusBadge = (conversation: Conversation) => {
    if (conversation.interview_completed) {
      return <Badge variant="default">Completed</Badge>
    } else {
      return <Badge variant="secondary">Pending</Badge>
    }
  }

  const exportHistory = () => {
    const csvContent = [
      ["Date", "Email", "Status", "Type", "Messages"].join(","),
      ...filteredConversations.map((conv) =>
        [
          new Date(conv.created_at).toLocaleDateString(),
          conv.email,
          conv.interview_completed ? "Completed" : "Pending",
          conv.interview_type,
          conv.message_count,
        ].join(","),
      ),
    ].join("\n")

    const blob = new Blob([csvContent], { type: "text/csv" })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "interview-history.csv"
    a.click()
    window.URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-300">Loading interview history...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Interview History</h1>
          <p className="text-gray-600 dark:text-gray-300">Track your Excel assessment progress over time</p>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filter & Search
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by email or ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                </SelectContent>
              </Select>

              <Select value={dateFilter} onValueChange={setDateFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by date" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Time</SelectItem>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="week">This Week</SelectItem>
                  <SelectItem value="month">This Month</SelectItem>
                </SelectContent>
              </Select>

              <Button onClick={exportHistory} variant="outline" className="flex items-center gap-2 bg-transparent">
                <Download className="h-4 w-4" />
                Export CSV
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Showing {filteredConversations.length} of {conversations.length} interviews
          </p>
        </div>

        {/* Interview List */}
        {filteredConversations.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <FileSpreadsheet className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No interviews found</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                {conversations.length === 0
                  ? "You haven't taken any interviews yet."
                  : "No interviews match your current filters."}
              </p>
              <Button asChild>
                <a href="/">Start Your First Interview</a>
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {filteredConversations.map((conversation) => (
              <Card key={conversation.conversation_id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-gray-900 dark:text-white">{conversation.email}</h3>
                        {getStatusBadge(conversation)}
                      </div>

                      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {new Date(conversation.created_at).toLocaleDateString()}
                        </div>
                        <div className="flex items-center gap-1">
                          <TrendingUp className="h-4 w-4" />
                          {conversation.interview_type}
                        </div>
                        <div>{conversation.message_count} messages</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-1" />
                        View Details
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
