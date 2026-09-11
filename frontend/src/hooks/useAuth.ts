import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as authApi from "@/api/auth"
import { clearToken, isAuthenticated, setToken } from "@/lib/auth"

export function useCurrentUser() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.getMe,
    enabled: isAuthenticated(),
    retry: false,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      authApi.login(username, password),
    onSuccess: (data) => {
      setToken(data.access_token)
      queryClient.invalidateQueries({ queryKey: ["auth"] })
    },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: ({
      username,
      password,
      fullName,
    }: {
      username: string
      password: string
      fullName: string
    }) => authApi.register(username, password, fullName),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()

  return () => {
    clearToken()
    queryClient.clear()
    window.location.href = "/login"
  }
}
