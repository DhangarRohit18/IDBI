"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { BellRing, AlertTriangle, Info, Loader2, ArrowRight } from "lucide-react"
import { toast } from "sonner"
import { formatDistanceToNow } from "date-fns"

export default function AlertsPage() {
  const router = useRouter()
  const [alerts, setAlerts] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await api.get("/ews/alerts?limit=50")
        setAlerts(response.data || [])
      } catch (error) {
        toast.error("Failed to load alerts")
      } finally {
        setIsLoading(false)
      }
    }

    fetchAlerts()
  }, [])

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case "CRITICAL": return <AlertTriangle className="h-5 w-5 text-red-600" />
      case "WARNING": return <BellRing className="h-5 w-5 text-amber-500" />
      case "INFO": return <Info className="h-5 w-5 text-blue-500" />
      default: return <BellRing className="h-5 w-5 text-slate-500" />
    }
  }

  const getAlertColor = (severity: string) => {
    switch (severity) {
      case "CRITICAL": return "border-red-200 bg-red-50/50"
      case "WARNING": return "border-amber-200 bg-amber-50/50"
      case "INFO": return "border-blue-200 bg-blue-50/50"
      default: return "border-slate-200 bg-white"
    }
  }

  const markAsRead = async (id: string) => {
    try {
      await api.post(`/ews/alerts/${id}/read`)
      setAlerts(alerts.map(a => a.id === id ? { ...a, status: 'read' } : a))
      toast.success("Alert marked as read")
    } catch (error) {
      toast.error("Failed to update alert")
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-10">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Early Warning Alerts</h2>
        <p className="text-muted-foreground">Monitor real-time EWS signals triggering from your portfolio.</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      ) : alerts.length === 0 ? (
        <Card className="h-64 flex flex-col items-center justify-center border-dashed">
          <BellRing className="h-10 w-10 text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-900">All clear</h3>
          <p className="text-sm text-slate-500">No active early warning alerts at this time.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <Card key={alert.id} className={`${getAlertColor(alert.severity)} transition-shadow hover:shadow-md`}>
              <CardContent className="p-4 flex items-start gap-4">
                <div className="mt-1">
                  {getAlertIcon(alert.severity)}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-semibold text-slate-900">{alert.msme_name}</h4>
                      <Badge variant="outline" className="bg-white">{alert.severity}</Badge>
                      {alert.status === 'unread' && <Badge className="bg-blue-600 text-white border-none">New</Badge>}
                    </div>
                    <span className="text-xs text-slate-500">
                      {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-slate-800">{alert.alert_type}</p>
                  <p className="text-sm text-slate-600">{alert.message}</p>
                  <div className="pt-2 flex items-center space-x-3">
                    <Button variant="outline" size="sm" onClick={() => router.push(`/msmes/${alert.msme_id}`)}>
                      View MSME <ArrowRight className="ml-2 h-3 w-3" />
                    </Button>
                    {alert.status === 'unread' && (
                      <Button variant="ghost" size="sm" onClick={() => markAsRead(alert.id)}>
                        Mark as read
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
