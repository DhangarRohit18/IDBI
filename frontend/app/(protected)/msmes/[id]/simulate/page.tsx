"use client"

import { useState } from "react"
import { useParams } from "next/navigation"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Loader2, Play, AlertOctagon, CheckCircle2 } from "lucide-react"
import { toast } from "sonner"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts"

export default function ScenarioSimulationPage() {
  const params = useParams()
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  // Simulation form state
  const [scenarioType, setScenarioType] = useState("REVENUE_DROP")
  const [severity, setSeverity] = useState("30")
  const [duration, setDuration] = useState("6")

  const handleSimulate = async () => {
    setIsLoading(true)
    try {
      const response = await api.post("/simulation/run", {
        msme_id: params.id,
        scenario_type: scenarioType,
        severity_percent: parseFloat(severity),
        duration_months: parseInt(duration),
        probability: 1.0
      })
      setResult(response.data)
      toast.success("Simulation complete")
    } catch (error) {
      toast.error("Failed to run scenario simulation")
    } finally {
      setIsLoading(false)
    }
  }

  // Format cashflow for chart
  const cashflowData = result?.cashflow_comparison ? 
    result.cashflow_comparison.baseline.months.map((month: string, index: number) => ({
      month: `M${index + 1}`,
      baseline: result.cashflow_comparison.baseline.net_cashflow[index],
      stressed: result.cashflow_comparison.stressed.net_cashflow[index]
    })) : []

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Stress Testing & Scenario Simulation</h2>
        <p className="text-muted-foreground">Simulate "What-If" business scenarios to predict future repayment capacity.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Configuration Panel */}
        <Card className="col-span-1 h-fit">
          <CardHeader>
            <CardTitle>Scenario Configuration</CardTitle>
            <CardDescription>Configure stress parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Scenario Type</Label>
              <Select value={scenarioType} onValueChange={(val) => setScenarioType(val || "")}>
                <SelectTrigger>
                  <SelectValue placeholder="Select scenario" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="REVENUE_DROP">Revenue Drop</SelectItem>
                  <SelectItem value="INFLATION">Inflation Spike</SelectItem>
                  <SelectItem value="INTEREST_RATE_INCREASE">Interest Rate Hike</SelectItem>
                  <SelectItem value="DELAYED_PAYMENTS">Delayed Payments</SelectItem>
                  <SelectItem value="SUPPLIER_FAILURE">Supplier Failure</SelectItem>
                  <SelectItem value="PANDEMIC">Pandemic / Lockdown</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Severity (%)</Label>
              <Input 
                type="number" 
                value={severity} 
                onChange={(e) => setSeverity(e.target.value)} 
                min="1" max="100" 
              />
            </div>
            <div className="space-y-2">
              <Label>Duration (Months)</Label>
              <Input 
                type="number" 
                value={duration} 
                onChange={(e) => setDuration(e.target.value)} 
                min="1" max="60" 
              />
            </div>
            <Button onClick={handleSimulate} disabled={isLoading} className="w-full mt-4">
              {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
              Run Simulation
            </Button>
          </CardContent>
        </Card>

        {/* Results Panel */}
        <div className="col-span-2 space-y-6">
          {result ? (
            <>
              <div className="grid gap-4 md:grid-cols-3">
                <Card className={result.stress_test_passed ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Stress Test Result</CardTitle>
                  </CardHeader>
                  <CardContent className="flex items-center space-x-2">
                    {result.stress_test_passed ? (
                      <>
                        <CheckCircle2 className="h-8 w-8 text-emerald-600" />
                        <div className="text-2xl font-bold text-emerald-700">PASSED</div>
                      </>
                    ) : (
                      <>
                        <AlertOctagon className="h-8 w-8 text-red-600" />
                        <div className="text-2xl font-bold text-red-700">FAILED</div>
                      </>
                    )}
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Baseline PD</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{(result.baseline_pd * 100).toFixed(1)}%</div>
                    <p className="text-xs text-muted-foreground">Score: {result.baseline_risk_score.toFixed(0)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Stressed PD</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-600">{(result.stressed_pd * 100).toFixed(1)}%</div>
                    <p className="text-xs text-red-500">Score: {result.stressed_risk_score.toFixed(0)}</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Cash Flow Impact (Next {duration} Months)</CardTitle>
                  <CardDescription>Comparing projected baseline net cash flow vs stressed net cash flow.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-[350px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={cashflowData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip formatter={(value: any) => typeof value === 'number' ? `₹${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : value} />
                        <Legend />
                        <Line type="monotone" dataKey="baseline" stroke="#10b981" strokeWidth={2} name="Baseline Net Cashflow" dot={false} />
                        <Line type="monotone" dataKey="stressed" stroke="#ef4444" strokeWidth={2} name="Stressed Net Cashflow" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="h-full min-h-[400px] flex items-center justify-center border-dashed">
              <div className="text-center space-y-2">
                <AlertOctagon className="h-8 w-8 text-slate-300 mx-auto" />
                <h3 className="text-lg font-medium text-slate-900">No Simulation Run</h3>
                <p className="text-sm text-slate-500 max-w-sm mx-auto">
                  Configure the stress parameters on the left and click "Run Simulation" to see how this business performs under pressure.
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
