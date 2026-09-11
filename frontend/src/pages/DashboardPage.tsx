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
      <header className="flex flex-col gap-4">
        <div className="max-w-lg">
          <h1 className="text-2xl font-semibold tracking-tight">
            Your data workspace
          </h1>
          <p className="mt-1.5 text-[0.9375rem] leading-relaxed text-muted-foreground">
            Upload a spreadsheet and ask questions in plain language. The agent
            writes code, inspects results, and shows its reasoning as it works.
          </p>
        </div>

        {datasets && datasets.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <span className="stat-chip">
              <strong>{datasets.length}</strong> dataset{datasets.length === 1 ? "" : "s"}
            </span>
            <span className="stat-chip">
              <strong>{formatNumber(totalRows)}</strong> total rows
            </span>
          </div>
        )}
      </header>

      <UploadZone onUpload={handleUpload} isUploading={isUploading} />

      <section>
        <h2 className="mb-4 text-sm font-medium text-muted-foreground">
          {datasets && datasets.length > 0
            ? "Recent datasets"
            : "No datasets yet"}
        </h2>

        {isLoading ? (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 3 }).map((_, index) => (
              <Skeleton key={index} className="h-[4.5rem] rounded-lg" />
            ))}
          </div>
        ) : datasets && datasets.length > 0 ? (
          <div className="panel overflow-hidden">
            <div className="divide-y divide-border/40">
              {datasets.map((dataset) => (
                <DatasetCard key={dataset.id} dataset={dataset} />
              ))}
            </div>
          </div>
        ) : (
          <div className="panel-inset px-6 py-10 text-center">
            <p className="text-sm text-muted-foreground">
              Upload a CSV or XLSX file above to create your first dataset.
            </p>
          </div>
        )}
      </section>
    </div>
  )
}
