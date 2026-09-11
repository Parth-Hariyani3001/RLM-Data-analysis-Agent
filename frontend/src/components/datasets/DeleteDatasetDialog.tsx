import { useState } from "react"
import { Trash2 } from "lucide-react"
import { toast } from "sonner"
import { ApiError } from "@/api/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Spinner } from "@/components/ui/spinner"
import { useDeleteDataset } from "@/hooks/useDatasets"
import { cn } from "@/lib/utils"

interface DeleteDatasetDialogProps {
  datasetId: string
  datasetName: string
  variant?: "icon" | "button"
  className?: string
  onDeleted?: () => void
}

export function DeleteDatasetDialog({
  datasetId,
  datasetName,
  variant = "icon",
  className,
  onDeleted,
}: DeleteDatasetDialogProps) {
  const [open, setOpen] = useState(false)
  const deleteDataset = useDeleteDataset()
  const isDeleting = deleteDataset.isPending

  const handleDelete = async () => {
    try {
      await deleteDataset.mutateAsync(datasetId)
      toast.success("Dataset deleted")
      setOpen(false)
      onDeleted?.()
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Could not delete dataset. Please try again."
      toast.error(message)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {variant === "icon" ? (
        <DialogTrigger
          render={
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label={`Delete ${datasetName}`}
              className={cn(
                "shrink-0 text-muted-foreground hover:text-destructive",
                className,
              )}
            />
          }
        >
          <Trash2 />
        </DialogTrigger>
      ) : (
        <DialogTrigger
          render={
            <Button
              type="button"
              variant="outline"
              size="sm"
              className={className}
            />
          }
        >
          <Trash2 data-icon="inline-start" />
          Delete dataset
        </DialogTrigger>
      )}

      <DialogContent showCloseButton={!isDeleting}>
        <DialogHeader>
          <DialogTitle>Delete dataset</DialogTitle>
          <DialogDescription>
            Delete {datasetName}? This removes the file and cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <DialogClose
            render={<Button variant="outline" disabled={isDeleting} />}
          >
            Cancel
          </DialogClose>
          <Button
            type="button"
            variant="destructive"
            disabled={isDeleting}
            onClick={() => void handleDelete()}
          >
            {isDeleting ? (
              <Spinner data-icon="inline-start" />
            ) : (
              <Trash2 data-icon="inline-start" />
            )}
            Delete dataset
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
