"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  Users, 
  Activity, 
  Bell, 
  Settings,
  LogOut
} from "lucide-react"
import { useAuthStore } from "@/lib/store"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "MSMEs", href: "/msmes", icon: Users },
  { name: "Alerts", href: "/alerts", icon: Bell },
  { name: "Activity", href: "/activity", icon: Activity },
  { name: "Settings", href: "/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const { clearAuth } = useAuthStore()

  return (
    <div className="flex h-screen w-64 flex-col border-r bg-slate-50">
      <div className="flex h-14 items-center border-b px-4">
        <span className="text-xl font-bold tracking-tight text-blue-700">FinTwin AI</span>
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-2">
          {navigation.map((item) => {
            const isActive = pathname.startsWith(item.href)
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  isActive
                    ? "bg-blue-100 text-blue-700"
                    : "text-slate-700 hover:bg-slate-100",
                  "group flex items-center rounded-md px-2 py-2 text-sm font-medium"
                )}
              >
                <item.icon
                  className={cn(
                    isActive ? "text-blue-700" : "text-slate-400 group-hover:text-slate-500",
                    "mr-3 h-5 w-5 flex-shrink-0"
                  )}
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
      <div className="border-t p-4">
        <button
          onClick={() => {
            clearAuth()
            window.location.href = "/login"
          }}
          className="group flex w-full items-center rounded-md px-2 py-2 text-sm font-medium text-slate-700 hover:bg-red-50 hover:text-red-700"
        >
          <LogOut className="mr-3 h-5 w-5 text-slate-400 group-hover:text-red-500" />
          Logout
        </button>
      </div>
    </div>
  )
}
