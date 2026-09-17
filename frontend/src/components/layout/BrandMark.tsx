import { Link } from "react-router-dom"
import { cn } from "@/lib/utils"

function BarMark({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden
      viewBox="0 0 16 16"
      className={cn("size-4 shrink-0 text-primary", className)}
    >
      <rect
        x="1"
        y="1"
        width="14"
        height="14"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.25"
      />
      <rect x="3.25" y="3.5" width="9.5" height="2" fill="currentColor" opacity="0.3" />
      <rect x="3.25" y="7" width="9.5" height="2" fill="currentColor" opacity="0.6" />
      <rect x="3.25" y="10.5" width="9.5" height="2" fill="currentColor" />
    </svg>
  )
}

interface BrandMarkProps {
  to?: string
  className?: string
}

export function BrandMark({ to = "/", className }: BrandMarkProps) {
  const content = (
    <>
      <BarMark />
      <span className="text-[0.9375rem] font-semibold tracking-tight">RLM</span>
      <span className="text-[0.9375rem] text-muted-foreground">agent</span>
    </>
  )

  if (!to) {
    return (
      <span className={cn("inline-flex items-center gap-2", className)}>
        {content}
      </span>
    )
  }

  return (
    <Link
      to={to}
      className={cn(
        "inline-flex items-center gap-2 rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-ring",
        className,
      )}
    >
      {content}
    </Link>
  )
}
