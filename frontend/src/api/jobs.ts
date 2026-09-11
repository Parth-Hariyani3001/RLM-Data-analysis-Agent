import { apiRequest } from "@/api/client"
import type { Job } from "@/types"

export async function getJob(id: string): Promise<Job> {
  return apiRequest<Job>(`/jobs/${id}`)
}
