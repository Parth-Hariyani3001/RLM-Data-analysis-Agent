export type DatasetStatus = "pending" | "processing" | "ready" | "failed"
export type DatasetSourceType = "csv" | "xlsx" | "database"
export type JobStatus = "pending" | "running" | "completed" | "failed"
export type JobType = "ingestion" | "analysis"
export type AgentStepType = "think" | "code" | "result" | "final" | "error"
export type ChatMessageRole = "user" | "assistant"

export interface User {
  id: string
  username: string
  full_name: string
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface Dataset {
  id: string
  user_id: string
  name: string
  source_type: DatasetSourceType
  status: DatasetStatus
  row_count: number | null
  column_count: number | null
  schema: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface Job {
  id: string
  user_id: string
  type: JobType
  status: JobStatus
  celery_task_id: string | null
  progress: number
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface UploadDatasetResponse {
  dataset: Dataset
  job: Job
}

export interface AgentStep {
  type: AgentStepType
  content: string
  iteration: number
}

export interface AgentStepEvent {
  event: "step"
  type: AgentStepType
  content: string
  iteration: number
}

export interface AgentFinalEvent {
  event: "final"
  answer: string
  iterations: number
  steps: AgentStep[]
  session_id?: string
  usage?: AgentUsageSummary
}

export interface AgentErrorEvent {
  event: "error"
  message: string
  status_code?: number
}

export type AgentStreamEvent = AgentStepEvent | AgentFinalEvent | AgentErrorEvent

export interface AgentUsageSummary {
  model?: string | null
  iterations: number
  llm_calls: number
  tool_calls: number
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  events: RunLogEvent[]
}

export interface RunLogEvent {
  type: string
  iteration?: number
  model?: string | null
  name?: string
  content?: string
  prompt_tokens?: number
  completion_tokens?: number
  total_tokens?: number
  [key: string]: unknown
}

export interface ChatSession {
  id: string
  user_id: string
  dataset_id: string
  title: string | null
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  role: ChatMessageRole
  content: string
  steps?: AgentStep[]
  iterations?: number
  session_id?: string
  created_at?: string
}

export interface ChatRunLog {
  id: string
  session_id: string
  message_id: string | null
  model: string | null
  iterations: number
  llm_calls: number
  tool_calls: number
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  events: RunLogEvent[]
  created_at: string
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[]
  run_logs?: ChatRunLog[]
}
