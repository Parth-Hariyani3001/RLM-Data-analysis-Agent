import { AgentLogDialog } from "@/components/agent/AgentLogDialog"
import { Badge } from "@/components/ui/badge"
import { formatDate, formatNumber } from "@/lib/utils"
import type { ChatRunLog } from "@/types"

interface RunLogsPanelProps {
  logs: ChatRunLog[]
}

export function RunLogsPanel({ logs }: RunLogsPanelProps) {
  const ordered = [...logs].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )

  if (ordered.length === 0) return null

  const latest = ordered[0]

  return (
    <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-2 sm:px-5">
      <div className="min-w-0">
        <p className="truncate text-xs text-muted-foreground">
          Last run {formatDate(latest.created_at)}
          {latest.model ? `, ${latest.model}` : ""},{" "}
          {formatNumber(latest.total_tokens)} tokens
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {ordered.length > 1 && (
          <Badge variant="secondary">{ordered.length}</Badge>
        )}
        <AgentLogDialog
          steps={[]}
          runLog={latest}
          iterations={latest.iterations}
          triggerLabel="Open log"
        />
      </div>
    </div>
  )
}
