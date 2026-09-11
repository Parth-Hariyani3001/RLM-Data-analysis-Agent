import { useMemo } from "react"
import { Link, useLocation, useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, Columns3, Rows3 } from "lucide-react"
import { ChatPanel } from "@/components/agent/ChatPanel"
import { DeleteDatasetDialog } from "@/components/datasets/DeleteDatasetDialog"
import { SchemaTable } from "@/components/datasets/SchemaTable"
import { StatusBadge } from "@/components/datasets/StatusBadge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { useDataset } from "@/hooks/useDatasets"
import { useJob } from "@/hooks/useJobs"
import { formatDate, formatNumber } from "@/lib/utils"

export function DatasetPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const jobId = (location.state as { jobId?: string } | null)?.jobId
  const { data: dataset, isLoading, isError } = useDataset(id ?? "")
  const { data: job } = useJob(jobId, Boolean(jobId))

  const ingestionProgress = useMemo(() => {
    if (job) return Math.max(0, Math.min(100, job.progress))
    if (dataset?.status === "ready") return 100
    if (dataset?.status === "processing") return 60
    if (dataset?.status === "pending") return 20
    return 0
  }, [dataset?.status, job])

  if (isLoading) {
    return (
      <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-hidden">
        <Skeleton className="h-8 w-48 shrink-0" />
        <Skeleton className="h-4 w-72 shrink-0" />
        <div className="grid min-h-0 flex-1 gap-5 lg:grid-cols-[minmax(0,1fr)_280px]">
          <Skeleton className="h-full min-h-0 rounded-lg" />
          <Skeleton className="h-full min-h-0 rounded-lg" />
        </div>
      </div>
    )
  }

  if (isError || !dataset) {
    return (
      <div className="panel border-destructive/30 bg-destructive/5 px-8 py-10 text-center">
        <p className="text-sm">This dataset could not be found.</p>
        <Link
          to="/"
          className="mt-4 inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
        >
          Back to datasets
        </Link>
      </div>
    )
  }

  const isProcessing = dataset.status !== "ready"

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden">
      <header className="flex shrink-0 flex-col gap-3">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="size-3.5" />
          All datasets
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-3">
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <h1 className="text-xl font-semibold tracking-tight">
                {dataset.name}
              </h1>
              <StatusBadge status={dataset.status} />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="stat-chip">
                <Rows3 className="size-3.5" />
                <strong>{formatNumber(dataset.row_count)}</strong> rows
              </span>
              <span className="stat-chip">
                <Columns3 className="size-3.5" />
                <strong>{formatNumber(dataset.column_count)}</strong> columns
              </span>
              <span className="stat-chip">
                Uploaded {formatDate(dataset.created_at)}
              </span>
            </div>
          </div>

          <DeleteDatasetDialog
            datasetId={dataset.id}
            datasetName={dataset.name}
            variant="button"
            onDeleted={() => navigate("/")}
          />
        </div>
      </header>

      <div className="grid min-h-0 flex-1 gap-4 [grid-template-rows:minmax(0,1fr)_minmax(0,12rem)] lg:grid-cols-[minmax(0,1fr)_260px] lg:[grid-template-rows:minmax(0,1fr)]">
        <ChatPanel dataset={dataset} />

        <aside className="flex min-h-0 flex-col gap-4 overflow-hidden">
          {isProcessing && (
            <div className="panel shrink-0 p-4">
              <p className="text-sm font-medium">Ingestion</p>
              <Progress value={ingestionProgress} className="mt-3" />
              <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                <span>{job?.status ?? dataset.status}</span>
                <span>{ingestionProgress}%</span>
              </div>
              {(dataset.error_message || job?.error_message) && (
                <p className="mt-3 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
                  {dataset.error_message || job?.error_message}
                </p>
              )}
            </div>
          )}

          <div className="panel flex min-h-0 flex-1 flex-col overflow-hidden p-4">
            <p className="shrink-0 text-sm font-medium">Schema</p>
            <div className="mt-3 min-h-0 flex-1 overflow-hidden">
              <SchemaTable schema={dataset.schema} />
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
