import { apiRequest } from "../../shared/api";
import type { User } from "../../entities/user/types";

export type LoginRequest = {
  login: string;
  password: string;
};

export type RegisterRequest = {
  login: string;
  password: string;
  name: string;
};

export function getCurrentUser(): Promise<User> {
  return apiRequest<User>("/auth/me");
}

export function login(payload: LoginRequest): Promise<User> {
  return apiRequest<User>("/auth/login", {
    method: "POST",
    body: payload
  });
}

export function register(payload: RegisterRequest): Promise<User> {
  return apiRequest<User>("/auth/register", {
    method: "POST",
    body: payload
  });
}

export function logout(): Promise<void> {
  return apiRequest<void>("/auth/logout", {
    method: "POST"
  });
}
