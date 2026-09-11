import { Fragment, useState } from "react"
import { ChevronDown, ChevronRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatDate, formatNumber } from "@/lib/utils"
import type { ChatRunLog, RunLogEvent } from "@/types"

interface RunLogsPanelProps {
  logs: ChatRunLog[]
}

function formatEvent(event: RunLogEvent): string {
  switch (event.type) {
    case "llm_call":
      return `LLM call · ${formatNumber(event.total_tokens ?? 0)} tokens`
    case "tool_call":
      return `Tool · ${event.name ?? "unknown"}`
    case "code":
      return "Code execution"
    case "error":
      return event.content ? `Error · ${event.content}` : "Error"
    default:
      return event.type
  }
}

export function RunLogsPanel({ logs }: RunLogsPanelProps) {
  const [open, setOpen] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const ordered = [...logs].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="border-y border-border/30 px-4 py-1.5 sm:px-5">
        <CollapsibleTrigger className="flex w-full items-center justify-between gap-2 text-left text-xs text-muted-foreground outline-none transition-colors hover:text-foreground">
          <span className="inline-flex items-center gap-2">
            Usage &amp; logs
            {ordered.length > 0 && (
              <Badge variant="secondary">{ordered.length}</Badge>
            )}
          </span>
          <ChevronDown
            className={`size-3.5 shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
          />
        </CollapsibleTrigger>

        <CollapsibleContent className="pt-2 pb-1">
          {ordered.length === 0 ? (
            <p className="pb-1 text-xs text-muted-foreground">
              No run logs yet for this chat.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-6" />
                  <TableHead>Time</TableHead>
                  <TableHead>Model</TableHead>
                  <TableHead>Iters</TableHead>
                  <TableHead>LLM</TableHead>
                  <TableHead>Tools</TableHead>
                  <TableHead>Tokens</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ordered.map((log) => {
                  const expanded = expandedId === log.id
                  return (
                    <Fragment key={log.id}>
                      <TableRow
                        className="cursor-pointer"
                        onClick={() =>
                          setExpandedId(expanded ? null : log.id)
                        }
                      >
                        <TableCell className="w-6 pr-0">
                          {expanded ? (
                            <ChevronDown className="size-3.5" />
                          ) : (
                            <ChevronRight className="size-3.5" />
                          )}
                        </TableCell>
                        <TableCell>{formatDate(log.created_at)}</TableCell>
                        <TableCell className="max-w-[8rem] truncate">
                          {log.model ?? "—"}
                        </TableCell>
                        <TableCell>{formatNumber(log.iterations)}</TableCell>
                        <TableCell>{formatNumber(log.llm_calls)}</TableCell>
                        <TableCell>{formatNumber(log.tool_calls)}</TableCell>
                        <TableCell>
                          {formatNumber(log.prompt_tokens)}/
                          {formatNumber(log.completion_tokens)}/
                          {formatNumber(log.total_tokens)}
                        </TableCell>
                      </TableRow>
                      {expanded && (
                        <TableRow>
                          <TableCell colSpan={7} className="bg-muted/30">
                            <ul className="flex flex-col gap-1 py-1 text-xs text-muted-foreground">
                              {log.events.length === 0 ? (
                                <li>No detailed events.</li>
                              ) : (
                                log.events.map((event, index) => (
                                  <li key={`${log.id}-e-${index}`}>
                                    <span className="text-foreground/70">
                                      iter {event.iteration ?? "—"}
                                    </span>
                                    {" · "}
                                    {formatEvent(event)}
                                  </li>
                                ))
                              )}
                            </ul>
                            <p className="pb-1 text-[0.7rem] text-muted-foreground">
                              Prompt {formatNumber(log.prompt_tokens)} ·
                              Completion{" "}
                              {formatNumber(log.completion_tokens)} · Total{" "}
                              {formatNumber(log.total_tokens)}
                            </p>
                          </TableCell>
                        </TableRow>
                      )}
                    </Fragment>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}
