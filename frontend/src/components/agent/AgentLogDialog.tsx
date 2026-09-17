import { CodeBlock } from "@/components/agent/CodeBlock"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { formatNumber } from "@/lib/utils"
import type { AgentStep, ChatRunLog, RunLogEvent } from "@/types"

interface AgentLogDialogProps {
  steps: AgentStep[]
  runLog?: ChatRunLog | null
  iterations?: number
  triggerLabel?: string
}

function EventBlock({ event }: { event: RunLogEvent }) {
  const details = [
    event.name ? `tool ${event.name}` : null,
    event.model ? String(event.model) : null,
    event.total_tokens != null
      ? `${formatNumber(event.total_tokens)} tokens`
      : null,
  ].filter(Boolean)

  return (
    <div className="flex flex-col gap-2 border border-border bg-card p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={event.type === "error" ? "destructive" : "outline"}>
          {event.type}
        </Badge>
        <span className="font-mono text-[0.6875rem] text-muted-foreground">
          step {event.iteration ?? "—"}
        </span>
        {details.length > 0 && (
          <span className="text-xs text-muted-foreground">
            {details.join(", ")}
          </span>
        )}
      </div>
      {event.content ? (
        <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-[0.6875rem] leading-relaxed text-foreground/85">
          {event.content}
        </pre>
      ) : null}
    </div>
  )
}

export function AgentLogDialog({
  steps,
  runLog,
  iterations,
  triggerLabel = "Open log",
}: AgentLogDialogProps) {
  const visibleSteps = steps.filter((step) => step.type !== "final")
  const events = runLog?.events ?? []

  return (
    <Dialog>
      <DialogTrigger
        render={
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="-ml-2.5 w-fit text-muted-foreground"
          />
        }
      >
        {triggerLabel}
      </DialogTrigger>
      <DialogContent className="flex h-[min(40rem,calc(100vh-2rem))] w-full max-w-[calc(100%-2rem)] flex-col gap-0 overflow-hidden rounded-sm p-0 sm:max-w-3xl">
        <DialogHeader className="border-b border-border px-4 py-3 pr-12">
          <DialogTitle>Run log</DialogTitle>
          <DialogDescription>
            {iterations != null
              ? `${iterations} iteration${iterations === 1 ? "" : "s"}`
              : "Code, model calls, and outputs for this answer"}
            {runLog?.model ? `. ${runLog.model}` : ""}
            {runLog
              ? `. ${formatNumber(runLog.total_tokens)} tokens`
              : ""}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="min-h-0 flex-1">
          <div className="flex flex-col gap-4 p-4">
            {runLog && (
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <div className="border border-border bg-muted/40 px-3 py-2">
                  <p className="text-xs text-muted-foreground">LLM calls</p>
                  <p className="font-mono text-sm">
                    {formatNumber(runLog.llm_calls)}
                  </p>
                </div>
                <div className="border border-border bg-muted/40 px-3 py-2">
                  <p className="text-xs text-muted-foreground">Tools</p>
                  <p className="font-mono text-sm">
                    {formatNumber(runLog.tool_calls)}
                  </p>
                </div>
                <div className="border border-border bg-muted/40 px-3 py-2">
                  <p className="text-xs text-muted-foreground">Prompt</p>
                  <p className="font-mono text-sm">
                    {formatNumber(runLog.prompt_tokens)}
                  </p>
                </div>
                <div className="border border-border bg-muted/40 px-3 py-2">
                  <p className="text-xs text-muted-foreground">Completion</p>
                  <p className="font-mono text-sm">
                    {formatNumber(runLog.completion_tokens)}
                  </p>
                </div>
              </div>
            )}

            {visibleSteps.length > 0 && (
              <div className="flex flex-col gap-3">
                <p className="text-sm font-medium">Reasoning</p>
                {visibleSteps.map((step, index) => (
                  <div
                    key={`${step.iteration}-${step.type}-${index}`}
                    className="flex flex-col gap-2 border-l-2 border-bar pl-3"
                  >
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          step.type === "error" ? "destructive" : "outline"
                        }
                        className="capitalize"
                      >
                        {step.type}
                      </Badge>
                      <span className="font-mono text-[0.6875rem] text-muted-foreground">
                        step {step.iteration}
                      </span>
                    </div>
                    {step.type === "code" ? (
                      <CodeBlock content={step.content} />
                    ) : (
                      <pre
                        className={
                          step.type === "error"
                            ? "overflow-x-auto whitespace-pre-wrap border border-destructive/30 bg-destructive/5 p-2.5 font-mono text-[0.6875rem] leading-relaxed text-destructive"
                            : "overflow-x-auto whitespace-pre-wrap border border-border bg-muted p-2.5 font-mono text-[0.6875rem] leading-relaxed"
                        }
                      >
                        {step.content}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            )}

            {events.length > 0 && (
              <div className="flex flex-col gap-3">
                <p className="text-sm font-medium">Events</p>
                {events.map((event, index) => (
                  <EventBlock
                    key={`${event.type}-${event.iteration}-${index}`}
                    event={event}
                  />
                ))}
              </div>
            )}

            {visibleSteps.length === 0 && events.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No detailed log for this turn yet.
              </p>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
