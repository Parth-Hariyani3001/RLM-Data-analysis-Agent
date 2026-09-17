import { useEffect, useMemo, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { MarkdownContent } from "@/components/agent/MarkdownContent"
import {
  ChevronDown,
  MessageSquarePlus,
  SendHorizontal,
  Square,
} from "lucide-react"
import { toast } from "sonner"
import { StepTimeline } from "@/components/agent/StepTimeline"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group"
import { Marker, MarkerContent, MarkerIcon } from "@/components/ui/marker"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Message, MessageContent } from "@/components/ui/message"
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller"
import { Spinner } from "@/components/ui/spinner"
import { useAgentStream } from "@/hooks/useAgentStream"
import {
  useChatSession,
  useChatSessions,
  useCreateChatSession,
} from "@/hooks/useChatSessions"
import type { ChatMessage, ChatRunLog, Dataset } from "@/types"

interface ChatPanelProps {
  dataset: Dataset
}

const SUGGESTED_PROMPTS = [
  "What columns does this dataset have?",
  "Show the top values in the first categorical column.",
  "Summarize missing values across columns.",
]

function withoutFinalSteps(steps: ChatMessage["steps"]) {
  return steps?.filter((step) => step.type !== "final")
}

function runLogForMessage(
  message: ChatMessage,
  logs: ChatRunLog[] | undefined,
): ChatRunLog | undefined {
  const matched = logs?.find((log) => log.message_id === message.id)
  if (matched) return matched
  if (!message.usage) return undefined

  return {
    id: `usage-${message.id}`,
    session_id: message.session_id ?? "",
    message_id: message.id,
    model: message.usage.model ?? null,
    iterations: message.usage.iterations,
    llm_calls: message.usage.llm_calls,
    tool_calls: message.usage.tool_calls,
    prompt_tokens: message.usage.prompt_tokens,
    completion_tokens: message.usage.completion_tokens,
    total_tokens: message.usage.total_tokens,
    events: message.usage.events,
    created_at: message.created_at ?? new Date().toISOString(),
  }
}

