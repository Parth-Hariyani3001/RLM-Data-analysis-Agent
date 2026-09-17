import { Link } from "react-router-dom"
import { DeleteDatasetDialog } from "@/components/datasets/DeleteDatasetDialog"
import { StatusBadge } from "@/components/datasets/StatusBadge"
import type { Dataset } from "@/types"
import { formatDate, formatNumber } from "@/lib/utils"

interface DatasetCardProps {
  dataset: Dataset
}

export function DatasetCard({ dataset }: DatasetCardProps) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_2.5rem] items-center gap-2 px-4 py-3 hover:bg-primary/5 sm:grid-cols-[minmax(0,1fr)_7rem_7rem_6rem_2.5rem] sm:gap-3">
      <Link
        to={`/datasets/${dataset.id}`}
        className="min-w-0 rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <div className="flex min-w-0 items-center gap-2">
          <p className="truncate text-sm font-medium">{dataset.name}</p>
          <StatusBadge className="sm:hidden" status={dataset.status} />
        </div>
        <p className="mt-0.5 text-xs text-muted-foreground sm:hidden">
          {formatNumber(dataset.row_count)} rows,{" "}
          {formatNumber(dataset.column_count)} columns
        </p>
        <p className="hidden text-xs text-muted-foreground sm:block">
          {formatDate(dataset.created_at)}
        </p>
      </Link>

      <p className="hidden text-right font-mono text-sm tabular-nums sm:block">
        {formatNumber(dataset.row_count)}
      </p>
      <p className="hidden text-right font-mono text-sm tabular-nums sm:block">
        {formatNumber(dataset.column_count)}
      </p>
      <div className="hidden sm:block">
        <StatusBadge status={dataset.status} />
      </div>
      <DeleteDatasetDialog
        datasetId={dataset.id}
        datasetName={dataset.name}
        variant="icon"
      />
    </div>
  )
}
