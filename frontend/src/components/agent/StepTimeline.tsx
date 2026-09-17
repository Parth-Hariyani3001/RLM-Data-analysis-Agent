import { AgentLogDialog } from "@/components/agent/AgentLogDialog"
import type { AgentStep, ChatRunLog } from "@/types"

interface StepTimelineProps {
  steps: AgentStep[]
  isStreaming?: boolean
  iterations?: number
  runLog?: ChatRunLog | null
}

export function StepTimeline({
  steps,
  isStreaming = false,
  iterations,
  runLog,
}: StepTimelineProps) {
  const visibleSteps = steps.filter((step) => step.type !== "final")
  if (visibleSteps.length === 0 && !runLog && !isStreaming) return null

  const latest = visibleSteps[visibleSteps.length - 1]
  const label = isStreaming
    ? latest
      ? `${latest.type}…`
      : "Working…"
    : `${visibleSteps.length || "Run"} step${visibleSteps.length === 1 ? "" : "s"}`

  return (
    <AgentLogDialog
      steps={visibleSteps}
      runLog={runLog}
      iterations={iterations}
      triggerLabel={label}
    />
  )
}
