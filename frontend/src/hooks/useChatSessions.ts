import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as chatsApi from "@/api/chats"

export function useChatSessions(datasetId: string, enabled = true) {
  return useQuery({
    queryKey: ["chat-sessions", datasetId],
    queryFn: () => chatsApi.listChatSessions(datasetId),
    enabled: Boolean(datasetId) && enabled,
  })
}

export function useChatSession(
  datasetId: string,
  sessionId: string | null,
  enabled = true,
) {
  return useQuery({
    queryKey: ["chat-sessions", datasetId, sessionId],
    queryFn: () => chatsApi.getChatSession(datasetId, sessionId!),
    enabled: Boolean(datasetId) && Boolean(sessionId) && enabled,
  })
}

export function useCreateChatSession(datasetId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => chatsApi.createChatSession(datasetId),
    onSuccess: (session) => {
      queryClient.invalidateQueries({
        queryKey: ["chat-sessions", datasetId],
      })
      queryClient.setQueryData(
        ["chat-sessions", datasetId, session.id],
        { ...session, messages: [] },
      )
    },
  })
}

export function useDeleteChatSession(datasetId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) =>
      chatsApi.deleteChatSession(datasetId, sessionId),
    onSuccess: (_data, sessionId) => {
      queryClient.removeQueries({
        queryKey: ["chat-sessions", datasetId, sessionId],
      })
      queryClient.invalidateQueries({
        queryKey: ["chat-sessions", datasetId],
      })
    },
  })
}
