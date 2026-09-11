import { ChevronDown } from "lucide-react"
import { CodeBlock } from "@/components/agent/CodeBlock"
import { Badge } from "@/components/ui/badge"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import type { AgentStep } from "@/types"
import { cn } from "@/lib/utils"

interface StepTimelineProps {
  steps: AgentStep[]
  isStreaming?: boolean
  collapsible?: boolean
}

function StepRail({
  steps,
  isStreaming = false,
}: {
  steps: AgentStep[]
  isStreaming?: boolean
}) {
  return (
    <div className="flex w-full flex-col gap-2">
      {isStreaming && (
        <p className="font-mono text-[0.6875rem] text-muted-foreground">
          <span className="shimmer">Running</span>
        </p>
      )}

      <div className="flex flex-col gap-3 border-l border-border/60 pl-3">
        {steps.map((step, index) => (
          <div
            key={`${step.iteration}-${step.type}-${index}`}
            className="flex flex-col gap-2"
          >
            <div className="flex items-center gap-2">
              <Badge
                variant={step.type === "error" ? "destructive" : "outline"}
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
              <Collapsible defaultOpen={step.type === "error"}>
                <CollapsibleTrigger className="flex cursor-pointer items-center gap-1.5 text-xs text-muted-foreground outline-none hover:text-foreground [&[data-panel-open]_svg]:rotate-180">
                  <ChevronDown className="size-3.5 transition-transform" />
                  Show output
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <pre
                    className={cn(
                      "mt-2 overflow-x-auto whitespace-pre-wrap rounded-md border border-border/50 bg-muted p-2.5 font-mono text-[0.6875rem] leading-relaxed text-foreground/85",
                      step.type === "error" &&
                        "border-destructive/30 bg-destructive/5 text-destructive",
                    )}
                  >
                    {step.content}
                  </pre>
                </CollapsibleContent>
              </Collapsible>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export function StepTimeline({
  steps,
  isStreaming = false,
  collapsible = false,
}: StepTimelineProps) {
  const visibleSteps = steps.filter((step) => step.type !== "final")
  if (visibleSteps.length === 0) return null

  if (collapsible && !isStreaming) {
    return (
      <Collapsible className="w-full">
        <CollapsibleTrigger className="flex cursor-pointer items-center gap-1.5 text-xs text-muted-foreground outline-none hover:text-foreground [&[data-panel-open]_svg]:rotate-180">
          <ChevronDown className="size-3.5 transition-transform" />
          Agent steps
          <Badge variant="secondary">{visibleSteps.length}</Badge>
        </CollapsibleTrigger>
        <CollapsibleContent className="pt-2">
          <StepRail steps={visibleSteps} />
        </CollapsibleContent>
      </Collapsible>
    )
  }

  return <StepRail steps={visibleSteps} isStreaming={isStreaming} />
}
