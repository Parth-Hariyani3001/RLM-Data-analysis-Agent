import { useEffect, useMemo, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import ReactMarkdown from "react-markdown"
import {
  BrainCircuit,
  ChevronDown,
  MessageSquarePlus,
  SendHorizontal,
  Square,
} from "lucide-react"
import { toast } from "sonner"
import { StepTimeline } from "@/components/agent/StepTimeline"
import { RunLogsPanel } from "@/components/agent/RunLogsPanel"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
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
import {
  Message,
  MessageAvatar,
  MessageContent,
  MessageFooter,
} from "@/components/ui/message"
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
import type { ChatMessage, Dataset } from "@/types"

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
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border border-border/50 bg-card/40">
      <div className="flex items-center justify-between gap-3 px-4 py-3 sm:px-5">
        <div className="min-w-0">
          <h2 className="truncate text-sm font-medium tracking-tight">
            {activeSession?.title ?? "New chat"}
          </h2>
          <p className="truncate text-xs text-muted-foreground">
            {dataset.name}
          </p>
        </div>

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
              <span className="max-w-[8rem] truncate">
                {activeSession?.title ?? "Chats"}
              </span>
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

      {activeSessionId && (
        <RunLogsPanel logs={sessionDetail?.run_logs ?? []} />
      )}

      <MessageScrollerProvider autoScroll>
        <MessageScroller className="min-h-0 flex-1">
          <MessageScrollerViewport>
            <MessageScrollerContent className="mx-auto w-full max-w-2xl px-4 py-5 sm:px-5">
              {showEmpty && (
                <MessageScrollerItem messageId="empty">
                  <Empty className="border-0 bg-transparent py-10">
                    <EmptyHeader>
                      <EmptyTitle>
                        {isReady
                          ? `Ask about ${dataset.name}`
                          : "Chat is locked"}
                      </EmptyTitle>
                      <EmptyDescription>
                        {isReady
                          ? "The agent writes and runs Python against this dataset."
                          : "Chat opens once ingestion finishes."}
                      </EmptyDescription>
                    </EmptyHeader>
                    {isReady && (
                      <EmptyContent className="items-stretch">
                        <div className="flex w-full flex-col gap-1">
                          {SUGGESTED_PROMPTS.map((prompt) => (
                            <Button
                              key={prompt}
                              type="button"
                              variant="ghost"
                              className="h-auto justify-start whitespace-normal px-3 py-2.5 text-left text-sm leading-snug text-muted-foreground hover:text-foreground"
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

              {messages.map((message) => (
                <MessageScrollerItem
                  key={message.id}
                  messageId={message.id}
                  scrollAnchor={message.role === "user"}
                >
                  <Message align={message.role === "user" ? "end" : "start"}>
                    {message.role === "assistant" && (
                      <MessageAvatar>
                        <Avatar className="size-8">
                          <AvatarFallback className="bg-primary/15 text-primary [&_svg]:size-4">
                            <BrainCircuit />
                          </AvatarFallback>
                        </Avatar>
                      </MessageAvatar>
                    )}
                    <MessageContent>
                      <Bubble
                        variant={
                          message.role === "user" ? "default" : "ghost"
                        }
                        align={message.role === "user" ? "end" : "start"}
                        className={
                          message.role === "assistant"
                            ? "max-w-full"
                            : undefined
                        }
                      >
                        <BubbleContent
                          className={
                            message.role === "assistant"
                              ? "w-full max-w-full"
                              : undefined
                          }
                        >
                          {message.role === "assistant" ? (
                            <div className="prose prose-sm max-w-none">
                              <ReactMarkdown>{message.content}</ReactMarkdown>
                            </div>
                          ) : (
                            message.content
                          )}
                        </BubbleContent>
                      </Bubble>

                      {message.role === "assistant" &&
                        (withoutFinalSteps(message.steps)?.length ?? 0) >
                          0 && (
                          <StepTimeline
                            steps={withoutFinalSteps(message.steps) ?? []}
                            collapsible
                          />
                        )}

                      {message.role === "assistant" &&
                        message.iterations != null && (
                          <MessageFooter>
                            {message.iterations} iteration
                            {message.iterations === 1 ? "" : "s"}
                          </MessageFooter>
                        )}
                    </MessageContent>
                  </Message>
                </MessageScrollerItem>
              ))}

              {isStreaming && (
                <MessageScrollerItem messageId="streaming">
                  <div className="flex flex-col gap-3">
                    <Marker role="status">
                      <MarkerIcon>
                        <Spinner />
                      </MarkerIcon>
                      <MarkerContent className="shimmer">
                        Working…
                      </MarkerContent>
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

      <div className="px-4 pb-4 sm:px-5">
        <div className="mx-auto w-full max-w-2xl">
          <InputGroup>
            <InputGroupTextarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder={
                isReady
                  ? "Ask about this dataset…"
                  : "Waiting for dataset to finish processing"
              }
              disabled={!isReady || isStreaming}
              rows={2}
              className="min-h-[4.5rem]"
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault()
                  void handleSubmit()
                }
              }}
            />
            <InputGroupAddon align="block-end" className="justify-end gap-1.5">
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
    </div>
  )
}
