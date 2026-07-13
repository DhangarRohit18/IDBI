"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Loader2, Activity, Play, Bot, ArrowRight, ShieldAlert, FileText } from "lucide-react"
import { toast } from "sonner"
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from "recharts"

export default function MSMEProfilePage() {
  const params = useParams()
  const router = useRouter()
  const [msme, setMsme] = useState<any>(null)
  const [twin, setTwin] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const msmeRes = await api.get(`/msme/${params.id}`)
        setMsme(msmeRes.data)
        
        try {
          const twinRes = await api.get(`/digital-twin/${params.id}`)
          setTwin(twinRes.data)
        } catch (e) {
          console.warn("Digital twin not found yet")
        }
      } catch (error) {
        toast.error("Failed to load MSME profile")
      } finally {
        setIsLoading(false)
      }
    }

    if (params.id) {
      fetchData()
    }
  }, [params.id])

  if (isLoading) {
    return <div className="flex h-full items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-blue-600" /></div>
  }

  if (!msme) return <div>MSME not found.</div>

  const radarData = twin ? [
    { subject: 'Liquidity', A: twin.liquidity_score, fullMark: 100 },
    { subject: 'Solvency', A: twin.solvency_score, fullMark: 100 },
    { subject: 'Profitability', A: twin.profitability_score, fullMark: 100 },
    { subject: 'Efficiency', A: twin.efficiency_score, fullMark: 100 },
    { subject: 'Growth', A: twin.growth_index, fullMark: 100 },
    { subject: 'Compliance', A: twin.compliance_score, fullMark: 100 },
  ] : []

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10">
      {/* Header Profile */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">{msme.business_name}</h2>
          <div className="flex items-center space-x-2 mt-2 text-sm text-slate-500">
            <span>GSTIN: {msme.gstin}</span>
            <span>•</span>
            <span>{msme.industry_type}</span>
            <span>•</span>
            <span>{msme.city}, {msme.state}</span>
          </div>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => router.push(`/msmes/${params.id}/risk`)}>
            <ShieldAlert className="mr-2 h-4 w-4 text-amber-500" />
            Predictive AI Risk
          </Button>
          <Button variant="outline" onClick={() => router.push(`/msmes/${params.id}/agents`)}>
            <Bot className="mr-2 h-4 w-4 text-blue-500" />
            Multi-Agent Analysis
          </Button>
          <Button onClick={() => router.push(`/msmes/${params.id}/simulate`)}>
            <Play className="mr-2 h-4 w-4" />
            Scenario Sim
          </Button>
        </div>
      </div>

      <Tabs defaultValue="twin" className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          <TabsTrigger value="twin">AI Digital Twin</TabsTrigger>
          <TabsTrigger value="details">Company Details</TabsTrigger>
        </TabsList>
        
        <TabsContent value="twin" className="space-y-6 mt-6">
          {twin ? (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <Card className="bg-slate-900 text-white">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-slate-300">Business Health Score</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-4xl font-bold">{twin.health_score.toFixed(0)}</div>
                    <p className="text-xs text-slate-400 mt-1">Out of 100</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Risk Index</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{twin.risk_index.toFixed(0)}</div>
                    <p className="text-xs text-muted-foreground">Lower is better</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Growth Trend</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{twin.growth_index.toFixed(0)}</div>
                    <p className="text-xs text-muted-foreground">YoY momentum</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Twin Version</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">v{twin.version}</div>
                    <p className="text-xs text-muted-foreground">Updated {new Date(twin.updated_at).toLocaleDateString()}</p>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Financial & Behavioral Dimensions</CardTitle>
                    <CardDescription>Multi-dimensional analysis generated by the Digital Twin.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[350px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                          <PolarGrid stroke="#e2e8f0" />
                          <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 12 }} />
                          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#94a3b8' }} />
                          <Tooltip />
                          <Radar name={msme.business_name} dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.4} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>AI Narrative Summary</CardTitle>
                    <CardDescription>Generative AI analysis of the MSME's health</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm prose-slate max-w-none text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-md">
                      {twin.narrative_summary}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          ) : (
            <Card className="h-64 flex flex-col items-center justify-center border-dashed">
              <Activity className="h-10 w-10 text-slate-300 mb-4" />
              <h3 className="text-lg font-medium text-slate-900">Digital Twin Not Available</h3>
              <p className="text-sm text-slate-500 mt-1 mb-4">No AI Digital Twin has been generated for this MSME yet.</p>
              <Button>Generate Digital Twin</Button>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="details" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Business Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="font-semibold text-slate-900">Registered Address</p>
                  <p className="text-slate-600">{msme.address}</p>
                  <p className="text-slate-600">{msme.city}, {msme.state} {msme.pincode}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Registration Date</p>
                  <p className="text-slate-600">{msme.registration_date ? new Date(msme.registration_date).toLocaleDateString() : 'N/A'}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">PAN</p>
                  <p className="text-slate-600">{msme.pan}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">GSTIN</p>
                  <p className="text-slate-600">{msme.gstin}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
