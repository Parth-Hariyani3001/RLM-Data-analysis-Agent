import { useState } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import {
  Field,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useRegister } from "@/hooks/useAuth"
import { ApiError } from "@/api/client"

interface RegisterFormProps {
  onSuccess?: () => void
}

export function RegisterForm({ onSuccess }: RegisterFormProps) {
  const register = useRegister()
  const [username, setUsername] = useState("")
  const [fullName, setFullName] = useState("")
  const [password, setPassword] = useState("")

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()

    try {
      await register.mutateAsync({ username, password, fullName })
      toast.success("Account created.")
      onSuccess?.()
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Registration failed"
      toast.error(message)
    }
  }

  return (
    <form onSubmit={(event) => void handleSubmit(event)}>
      <FieldGroup className="gap-4">
        <Field>
          <FieldLabel htmlFor="register-username">Username</FieldLabel>
          <Input
            id="register-username"
            className="h-10"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            required
          />
        </Field>

        <Field>
          <FieldLabel htmlFor="register-full-name">Full name</FieldLabel>
          <Input
            id="register-full-name"
            className="h-10"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            autoComplete="name"
            required
          />
        </Field>

        <Field>
          <FieldLabel htmlFor="register-password">Password</FieldLabel>
          <Input
            id="register-password"
            className="h-10"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="new-password"
            required
          />
        </Field>

        <Field className="pt-1">
          <Button
            type="submit"
            className="h-10 w-full"
            disabled={register.isPending}
          >
            {register.isPending && <Spinner data-icon="inline-start" />}
            {register.isPending ? "Creating account…" : "Create account"}
          </Button>
        </Field>
      </FieldGroup>
    </form>
  )
}
