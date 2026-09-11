import { useQuery } from "@tanstack/react-query"
import * as jobsApi from "@/api/jobs"
import type { JobStatus } from "@/types"

const ACTIVE_STATUSES: JobStatus[] = ["pending", "running"]

export function useJob(id: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ["jobs", id],
    queryFn: () => jobsApi.getJob(id!),
    enabled: Boolean(id) && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status && ACTIVE_STATUSES.includes(status)) {
        return 1500
      }
      return false
    },
  })
}
