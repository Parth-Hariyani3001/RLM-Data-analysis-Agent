import { Badge } from "@/components/ui/badge"
import type { DatasetStatus, JobStatus } from "@/types"
import { cn } from "@/lib/utils"

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-500/12 text-amber-300/90 border-amber-500/25",
  processing: "bg-sky-500/12 text-sky-300/90 border-sky-500/25",
  running: "bg-sky-500/12 text-sky-300/90 border-sky-500/25",
  ready: "bg-emerald-500/12 text-emerald-300/90 border-emerald-500/25",
  completed: "bg-emerald-500/12 text-emerald-300/90 border-emerald-500/25",
  failed: "bg-red-500/12 text-red-300/90 border-red-500/25",
}

interface StatusBadgeProps {
  status: DatasetStatus | JobStatus
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "h-5 px-1.5 text-[0.6875rem] font-normal capitalize",
        STATUS_STYLES[status],
        className,
      )}
    >
      {status}
    </Badge>
  )
}
