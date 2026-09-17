import { Badge } from "@/components/ui/badge"
import type { DatasetStatus, JobStatus } from "@/types"
import { cn } from "@/lib/utils"

const STATUS_STYLES: Record<string, string> = {
  pending: "border-border bg-muted text-muted-foreground",
  processing: "border-border bg-muted text-foreground",
  running: "border-border bg-muted text-foreground",
  ready: "border-primary/30 bg-bar text-primary",
  completed: "border-primary/30 bg-bar text-primary",
  failed: "border-destructive/30 bg-destructive/10 text-destructive",
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
        "h-5 rounded-sm px-1.5 text-[0.6875rem] font-normal capitalize",
        STATUS_STYLES[status],
        className,
      )}
    >
      {status}
    </Badge>
  )
}
