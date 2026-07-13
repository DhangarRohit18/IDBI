"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Loader2, Play, Bot, BrainCircuit, ShieldAlert, LineChart, MessageSquareText, SearchCode, Scale } from "lucide-react"
import { toast } from "sonner"

export default function MultiAgentAnalysisPage() {
  const params = useParams()
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)

  const runAnalysis = async () => {
    setIsLoading(true)
    try {
      // Assuming a LangGraph trigger endpoint
      const response = await api.post(`/agents/analyze`, { msme_id: params.id })
      setData(response.data)
      toast.success("Multi-Agent AI analysis complete")
    } catch (error) {
      toast.error("Failed to run AI agents")
    } finally {
      setIsLoading(false)
    }
  }

  const agentIcons: any = {
    "Risk Agent": <ShieldAlert className="h-5 w-5 text-red-500" />,
    "Fraud Agent": <SearchCode className="h-5 w-5 text-orange-500" />,
    "Financial Analyst Agent": <LineChart className="h-5 w-5 text-blue-500" />,
    "Market Agent": <BrainCircuit className="h-5 w-5 text-purple-500" />,
    "Compliance Agent": <Scale className="h-5 w-5 text-slate-500" />,
    "Recommendation Agent": <MessageSquareText className="h-5 w-5 text-emerald-500" />
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Multi-Agent Decision Engine</h2>
          <p className="text-muted-foreground">LangGraph orchestrated agents analyzing risk, fraud, compliance, and financials.</p>
        </div>
        <Button onClick={runAnalysis} disabled={isLoading}>
          {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
          Run Full AI Analysis
        </Button>
      </div>

      {!data && !isLoading && (
        <Card className="h-64 flex items-center justify-center border-dashed">
          <div className="text-center space-y-2">
            <Bot className="h-10 w-10 text-slate-300 mx-auto" />
            <h3 className="text-lg font-medium text-slate-900">No Agent Analysis Found</h3>
            <p className="text-sm text-slate-500 max-w-sm mx-auto">
              Click "Run Full AI Analysis" to trigger the LangGraph pipeline and generate a comprehensive decision.
            </p>
          </div>
        </Card>
      )}

      {isLoading && (
        <Card className="h-64 flex items-center justify-center">
          <div className="text-center space-y-4">
            <Loader2 className="h-10 w-10 animate-spin text-blue-600 mx-auto" />
            <p className="text-sm font-medium text-slate-600 animate-pulse">Agents are analyzing the MSME data...</p>
          </div>
        </Card>
      )}

      {data && (
        <div className="grid gap-6 md:grid-cols-3">
          {/* Coordinator Final Decision */}
          <Card className="col-span-3 border-2 border-blue-100 bg-blue-50/50">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bot className="h-6 w-6 text-blue-600" />
                <span>Coordinator Agent: Final Recommendation</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-4 mb-4">
                <Badge className={data.decision === "Approve" ? "bg-emerald-500" : data.decision === "Reject" ? "bg-red-500" : "bg-amber-500"} text-lg py-1 px-4>
                  {data.decision}
                </Badge>
                <span className="text-sm text-muted-foreground">Confidence: {(data.confidence * 100).toFixed(1)}%</span>
              </div>
              <p className="text-slate-700 leading-relaxed">
                {data.final_reasoning}
              </p>
            </CardContent>
          </Card>

          {/* Individual Agent Outputs */}
          {data.agent_logs?.map((log: any, index: number) => (
            <Card key={index} className="col-span-1">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center space-x-2">
                  {agentIcons[log.agent_name] || <Bot className="h-5 w-5 text-slate-500" />}
                  <span>{log.agent_name}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant="outline" className="mb-2">{log.status}</Badge>
                <p className="text-sm text-slate-600">
                  {log.finding_summary}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
