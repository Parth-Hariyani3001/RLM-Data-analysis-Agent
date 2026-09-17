import { useCallback, useRef, useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"
import { ApiError } from "@/api/client"

interface UploadZoneProps {
  onUpload: (file: File) => Promise<void>
  isUploading?: boolean
}

const ACCEPTED = ".csv,.xlsx"

export function UploadZone({ onUpload, isUploading = false }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      const file = files?.[0]
      if (!file) return

      const extension = file.name.split(".").pop()?.toLowerCase()
      if (!extension || !["csv", "xlsx"].includes(extension)) {
        toast.error("Only CSV and XLSX files are supported")
        return
      }

      try {
        await onUpload(file)
      } catch (error) {
        const message =
          error instanceof ApiError
            ? error.message
            : "Upload failed. Please try again."
        toast.error(message)
      }
    },
    [onUpload],
  )

  return (
    <div
      className={cn(
        "border border-dashed border-border bg-card px-5 py-6 transition-colors",
        isDragging && "border-primary bg-bar",
      )}
      onDragOver={(event) => {
        event.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(event) => {
        event.preventDefault()
        setIsDragging(false)
        void handleFiles(event.dataTransfer.files)
      }}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-medium">
            {isUploading ? "Uploading…" : "Add a file"}
          </h2>
          <p className="mt-1 max-w-md text-sm leading-relaxed text-muted-foreground">
            Drop a CSV or XLSX here, or browse. Maximum 500 MB.
          </p>
        </div>

        <div className="shrink-0">
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            className="hidden"
            disabled={isUploading}
            onChange={(event) => void handleFiles(event.target.files)}
          />
          <Button
            type="button"
            disabled={isUploading}
            onClick={() => inputRef.current?.click()}
          >
            {isUploading && <Spinner data-icon="inline-start" />}
            {isUploading ? "Uploading…" : "Browse files"}
          </Button>
        </div>
      </div>
    </div>
  )
}
