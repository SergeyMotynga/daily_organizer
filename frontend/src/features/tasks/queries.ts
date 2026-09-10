import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { TaskListParams, UpdateTaskPayload } from "../../entities/task/types";
import { calendarQueryKeys } from "../calendar/queries";
import { todayQueryKeys } from "../today/queries";
import {
  completeTaskRecurrence,
  createTask,
  deleteTask,
  getTask,
  getTaskRecurrenceTypes,
  getTasks,
  getTaskStatuses,
  uncompleteTaskRecurrence,
  updateTask
} from "./api";

export const taskQueryKeys = {
  all: ["tasks"] as const,
  lists: ["tasks", "list"] as const,
  list: (params: TaskListParams) => ["tasks", "list", params] as const,
  statuses: ["tasks", "statuses"] as const,
  recurrenceTypes: ["tasks", "recurrence-types"] as const,
  detail: (taskId: string) => ["tasks", "detail", taskId] as const
};

export function useTasksQuery(params: TaskListParams) {
  return useQuery({
    queryKey: taskQueryKeys.list(params),
    queryFn: () => getTasks(params),
    placeholderData: (previousData) => previousData
  });
}

export function useTaskStatusesQuery() {
  return useQuery({
    queryKey: taskQueryKeys.statuses,
    queryFn: getTaskStatuses,
    staleTime: 5 * 60_000
  });
}

export function useTaskRecurrenceTypesQuery() {
  return useQuery({
    queryKey: taskQueryKeys.recurrenceTypes,
    queryFn: getTaskRecurrenceTypes,
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
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists }),
        queryClient.invalidateQueries({ queryKey: calendarQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: todayQueryKeys.all })
      ]);
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
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists }),
        queryClient.invalidateQueries({ queryKey: calendarQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: todayQueryKeys.all })
      ]);
    }
  });
}

export function useDeleteTaskMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteTask,
    onSuccess: async (_data, taskId) => {
      queryClient.removeQueries({ queryKey: taskQueryKeys.detail(taskId) });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists }),
        queryClient.invalidateQueries({ queryKey: calendarQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: todayQueryKeys.all })
      ]);
    }
  });
}

export function useRecurrenceCompletionMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      taskId,
      occurrenceDate,
      completed
    }: {
      taskId: string;
      occurrenceDate: string;
      completed: boolean;
    }) =>
      completed
        ? completeTaskRecurrence(taskId, occurrenceDate)
        : uncompleteTaskRecurrence(taskId, occurrenceDate),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists }),
        queryClient.invalidateQueries({ queryKey: calendarQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: todayQueryKeys.all })
      ]);
    }
  });
}
