"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Activity, ShieldAlert, BarChart3, TrendingDown } from "lucide-react"
import { toast } from "sonner"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from "recharts"

export default function RiskPredictionPage() {
  const params = useParams()
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchPrediction = async () => {
      try {
        const response = await api.post(`/risk/predict`, { msme_id: params.id })
        setData(response.data)
      } catch (error) {
        toast.error("Failed to run risk prediction")
      } finally {
        setIsLoading(false)
      }
    }

    if (params.id) {
      fetchPrediction()
    }
  }, [params.id])

  if (isLoading) {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <p className="text-muted-foreground">Running ensemble ML models...</p>
      </div>
    )
  }

  if (!data) return <div>No prediction data available.</div>

  const pdPercentage = (data.probability_of_default * 100).toFixed(1)
  const accuracy = (data.confidence_score * 100).toFixed(1)
  
  // Format SHAP data for chart
  const shapData = data.top_risk_factors?.map((f: any) => ({
    name: f.name.replace(/_/g, ' '),
    value: f.shap_value,
    direction: f.direction
  })) || []

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-10">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Predictive AI Risk Assessment</h2>
        <p className="text-muted-foreground">Ensemble ML prediction (LightGBM, XGBoost, CatBoost, NN) forecasting 12-month default probability.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="bg-slate-900 text-white border-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-300">Probability of Default (12m)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">{pdPercentage}%</div>
            <p className="text-xs text-slate-400 mt-1">Risk Tier: <span className="font-bold text-white">{data.risk_tier}</span></p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Prediction Accuracy</CardTitle>
            <Activity className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{accuracy}%</div>
            <p className="text-xs text-muted-foreground">Confidence across ensemble models</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Risk Score</CardTitle>
            <ShieldAlert className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.risk_score} <span className="text-sm text-muted-foreground font-normal">/ 1000</span></div>
            <p className="text-xs text-muted-foreground">Lower is better</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Recovery Probability</CardTitle>
            <TrendingDown className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(data.recovery_probability * 100).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">Estimated recovery on default</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="h-full">
          <CardHeader>
            <CardTitle>Common Interpretation Framework (SHAP)</CardTitle>
            <CardDescription>Factors driving the risk prediction. Red increases risk, green decreases risk.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={shapData} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={120} tick={{fontSize: 12}} />
                  <Tooltip formatter={(value: any) => typeof value === 'number' ? value.toFixed(4) : value} />
                  <Bar dataKey="value">
                    {shapData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.value > 0 ? '#ef4444' : '#10b981'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Ensemble Model Breakdown</CardTitle>
              <CardDescription>Individual model predictions contributing to the final ensemble PD.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b pb-2">
                  <span className="font-medium">LightGBM (30% weight)</span>
                  <Badge variant="outline">{(data.lgbm_score * 100).toFixed(1)}%</Badge>
                </div>
                <div className="flex justify-between items-center border-b pb-2">
                  <span className="font-medium">XGBoost (25% weight)</span>
                  <Badge variant="outline">{(data.xgb_score * 100).toFixed(1)}%</Badge>
                </div>
                <div className="flex justify-between items-center border-b pb-2">
                  <span className="font-medium">CatBoost (20% weight)</span>
                  <Badge variant="outline">{(data.catboost_score * 100).toFixed(1)}%</Badge>
                </div>
                <div className="flex justify-between items-center border-b pb-2">
                  <span className="font-medium">Random Forest (15% weight)</span>
                  <Badge variant="outline">{(data.rf_score * 100).toFixed(1)}%</Badge>
                </div>
                <div className="flex justify-between items-center pb-2">
                  <span className="font-medium">Neural Network (10% weight)</span>
                  <Badge variant="outline">{(data.nn_score * 100).toFixed(1)}%</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data Sources Utilized</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">Structured Financials (MCA)</Badge>
              <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">GST Returns Network</Badge>
              <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100">Bank Statement Txns</Badge>
              <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">Credit Bureau Data</Badge>
              <Badge className="bg-slate-100 text-slate-800 hover:bg-slate-100">Macroeconomic Indicators</Badge>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
