import { Outlet, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"
import { LogOut, UserRound } from "lucide-react"
import { BrandMark } from "@/components/layout/BrandMark"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useCurrentUser, useLogout } from "@/hooks/useAuth"

export function AppShell() {
  const location = useLocation()
  const { data: user } = useCurrentUser()
  const logout = useLogout()
  const initials = user?.username?.slice(0, 2).toUpperCase() ?? "U"
  const isWorkspace = location.pathname.startsWith("/datasets/")

  return (
    <div className="flex h-svh flex-col overflow-hidden bg-background text-foreground">
      <header className="shrink-0 border-b-4 border-bar bg-card">
        <div
          className={cn(
            "mx-auto flex h-12 w-full items-center justify-between px-4 sm:px-6",
            isWorkspace ? "max-w-none" : "max-w-5xl",
          )}
        >
          <BrandMark />

          <div className="flex items-center gap-1">
            <ThemeToggle />
            <DropdownMenu>
              <DropdownMenuTrigger className="inline-flex items-center gap-2 rounded-sm px-1.5 py-1 text-sm outline-none hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring">
                <Avatar className="size-6 rounded-sm after:rounded-sm">
                  <AvatarFallback className="rounded-sm bg-bar text-[0.65rem] text-foreground">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden text-sm sm:inline">
                  {user?.username}
                </span>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44">
                <DropdownMenuItem disabled>
                  <UserRound />
                  {user?.full_name || user?.username}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={logout}>
                  <LogOut />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <main
        className={cn(
          "relative mx-auto flex min-h-0 w-full flex-1 flex-col px-4 sm:px-6",
          isWorkspace ? "max-w-none px-3 py-2 sm:px-4" : "max-w-5xl py-6",
        )}
      >
        <div className="page-enter flex min-h-0 flex-1 flex-col">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
