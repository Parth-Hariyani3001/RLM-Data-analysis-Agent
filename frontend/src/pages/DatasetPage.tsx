import { useMemo, useState } from "react"
import { Link, useLocation, useNavigate, useParams } from "react-router-dom"
import { ArrowLeft, PanelRight } from "lucide-react"
import { ChatPanel } from "@/components/agent/ChatPanel"
import { DeleteDatasetDialog } from "@/components/datasets/DeleteDatasetDialog"
import { SchemaTable } from "@/components/datasets/SchemaTable"
import { StatusBadge } from "@/components/datasets/StatusBadge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { useDataset } from "@/hooks/useDatasets"
import { useJob } from "@/hooks/useJobs"
import { formatNumber } from "@/lib/utils"

export function DatasetPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const jobId = (location.state as { jobId?: string } | null)?.jobId
  const { data: dataset, isLoading, isError } = useDataset(id ?? "")
  const { data: job } = useJob(jobId, Boolean(jobId))
  const [schemaOpen, setSchemaOpen] = useState(false)

  const ingestionProgress = useMemo(() => {
    if (job) return Math.max(0, Math.min(100, job.progress))
    if (dataset?.status === "ready") return 100
    if (dataset?.status === "processing") return 60
    if (dataset?.status === "pending") return 20
    return 0
  }, [dataset?.status, job])

  if (isLoading) {
    return (
      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden">
        <Skeleton className="h-8 w-64 shrink-0 rounded-sm" />
        <Skeleton className="min-h-0 flex-1 rounded-sm" />
      </div>
    )
  }

  if (isError || !dataset) {
    return (
      <div className="border border-destructive/30 bg-destructive/5 px-8 py-10">
        <p className="text-sm">This dataset could not be found.</p>
        <Link
          to="/"
          className="mt-4 inline-flex h-9 items-center bg-primary px-4 text-sm font-medium text-primary-foreground"
        >
          Back to datasets
        </Link>
      </div>
    )
  }

  const isProcessing = dataset.status !== "ready"

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden">
      <header className="flex shrink-0 flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-3">
          <Link
            to="/"
            className="inline-flex shrink-0 items-center gap-1.5 text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
          >
            <ArrowLeft className="size-3.5" />
            Datasets
          </Link>
          <h1 className="truncate text-lg font-semibold tracking-tight">
            {dataset.name}
          </h1>
          <StatusBadge status={dataset.status} />
          <p className="hidden truncate text-sm text-muted-foreground md:block">
            {formatNumber(dataset.row_count)} rows,{" "}
            {formatNumber(dataset.column_count)} columns
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-1.5">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setSchemaOpen(true)}
          >
            <PanelRight data-icon="inline-start" />
            Schema
          </Button>
          <DeleteDatasetDialog
            datasetId={dataset.id}
            datasetName={dataset.name}
            variant="button"
            onDeleted={() => navigate("/")}
          />
        </div>
      </header>

      <div className="min-h-0 flex-1">
        <ChatPanel dataset={dataset} />
      </div>

      <Sheet open={schemaOpen} onOpenChange={setSchemaOpen}>
        <SheetContent
          side="right"
          className="w-[min(24rem,100%)] gap-0 p-0 sm:max-w-sm"
        >
          <SheetHeader className="border-b border-border">
            <SheetTitle>Schema</SheetTitle>
            <SheetDescription>
              {formatNumber(dataset.column_count)} columns in {dataset.name}
            </SheetDescription>
          </SheetHeader>
          {isProcessing && (
            <div className="border-b border-border p-4">
              <p className="text-sm font-medium">Ingestion</p>
              <Progress value={ingestionProgress} className="mt-3" />
              <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                <span>{job?.status ?? dataset.status}</span>
                <span>{ingestionProgress}%</span>
              </div>
              {(dataset.error_message || job?.error_message) && (
                <p className="mt-3 bg-destructive/10 px-3 py-2 text-xs text-destructive">
                  {dataset.error_message || job?.error_message}
                </p>
              )}
            </div>
          )}
          <div className="min-h-0 flex-1 overflow-hidden p-4">
            <SchemaTable schema={dataset.schema} />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}
