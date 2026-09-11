import { useCallback, useRef, useState } from "react"
import { CloudUpload, FileSpreadsheet } from "lucide-react"
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
        "panel relative overflow-hidden transition-colors duration-200",
        isDragging && "border-primary/40 bg-primary/5",
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
      <div className="flex flex-col items-center gap-5 px-6 py-10 sm:flex-row sm:items-center sm:justify-between sm:gap-8 sm:py-8">
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-center">
          <div
            className={cn(
              "flex size-12 items-center justify-center rounded-xl transition-colors",
              isDragging
                ? "bg-primary/15 text-primary"
                : "bg-warm/10 text-warm",
            )}
          >
            {isUploading ? (
              <Spinner className="size-5" />
            ) : (
              <CloudUpload className="size-5" />
            )}
          </div>

          <div className="text-center sm:text-left">
            <h3 className="text-base font-medium">
              {isUploading ? "Uploading…" : "Add a dataset"}
            </h3>
            <p className="mt-1 max-w-sm text-sm leading-relaxed text-muted-foreground">
              Drop a CSV or XLSX file here, or browse from your computer.
              Max 500 MB.
            </p>
            <div className="mt-2 flex items-center justify-center gap-1.5 text-xs text-muted-foreground sm:justify-start">
              <FileSpreadsheet className="size-3.5" />
              <span>CSV, XLSX</span>
            </div>
          </div>
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
            variant="secondary"
            onClick={() => inputRef.current?.click()}
          >
            {isUploading ? "Uploading…" : "Browse files"}
          </Button>
        </div>
      </div>
    </div>
  )
}
