import { Link } from "react-router-dom"
import { ChevronRight, FileSpreadsheet } from "lucide-react"
import { DeleteDatasetDialog } from "@/components/datasets/DeleteDatasetDialog"
import { StatusBadge } from "@/components/datasets/StatusBadge"
import type { Dataset } from "@/types"
import { formatDate, formatNumber } from "@/lib/utils"

interface DatasetCardProps {
  dataset: Dataset
}

export function DatasetCard({ dataset }: DatasetCardProps) {
  return (
    <div className="data-row flex items-center gap-2 px-3 py-3 sm:gap-3 sm:px-5 sm:py-4">
      <Link
        to={`/datasets/${dataset.id}`}
        className="group flex min-w-0 flex-1 items-center gap-4"
      >
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-warm/10 text-warm">
          <FileSpreadsheet className="size-4" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2.5">
            <p className="truncate text-sm font-medium">{dataset.name}</p>
            <StatusBadge status={dataset.status} />
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {formatNumber(dataset.row_count)} rows ·{" "}
            {formatNumber(dataset.column_count)} columns ·{" "}
            {formatDate(dataset.created_at)}
          </p>
        </div>

        <ChevronRight className="size-4 shrink-0 text-muted-foreground/50 transition-transform group-hover:translate-x-0.5 group-hover:text-muted-foreground" />
      </Link>

      <DeleteDatasetDialog
        datasetId={dataset.id}
        datasetName={dataset.name}
        variant="icon"
      />
    </div>
  )
}
