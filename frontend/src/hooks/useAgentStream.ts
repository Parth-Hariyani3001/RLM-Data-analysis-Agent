import { useCallback, useRef, useState } from "react"
import { getApiBase } from "@/api/client"
import { getToken } from "@/lib/auth"
import type { AgentStep, AgentStreamEvent, AgentUsageSummary } from "@/types"

interface UseAgentStreamResult {
  steps: AgentStep[]
  isStreaming: boolean
  error: string | null
  ask: (
    datasetId: string,
    question: string,
    sessionId?: string | null,
  ) => Promise<{
    answer: string
    iterations: number
    steps: AgentStep[]
    session_id?: string
    usage?: AgentUsageSummary
  } | null>
  abort: () => void
  reset: () => void
}

function parseSseChunk(buffer: string): {
  events: AgentStreamEvent[]
  remainder: string
} {
  const events: AgentStreamEvent[] = []
  const parts = buffer.split("\n\n")
  const remainder = parts.pop() ?? ""

  for (const part of parts) {
    const line = part
      .split("\n")
      .find((entry) => entry.startsWith("data: "))

    if (!line) continue

    try {
      events.push(JSON.parse(line.slice(6)) as AgentStreamEvent)
    } catch {
      // skip malformed chunks
    }
  }

  return { events, remainder }
}

export function useAgentStream(): UseAgentStreamResult {
  const [steps, setSteps] = useState<AgentStep[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const reset = useCallback(() => {
    setSteps([])
    setError(null)
  }, [])

  const abort = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setIsStreaming(false)
  }, [])

  const ask = useCallback(
    async (
      datasetId: string,
      question: string,
      sessionId?: string | null,
    ) => {
      abort()
      reset()
      setIsStreaming(true)

      const controller = new AbortController()
      abortRef.current = controller

      try {
        const response = await fetch(
          `${getApiBase()}/datasets/${datasetId}/ask`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${getToken()}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              question,
              ...(sessionId ? { session_id: sessionId } : {}),
            }),
            signal: controller.signal,
          },
        )

        if (!response.ok) {
          let message = response.statusText
          try {
            const body = await response.json()
            message = body.detail ?? message
          } catch {
            // ignore
          }
          throw new Error(String(message))
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error("No response stream available")
        }

        const decoder = new TextDecoder()
        let buffer = ""
        let finalResult: {
          answer: string
          iterations: number
          steps: AgentStep[]
          session_id?: string
          usage?: AgentUsageSummary
        } | null = null

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const { events, remainder } = parseSseChunk(buffer)
          buffer = remainder

          for (const event of events) {
            if (event.event === "step") {
              if (event.type === "final") continue
              const step: AgentStep = {
                type: event.type,
                content: event.content,
                iteration: event.iteration,
              }
              setSteps((current) => [...current, step])
            } else if (event.event === "final") {
              const stepsWithoutFinal = event.steps.filter(
                (step) => step.type !== "final",
              )
              setSteps(stepsWithoutFinal)
              finalResult = {
                answer: event.answer,
                iterations: event.iterations,
                steps: stepsWithoutFinal,
                session_id: event.session_id,
                usage: event.usage,
              }
            } else if (event.event === "error") {
              throw new Error(event.message)
            }
          }
        }

        return finalResult
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return null
        }
        const message = err instanceof Error ? err.message : "Stream failed"
        setError(message)
        throw err
      } finally {
        setIsStreaming(false)
        abortRef.current = null
      }
    },
    [abort, reset],
  )

  return { steps, isStreaming, error, ask, abort, reset }
}
