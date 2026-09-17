import { useState } from "react"
import { Navigate } from "react-router-dom"
import { LoginForm } from "@/components/auth/LoginForm"
import { RegisterForm } from "@/components/auth/RegisterForm"
import { BrandMark } from "@/components/layout/BrandMark"
import { ThemeToggle } from "@/components/layout/ThemeToggle"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { isAuthenticated } from "@/lib/auth"

function PrintoutPreview() {
  return (
    <div className="printout relative hidden min-h-full flex-col justify-center overflow-hidden border-r border-border p-8 md:flex lg:p-12">
      <div className="flex max-w-md flex-col gap-6">
        <div>
          <p className="text-sm text-muted-foreground">Sample run</p>
          <h2 className="mt-2 text-2xl leading-tight font-semibold tracking-tight">
            Ask the table. Read the code. Keep the answer.
          </h2>
        </div>

        <div className="border border-border bg-card/90 p-4 shadow-[4px_4px_0_0_var(--bar)]">
          <div className="flex flex-col gap-4 font-mono text-[0.8125rem] leading-6">
            <div className="flex flex-col gap-1">
              <p className="text-muted-foreground">you</p>
              <p>Which five regions brought in the most revenue last quarter?</p>
            </div>
            <div className="flex flex-col gap-1 border-t border-border pt-4">
              <p className="text-muted-foreground">rlm</p>
              <pre className="whitespace-pre-wrap text-foreground">{`df.groupby("region")["revenue"]
  .sum()
  .nlargest(5)`}</pre>
              <p>
                West leads at $4.1M, then Northeast, South, Midwest, and
                Mountain.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function LoginPage() {
  const [activeTab, setActiveTab] = useState("login")

  if (isAuthenticated()) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="flex min-h-svh bg-background text-foreground">
      <div className="page-enter grid min-h-svh w-full md:grid-cols-2">
        <PrintoutPreview />

        <div className="flex flex-col justify-center bg-card px-6 py-10 sm:px-10">
          <div className="flex items-center justify-between gap-3">
            <BrandMark />
            <ThemeToggle />
          </div>
          <p className="mt-6 max-w-sm text-sm leading-relaxed text-muted-foreground">
            Sign in to upload spreadsheets and run questions against them.
          </p>

          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="mt-8 w-full max-w-sm"
          >
            <TabsList variant="line">
              <TabsTrigger
                value="login"
                className="text-muted-foreground data-active:text-foreground"
              >
                Sign in
              </TabsTrigger>
              <TabsTrigger
                value="register"
                className="text-muted-foreground data-active:text-foreground"
              >
                Create account
              </TabsTrigger>
            </TabsList>
            <div className="mt-6">
              <TabsContent value="login">
                <LoginForm />
              </TabsContent>
              <TabsContent value="register">
                <RegisterForm onSuccess={() => setActiveTab("login")} />
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
    </div>
  )
}
