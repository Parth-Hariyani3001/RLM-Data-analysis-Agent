import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as datasetsApi from "@/api/datasets"

export function useDatasets() {
  return useQuery({
    queryKey: ["datasets"],
    queryFn: datasetsApi.listDatasets,
  })
}

export function useDataset(id: string) {
  return useQuery({
    queryKey: ["datasets", id],
    queryFn: () => datasetsApi.getDataset(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === "pending" || status === "processing") {
        return 2000
      }
      return false
    },
  })
}

export function useUploadDataset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => datasetsApi.uploadDataset(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] })
    },
  })
}

export function useDeleteDataset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => datasetsApi.deleteDataset(id),
    onSuccess: (_data, id) => {
      queryClient.removeQueries({ queryKey: ["datasets", id] })
      queryClient.invalidateQueries({ queryKey: ["datasets"] })
    },
  })
}
