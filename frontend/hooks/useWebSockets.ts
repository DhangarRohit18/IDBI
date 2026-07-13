import { useEffect } from "react"
import { useAuthStore } from "@/lib/store"
import { toast } from "sonner"

export function useWebSockets() {
  const { user } = useAuthStore()

  useEffect(() => {
    if (!user) return

    const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws"
    const ws = new WebSocket(`${WS_URL}/${user.id}`)

    ws.onopen = () => {
      console.log("WebSocket connected for user", user.id)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === "ews_alert") {
          toast.warning(`Early Warning Alert: ${data.msme_name}`, {
            description: data.message,
            duration: 10000,
            action: {
              label: "View",
              onClick: () => window.location.href = `/msmes/${data.msme_id}`,
            },
          })
        }
      } catch (err) {
        console.error("Failed to parse WS message", err)
      }
    }

    ws.onerror = (error) => {
      console.error("WebSocket error", error)
    }

    ws.onclose = () => {
      console.log("WebSocket disconnected")
    }

    return () => {
      ws.close()
    }
  }, [user])
}
