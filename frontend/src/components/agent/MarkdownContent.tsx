import type { ComponentPropsWithoutRef } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { CodeBlock } from "@/components/agent/CodeBlock"
import { cn } from "@/lib/utils"

interface MarkdownContentProps {
  children: string
  className?: string
}

function PreBlock({ children }: ComponentPropsWithoutRef<"pre">) {
  const child = Array.isArray(children) ? children[0] : children
  if (
    child &&
    typeof child === "object" &&
    "props" in child &&
    child.props &&
    typeof child.props === "object" &&
    "children" in child.props
  ) {
    const code = String(child.props.children).replace(/\n$/, "")
    return <CodeBlock content={code} />
  }

  return (
    <pre className="overflow-x-auto border border-border bg-muted p-3 font-mono text-[0.6875rem] leading-relaxed">
      {children}
    </pre>
  )
}

export function MarkdownContent({ children, className }: MarkdownContentProps) {
  return (
    <div
      className={cn(
        "prose prose-sm dark:prose-invert max-w-none [overflow-wrap:anywhere]",
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre: PreBlock,
          code: ({ className: codeClassName, children: codeChildren, ...props }) => {
            const isBlock = codeClassName?.includes("language-")
            if (isBlock) {
              return (
                <code className={codeClassName} {...props}>
                  {codeChildren}
                </code>
              )
            }

            return (
              <code className={codeClassName} {...props}>
                {codeChildren}
              </code>
            )
          },
          table: ({ children, ...props }) => (
            <div className="my-3 overflow-x-auto">
              <table
                className="w-full border-collapse text-sm"
                {...props}
              >
                {children}
              </table>
            </div>
          ),
          th: ({ children, ...props }) => (
            <th
              className="border border-border bg-muted px-3 py-1.5 text-left font-medium"
              {...props}
            >
              {children}
            </th>
          ),
          td: ({ children, ...props }) => (
            <td
              className="border border-border px-3 py-1.5"
              {...props}
            >
              {children}
            </td>
          ),
          a: ({ children, href, ...props }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline underline-offset-2"
              {...props}
            >
              {children}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
