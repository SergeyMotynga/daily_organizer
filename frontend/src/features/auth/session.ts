import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../../shared/api";
import { getCurrentUser, login, logout, register } from "./api";

export const authQueryKeys = {
  currentUser: ["auth", "current-user"] as const
};

export function isUnauthorizedError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

export function useCurrentUserQuery() {
  return useQuery({
    queryKey: authQueryKeys.currentUser,
    queryFn: getCurrentUser,
    retry: false,
    staleTime: 60_000,
    refetchOnWindowFocus: false
  });
}

export function useLoginMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: login,
    onSuccess: (user) => {
      queryClient.setQueryData(authQueryKeys.currentUser, user);
    }
  });
}

export function useRegisterMutation() {
  return useMutation({
    mutationFn: register
  });
}

export function useLogoutMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: logout,
    onSettled: async () => {
      await queryClient.cancelQueries({ queryKey: authQueryKeys.currentUser });
      queryClient.removeQueries({ queryKey: authQueryKeys.currentUser });
    }
  });
}

export function getAuthErrorMessage(error: unknown): string {
  const fallbackMessage = "Что-то пошло не так. Попробуйте еще раз.";

  if (!(error instanceof ApiError)) {
    return fallbackMessage;
  }

  const messagesByCode: Record<string, string> = {
    INVALID_CREDENTIALS: "Неверный login или пароль. Login и пароль чувствительны к регистру.",
    LOGIN_ALREADY_EXISTS:
      "Пользователь с таким login уже существует. Login чувствителен к регистру.",
    WEAK_PASSWORD: "Пароль должен быть 8-30 символов, с латинской буквой и цифрой, без пробелов."
  };

  return messagesByCode[error.code] ?? fallbackMessage;
}
