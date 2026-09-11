import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

interface SchemaTableProps {
  schema: Record<string, unknown> | null
}

function getColumns(schema: Record<string, unknown> | null): Array<{
  name: string
  type: string
}> {
  if (!schema) return []

  if (Array.isArray(schema.columns)) {
    return schema.columns.map((column) => {
      if (typeof column === "string") {
        return { name: column, type: "unknown" }
      }
      if (column && typeof column === "object") {
        const entry = column as Record<string, unknown>
        return {
          name: String(entry.name ?? entry.column ?? "column"),
          type: String(entry.type ?? entry.dtype ?? "unknown"),
        }
      }
      return { name: "column", type: "unknown" }
    })
  }

  return Object.entries(schema).map(([name, value]) => ({
    name,
    type:
      typeof value === "string"
        ? value
        : typeof value === "object" && value && "type" in value
          ? String((value as Record<string, unknown>).type)
          : "unknown",
  }))
}

export function SchemaTable({ schema }: SchemaTableProps) {
  const columns = getColumns(schema)

  if (columns.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">
        Schema appears after ingestion completes.
      </p>
    )
  }

  return (
    <div className="scrollbar-invisible h-full min-h-0 overflow-y-auto rounded-md border border-border/30">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="h-8 text-xs">Column</TableHead>
            <TableHead className="h-8 text-xs">Type</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {columns.map((column) => (
            <TableRow key={column.name} className="data-row">
              <TableCell className="py-2 text-xs font-medium">
                {column.name}
              </TableCell>
              <TableCell className="py-2 font-mono text-[0.6875rem] text-muted-foreground">
                {column.type}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
