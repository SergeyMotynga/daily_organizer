import { useQuery } from "@tanstack/react-query";

import { ApiError } from "../../shared/api";
import { getCurrentUser } from "./api";

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
