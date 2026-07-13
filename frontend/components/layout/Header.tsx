"use client"
import { Bell } from "lucide-react"
import { useAuthStore } from "@/lib/store"

export function Header() {
  const { user } = useAuthStore()

  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-900">Dashboard</h1>
      </div>
      <div className="flex items-center space-x-4">
        <button className="relative rounded-full p-1 text-slate-400 hover:text-slate-500 focus:outline-none">
          <span className="sr-only">View notifications</span>
          <Bell className="h-6 w-6" aria-hidden="true" />
          <span className="absolute right-0 top-0 block h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white" />
        </button>
        <div className="flex items-center">
          <div className="ml-3">
            <p className="text-sm font-medium text-slate-700">{user?.first_name} {user?.last_name}</p>
            <p className="text-xs font-medium text-slate-500">{user?.role}</p>
          </div>
        </div>
      </div>
    </header>
  )
}
