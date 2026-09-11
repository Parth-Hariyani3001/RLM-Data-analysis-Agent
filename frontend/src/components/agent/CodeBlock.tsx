import { cn } from "@/lib/utils"

interface CodeBlockProps {
  content: string
  className?: string
}

export function CodeBlock({ content, className }: CodeBlockProps) {
  return (
    <pre
      className={cn(
        "overflow-x-auto rounded-md border border-border/50 bg-muted p-3 font-mono text-[0.6875rem] leading-relaxed text-foreground",
        className,
      )}
    >
      <code>{content}</code>
    </pre>
  )
}
