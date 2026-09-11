import { apiRequest } from "@/api/client"
import type { Token, User } from "@/types"

export async function login(username: string, password: string): Promise<Token> {
  return apiRequest<Token>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  })
}

export async function register(
  username: string,
  password: string,
  fullName: string,
): Promise<User> {
  return apiRequest<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      username,
      password,
      full_name: fullName,
    }),
  })
}

export async function getMe(): Promise<User> {
  return apiRequest<User>("/auth/me")
}