export function ChatPanel({ dataset }: ChatPanelProps) {
  const queryClient = useQueryClient()
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState("")
  const { steps, isStreaming, ask, abort, reset } = useAgentStream()

  const { data: sessions = [], isLoading: sessionsLoading } = useChatSessions(
    dataset.id,
  )
  const { data: sessionDetail, isLoading: sessionLoading } = useChatSession(
    dataset.id,
    activeSessionId,
  )
  const createSession = useCreateChatSession(dataset.id)

  const isReady = dataset.status === "ready"
  const showEmpty = messages.length === 0 && !isStreaming && !sessionLoading

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) ?? null,
    [sessions, activeSessionId],
  )

  useEffect(() => {
    if (sessionsLoading) return

    if (sessions.length === 0) {
      setActiveSessionId(null)
      setMessages([])
      return
    }

    setActiveSessionId((current) => {
      if (current && sessions.some((session) => session.id === current)) {
        return current
      }
      return sessions[0].id
    })
  }, [sessions, sessionsLoading])

  useEffect(() => {
    if (!sessionDetail || sessionDetail.id !== activeSessionId) return
    if (isStreaming) return

    setMessages(
      sessionDetail.messages.map((message) => ({
        id: message.id,
        role: message.role,
        content: message.content,
        steps: withoutFinalSteps(message.steps),
        iterations: message.iterations ?? undefined,
        session_id: message.session_id,
        created_at: message.created_at,
      })),
    )
  }, [sessionDetail, activeSessionId, isStreaming])

  const handleNewChat = async () => {
    if (isStreaming) return

    try {
      const session = await createSession.mutateAsync()
      setActiveSessionId(session.id)
      setMessages([])
      reset()
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to create chat"
      toast.error(message)
    }
  }

  const handleSubmit = async (override?: string) => {
    const trimmed = (override ?? question).trim()
    if (!trimmed || !isReady || isStreaming) return

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    }

    setMessages((current) => [...current, userMessage])
    setQuestion("")
    reset()

    try {
      const result = await ask(dataset.id, trimmed, activeSessionId)
      if (!result) return

      if (result.session_id && result.session_id !== activeSessionId) {
        setActiveSessionId(result.session_id)
      }

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          steps: withoutFinalSteps(result.steps),
          iterations: result.iterations,
          usage: result.usage,
        },
      ])

      await queryClient.invalidateQueries({
        queryKey: ["chat-sessions", dataset.id],
      })
      if (result.session_id || activeSessionId) {
        await queryClient.invalidateQueries({
          queryKey: [
            "chat-sessions",
            dataset.id,
            result.session_id ?? activeSessionId,
          ],
        })
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to get an answer"
      toast.error(message)
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden border border-border bg-card">
      <div className="relative z-10 flex shrink-0 items-center justify-between gap-3 border-b border-border bg-card px-4 py-2 sm:px-8 lg:px-10">
        <h2 className="min-w-0 truncate text-sm font-medium tracking-tight">
          {activeSession?.title ?? "New chat"}
        </h2>

        <div className="flex shrink-0 items-center gap-1.5">
          <DropdownMenu>
            <DropdownMenuTrigger
              disabled={sessionsLoading || isStreaming}
              render={
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={sessionsLoading || isStreaming}
                />
              }
            >
              <span className="max-w-[8rem] truncate">Chats</span>
              <ChevronDown data-icon="inline-end" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-52">
              <DropdownMenuGroup>
                <DropdownMenuLabel>Sessions</DropdownMenuLabel>
                {sessions.length === 0 ? (
                  <DropdownMenuItem disabled>No chats yet</DropdownMenuItem>
                ) : (
                  sessions.map((session) => (
                    <DropdownMenuItem
                      key={session.id}
                      onClick={() => {
                        if (session.id === activeSessionId || isStreaming) return
                        setActiveSessionId(session.id)
                        reset()
                      }}
                    >
                      <span className="truncate">
                        {session.title ?? "Untitled chat"}
                      </span>
                    </DropdownMenuItem>
                  ))
                )}
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                disabled={isStreaming || createSession.isPending}
                onClick={() => void handleNewChat()}
              >
                <MessageSquarePlus />
                New chat
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-label="New chat"
            disabled={isStreaming || createSession.isPending}
            onClick={() => void handleNewChat()}
          >
            <MessageSquarePlus />
          </Button>
        </div>
      </div>

      <MessageScrollerProvider autoScroll>
        <MessageScroller className="min-h-0 flex-1">
          <MessageScrollerViewport>
            <MessageScrollerContent className="w-full px-4 py-5 sm:px-8 lg:px-10">
              {showEmpty && (
                <MessageScrollerItem messageId="empty">
                  <Empty className="items-start border-0 bg-transparent py-6 text-left">
                    <EmptyHeader className="items-start">
                      <EmptyTitle>
                        {isReady
                          ? `Ask about ${dataset.name}`
                          : "Chat is locked"}
                      </EmptyTitle>
                      <EmptyDescription>
                        {isReady
                          ? "The agent writes and runs Python against this file."
                          : "Chat opens once ingestion finishes."}
                      </EmptyDescription>
                    </EmptyHeader>
                    {isReady && (
                      <EmptyContent className="items-stretch">
                        <div className="flex w-full flex-col gap-0 border-l-2 border-bar">
                          {SUGGESTED_PROMPTS.map((prompt) => (
                            <Button
                              key={prompt}
                              type="button"
                              variant="ghost"
                              className="h-auto justify-start rounded-none px-3 py-2.5 text-left text-sm leading-snug font-normal whitespace-normal text-muted-foreground hover:bg-bar/60 hover:text-foreground"
                              onClick={() => void handleSubmit(prompt)}
                            >
                              {prompt}
                            </Button>
                          ))}
                        </div>
                      </EmptyContent>
                    )}
                  </Empty>
                </MessageScrollerItem>
              )}

              {messages.map((message) => {
                const isUser = message.role === "user"
                return (
                  <MessageScrollerItem
                    key={message.id}
                    messageId={message.id}
                    scrollAnchor={isUser}
                  >
                    <Message align={isUser ? "end" : "start"}>
                      <MessageContent className={isUser ? "items-end" : "max-w-[min(56rem,100%)]"}>
                        <Bubble
                          variant={isUser ? "secondary" : "ghost"}
                          align={isUser ? "end" : "start"}
                          className={
                            isUser
                              ? "max-w-[min(42rem,85%)]"
                              : "max-w-full"
                          }
                        >
                          <BubbleContent
                            className={
                              isUser
                                ? undefined
                                : "w-full max-w-none p-0"
                            }
                          >
                            {isUser ? (
                              <p className="text-sm leading-relaxed">
                                {message.content}
                              </p>
                            ) : (
                              <MarkdownContent>
                                {message.content}
                              </MarkdownContent>
                            )}
                          </BubbleContent>
                        </Bubble>

                        {!isUser &&
                          ((withoutFinalSteps(message.steps)?.length ?? 0) >
                            0 ||
                            message.usage) && (
                            <StepTimeline
                              steps={withoutFinalSteps(message.steps) ?? []}
                              iterations={message.iterations}
                              runLog={runLogForMessage(
                                message,
                                sessionDetail?.run_logs,
                              )}
                            />
                          )}
                      </MessageContent>
                    </Message>
                  </MessageScrollerItem>
                )
              })}

              {isStreaming && (
                <MessageScrollerItem messageId="streaming">
                  <div className="flex flex-col gap-3">
                    <Marker role="status">
                      <MarkerIcon>
                        <Spinner />
                      </MarkerIcon>
                      <MarkerContent>Working…</MarkerContent>
                    </Marker>
                    <StepTimeline
                      steps={steps.filter((step) => step.type !== "final")}
                      isStreaming
                    />
                  </div>
                </MessageScrollerItem>
              )}
            </MessageScrollerContent>
          </MessageScrollerViewport>
          <MessageScrollerButton />
        </MessageScroller>
      </MessageScrollerProvider>

      <div className="shrink-0 border-t border-border bg-card px-4 py-3 sm:px-8 lg:px-10">
        <InputGroup className="h-auto items-end">
            <InputGroupTextarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={
                isReady
                  ? "Ask about this dataset…"
                  : "Waiting for dataset to finish processing"
              }
              disabled={!isReady || isStreaming}
              rows={1}
              className="min-h-10 py-2.5"
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault()
                  void handleSubmit()
                }
              }}
            />
            <InputGroupAddon align="inline-end" className="py-1.5 pr-1.5">
              {isStreaming ? (
                <InputGroupButton
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={abort}
                >
                  <Square data-icon="inline-start" />
                  Stop
                </InputGroupButton>
              ) : (
                <InputGroupButton
                  type="button"
                  variant="default"
                  size="sm"
                  disabled={!isReady || !question.trim()}
                  onClick={() => void handleSubmit()}
                >
                  <SendHorizontal data-icon="inline-start" />
                  Send
                </InputGroupButton>
              )}
            </InputGroupAddon>
          </InputGroup>
      </div>
    </div>
  )
}
