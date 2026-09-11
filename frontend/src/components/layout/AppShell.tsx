import { Link, Outlet, useLocation } from "react-router-dom"
import { BrainCircuit, Database, LogOut, UserRound } from "lucide-react"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useCurrentUser, useLogout } from "@/hooks/useAuth"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { href: "/", label: "Datasets", icon: Database },
]

export function AppShell() {
  const location = useLocation()
  const { data: user } = useCurrentUser()
  const logout = useLogout()

  return (
    <div className="workspace-bg flex h-svh flex-col overflow-hidden text-foreground">
      <header className="sticky top-0 z-40 shrink-0 border-b border-border/40 bg-background/70 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-5">
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="flex size-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
                <BrainCircuit className="size-4" />
              </div>
              <span className="text-sm font-semibold tracking-tight">
                RLM Agent
              </span>
            </Link>

            <nav className="hidden items-center sm:flex">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon
                const active = location.pathname === item.href
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors",
                      active
                        ? "bg-primary/12 text-primary"
                        : "text-muted-foreground hover:text-foreground",
                    )}
                  >
                    <Icon className="size-3.5" />
                    {item.label}
                  </Link>
                )
              })}
            </nav>
          </div>

          <div className="flex items-center gap-1.5">
            <ThemeToggle />
            <DropdownMenu>
              <DropdownMenuTrigger className="inline-flex items-center gap-2 rounded-md px-2 py-1 text-sm transition-colors hover:bg-muted/60">
                <Avatar className="size-7">
                  <AvatarFallback className="bg-primary/15 text-xs text-primary">
                    {user?.username?.slice(0, 2).toUpperCase() ?? "U"}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden text-sm text-muted-foreground sm:inline">
                  {user?.username}
                </span>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44">
                <DropdownMenuItem disabled>
                  <UserRound className="size-4" />
                  {user?.full_name || user?.username}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={logout}>
                  <LogOut className="size-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <main className="relative mx-auto flex min-h-0 w-full max-w-6xl flex-1 flex-col px-5 py-6">
        <div className="page-enter flex min-h-0 flex-1 flex-col">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
