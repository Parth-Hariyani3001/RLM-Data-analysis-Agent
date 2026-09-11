import { apiRequest } from "@/api/client"
import type { Dataset, UploadDatasetResponse } from "@/types"

export async function listDatasets(): Promise<Dataset[]> {
  return apiRequest<Dataset[]>("/datasets")
}

export async function getDataset(id: string): Promise<Dataset> {
  return apiRequest<Dataset>(`/datasets/${id}`)
}

export async function uploadDataset(file: File): Promise<UploadDatasetResponse> {
  const formData = new FormData()
  formData.append("file", file)

  return apiRequest<UploadDatasetResponse>("/datasets", {
    method: "POST",
    body: formData,
  })
}

export async function deleteDataset(id: string): Promise<void> {
  return apiRequest<void>(`/datasets/${id}`, {
    method: "DELETE",
  })
}
