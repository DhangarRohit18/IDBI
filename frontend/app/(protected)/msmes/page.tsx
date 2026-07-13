"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Search, Loader2, Plus, ArrowRight } from "lucide-react"

export default function MSMEListPage() {
  const router = useRouter()
  const [msmes, setMsmes] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")

  useEffect(() => {
    const fetchMSMEs = async () => {
      try {
        const response = await api.get("/msme/list?limit=50")
        setMsmes(response.data.items || [])
      } catch (error) {
        console.error("Failed to load MSMEs", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchMSMEs()
  }, [])

  const filteredMsmes = msmes.filter((m) => 
    m.business_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    m.gstin.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getRiskColor = (tier: string) => {
    switch (tier) {
      case "Very Low": return "bg-emerald-100 text-emerald-800"
      case "Low": return "bg-emerald-50 text-emerald-700"
      case "Medium": return "bg-amber-100 text-amber-800"
      case "High": return "bg-orange-100 text-orange-800"
      case "Very High": return "bg-red-100 text-red-800"
      default: return "bg-slate-100 text-slate-800"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">MSME Directory</h2>
          <p className="text-muted-foreground">Manage and monitor MSME profiles and loan applications.</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> Add MSME
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                placeholder="Search by business name or GSTIN..."
                className="pl-8"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Business Name</TableHead>
                    <TableHead>GSTIN</TableHead>
                    <TableHead>Industry</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Risk Tier</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredMsmes.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center h-24 text-slate-500">
                        No MSMEs found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredMsmes.map((msme) => (
                      <TableRow key={msme.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => router.push(`/msmes/${msme.id}`)}>
                        <TableCell className="font-medium text-blue-700">{msme.business_name}</TableCell>
                        <TableCell>{msme.gstin}</TableCell>
                        <TableCell>{msme.industry_type}</TableCell>
                        <TableCell>{msme.city}, {msme.state}</TableCell>
                        <TableCell>
                          <Badge className={getRiskColor(msme.current_risk_tier || "Pending")} variant="outline">
                            {msme.current_risk_tier || "Pending"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); router.push(`/msmes/${msme.id}`) }}>
                            View <ArrowRight className="ml-2 h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
