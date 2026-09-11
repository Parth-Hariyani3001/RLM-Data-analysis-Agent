import { apiRequest } from "@/api/client"
import type { ChatSession, ChatSessionDetail } from "@/types"

export async function listChatSessions(
  datasetId: string,
): Promise<ChatSession[]> {
  return apiRequest<ChatSession[]>(`/datasets/${datasetId}/sessions`)
}

export async function createChatSession(
  datasetId: string,
): Promise<ChatSession> {
  return apiRequest<ChatSession>(`/datasets/${datasetId}/sessions`, {
    method: "POST",
  })
}

export async function getChatSession(
  datasetId: string,
  sessionId: string,
): Promise<ChatSessionDetail> {
  return apiRequest<ChatSessionDetail>(
    `/datasets/${datasetId}/sessions/${sessionId}`,
  )
}

export async function deleteChatSession(
  datasetId: string,
  sessionId: string,
): Promise<void> {
  return apiRequest<void>(`/datasets/${datasetId}/sessions/${sessionId}`, {
    method: "DELETE",
  })
}
