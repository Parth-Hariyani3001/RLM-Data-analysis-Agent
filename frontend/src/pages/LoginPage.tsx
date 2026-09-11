import { useState } from "react"
import { Navigate } from "react-router-dom"
import { BrainCircuit } from "lucide-react"
import { LoginForm } from "@/components/auth/LoginForm"
import { RegisterForm } from "@/components/auth/RegisterForm"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { isAuthenticated } from "@/lib/auth"

const PROCESS_STEPS = [
  {
    title: "Upload a dataset",
    description: "Drop a CSV or spreadsheet. We index the schema and rows.",
  },
  {
    title: "Ask in plain language",
    description: "Type what you want to know — totals, trends, top values.",
  },
  {
    title: "Review code and results",
    description: "The agent writes Python, runs it, and explains what it found.",
  },
] as const

function AgentPreview() {
  return (
    <div className="relative hidden flex-col justify-center gap-8 bg-muted/30 p-8 md:flex">
      <div className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold tracking-tight">
          From spreadsheet to answer
        </h2>
        <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
          Upload tabular data, ask a question, and follow the agent as it
          writes and runs analysis code.
        </p>
      </div>

      <ol className="flex flex-col gap-4">
        {PROCESS_STEPS.map((step, index) => (
          <li key={step.title} className="flex gap-3">
            <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-medium text-primary">
              {index + 1}
            </span>
            <div className="flex flex-col gap-0.5">
              <span className="text-sm font-medium">{step.title}</span>
              <span className="text-sm text-muted-foreground">
                {step.description}
              </span>
            </div>
          </li>
        ))}
      </ol>

      <div className="rounded-lg border border-border/50 bg-background/50 p-5 font-mono text-xs leading-relaxed">
        <p className="mb-3 font-sans text-xs text-muted-foreground">
          Example query
        </p>
        <pre className="text-foreground/90">{`df.groupby("region")["revenue"]
  .sum()
  .nlargest(5)`}</pre>
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
    <div className="workspace-bg flex min-h-screen flex-col items-center justify-center p-6 md:p-10">
      <div className="page-enter w-full max-w-md md:max-w-3xl">
        <Card className="overflow-hidden py-0">
          <CardContent className="grid p-0 md:grid-cols-2">
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="flex min-w-0 flex-col"
            >
              <CardHeader className="gap-4 border-b border-border/40 px-6 pt-6 pb-4 md:px-8">
                <div className="flex items-center gap-2.5">
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
                    <BrainCircuit />
                  </div>
                  <CardTitle className="text-base">RLM Agent</CardTitle>
                </div>

                <TabsList variant="line">
                  <TabsTrigger value="login">Sign in</TabsTrigger>
                  <TabsTrigger value="register">Register</TabsTrigger>
                </TabsList>
              </CardHeader>

              <div className="px-6 py-6 md:px-8">
                <TabsContent value="login">
                  <LoginForm />
                </TabsContent>
                <TabsContent value="register">
                  <RegisterForm onSuccess={() => setActiveTab("login")} />
                </TabsContent>
              </div>
            </Tabs>
            <AgentPreview />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
