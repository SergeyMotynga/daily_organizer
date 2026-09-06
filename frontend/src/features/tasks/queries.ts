import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { todayQueryKeys } from "../today/queries";
import { createTask, getTaskStatuses } from "./api";

export const taskQueryKeys = {
  statuses: ["tasks", "statuses"] as const
};

export function useTaskStatusesQuery() {
  return useQuery({
    queryKey: taskQueryKeys.statuses,
    queryFn: getTaskStatuses,
    staleTime: 5 * 60_000
  });
}

export function useCreateTaskMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTask,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: todayQueryKeys.all });
    }
  });
}
