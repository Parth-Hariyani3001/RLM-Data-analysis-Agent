import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { DatasetCard } from "@/components/datasets/DatasetCard"
import { UploadZone } from "@/components/datasets/UploadZone"
import { Skeleton } from "@/components/ui/skeleton"
import { useDatasets, useUploadDataset } from "@/hooks/useDatasets"
import { formatNumber } from "@/lib/utils"

export function DashboardPage() {
  const navigate = useNavigate()
  const { data: datasets, isLoading } = useDatasets()
  const uploadDataset = useUploadDataset()
  const [isUploading, setIsUploading] = useState(false)

  const totalRows = datasets?.reduce((sum, d) => sum + (d.row_count ?? 0), 0) ?? 0
  const hasDatasets = Boolean(datasets && datasets.length > 0)

  const handleUpload = async (file: File) => {
    setIsUploading(true)
    try {
      const result = await uploadDataset.mutateAsync(file)
      toast.success("Dataset uploaded. Processing started.")
      navigate(`/datasets/${result.dataset.id}`, {
        state: { jobId: result.job.id },
      })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-8 overflow-y-auto">
      <header className="max-w-xl">
        <h1 className="text-[1.75rem] leading-tight font-semibold tracking-tight">
          Datasets
        </h1>
        <p className="mt-2 text-[0.9375rem] leading-relaxed text-muted-foreground">
          Drop a spreadsheet, then ask a question. The agent writes Python
          against the file until it has an answer.
        </p>
        {hasDatasets && (
          <p className="mt-3 text-sm text-muted-foreground">
            {datasets!.length} {datasets!.length === 1 ? "file" : "files"},{" "}
            {formatNumber(totalRows)} rows
          </p>
        )}
      </header>

      <UploadZone onUpload={handleUpload} isUploading={isUploading} />

      <section className="flex min-h-0 flex-col">
        {isLoading ? (
          <div className="flex flex-col gap-px overflow-hidden border border-border">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-12 rounded-none" />
            ))}
          </div>
        ) : hasDatasets ? (
          <div className="overflow-hidden border border-border">
            <div className="hidden grid-cols-[minmax(0,1fr)_7rem_7rem_6rem_2.5rem] gap-3 border-b border-border bg-card px-4 py-2 text-sm text-muted-foreground sm:grid">
              <span>File</span>
              <span className="text-right">Rows</span>
              <span className="text-right">Columns</span>
              <span>Status</span>
              <span className="sr-only">Actions</span>
            </div>
            <div className="greenbar">
              {datasets!.map((dataset) => (
                <DatasetCard key={dataset.id} dataset={dataset} />
              ))}
            </div>
          </div>
        ) : (
          <p className="border border-dashed border-border px-4 py-8 text-sm text-muted-foreground">
            No files yet. Upload a CSV or XLSX to create the first dataset.
          </p>
        )}
      </section>
    </div>
  )
}
