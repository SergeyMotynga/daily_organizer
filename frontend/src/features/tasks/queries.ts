import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { UpdateTaskPayload } from "../../entities/task/types";
import { todayQueryKeys } from "../today/queries";
import { createTask, deleteTask, getTask, getTaskStatuses, updateTask } from "./api";

export const taskQueryKeys = {
  all: ["tasks"] as const,
  statuses: ["tasks", "statuses"] as const,
  detail: (taskId: string) => ["tasks", "detail", taskId] as const
};

export function useTaskStatusesQuery() {
  return useQuery({
    queryKey: taskQueryKeys.statuses,
    queryFn: getTaskStatuses,
    staleTime: 5 * 60_000
  });
}

export function useTaskQuery(taskId: string) {
  return useQuery({
    queryKey: taskQueryKeys.detail(taskId),
    queryFn: () => getTask(taskId)
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

export function useUpdateTaskMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, payload }: { taskId: string; payload: UpdateTaskPayload }) =>
      updateTask(taskId, payload),
    onSuccess: async (task) => {
      queryClient.setQueryData(taskQueryKeys.detail(task.id), task);
      await queryClient.invalidateQueries({ queryKey: todayQueryKeys.all });
    }
  });
}

export function useDeleteTaskMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteTask,
    onSuccess: async (_data, taskId) => {
      queryClient.removeQueries({ queryKey: taskQueryKeys.detail(taskId) });
      await queryClient.invalidateQueries({ queryKey: todayQueryKeys.all });
    }
  });
}
