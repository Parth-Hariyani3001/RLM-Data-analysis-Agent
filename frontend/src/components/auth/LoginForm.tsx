import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import {
  Field,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useLogin } from "@/hooks/useAuth"
import { ApiError } from "@/api/client"

export function LoginForm() {
  const navigate = useNavigate()
  const login = useLogin()
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()

    try {
      await login.mutateAsync({ username, password })
      navigate("/")
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Login failed"
      toast.error(message)
    }
  }

  return (
    <form onSubmit={(event) => void handleSubmit(event)}>
      <FieldGroup className="gap-4">
        <Field>
          <FieldLabel htmlFor="login-username">Username</FieldLabel>
          <Input
            id="login-username"
            className="h-10"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            required
          />
        </Field>

        <Field>
          <FieldLabel htmlFor="login-password">Password</FieldLabel>
          <Input
            id="login-password"
            className="h-10"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />
        </Field>

        <Field className="pt-1">
          <Button
            type="submit"
            className="h-10 w-full"
            disabled={login.isPending}
          >
            {login.isPending && <Spinner data-icon="inline-start" />}
            {login.isPending ? "Signing in…" : "Sign in"}
          </Button>
        </Field>
      </FieldGroup>
    </form>
  )
}
