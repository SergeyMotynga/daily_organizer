import type {
  CreateTaskPayload,
  Task,
  TaskListParams,
  TaskListResponse,
  TaskRecurrenceCompletion,
  TaskRecurrenceType,
  TaskStatus,
  UpdateTaskPayload
} from "../../entities/task/types";
import { apiRequest } from "../../shared/api";

export function getTaskStatuses(): Promise<TaskStatus[]> {
  return apiRequest<TaskStatus[]>("/task-statuses");
}

export function getTaskRecurrenceTypes(): Promise<TaskRecurrenceType[]> {
  return apiRequest<TaskRecurrenceType[]>("/task-recurrence-types");
}

export function getTasks(params: TaskListParams): Promise<TaskListResponse> {
  const searchParams = new URLSearchParams({
    preset: params.preset,
    sort: params.sort,
    limit: String(params.limit),
    offset: String(params.offset)
  });

  if (params.statuses.length > 0) {
    searchParams.set("statuses", params.statuses.join(","));
  }

  if (params.archived) {
    searchParams.set("archived", "true");
  }

  if (params.planned_date) {
    searchParams.set("planned_date", params.planned_date);
  }

  if (params.planned_from) {
    searchParams.set("planned_from", params.planned_from);
  }

  if (params.planned_to) {
    searchParams.set("planned_to", params.planned_to);
  }

  if (params.deadline_date) {
    searchParams.set("deadline_date", params.deadline_date);
  }

  if (params.deadline_preset) {
    searchParams.set("deadline_preset", params.deadline_preset);
  }

  if (params.timezone) {
    searchParams.set("timezone", params.timezone);
  }

  if (params.q.trim()) {
    searchParams.set("q", params.q.trim());
  }

  return apiRequest<TaskListResponse>(`/tasks?${searchParams.toString()}`);
}

export function createTask(payload: CreateTaskPayload): Promise<Task> {
  return apiRequest<Task>("/tasks", {
    method: "POST",
    body: payload
  });
}

export function getTask(taskId: string): Promise<Task> {
  return apiRequest<Task>(`/tasks/${taskId}`);
}

export function updateTask(taskId: string, payload: UpdateTaskPayload): Promise<Task> {
  return apiRequest<Task>(`/tasks/${taskId}`, {
    method: "PATCH",
    body: payload
  });
}

export function deleteTask(taskId: string): Promise<void> {
  return apiRequest<void>(`/tasks/${taskId}`, {
    method: "DELETE"
  });
}

export function completeTaskRecurrence(
  taskId: string,
  occurrenceDate: string
): Promise<TaskRecurrenceCompletion> {
  return apiRequest<TaskRecurrenceCompletion>(
    `/tasks/${taskId}/recurrence-completions/${occurrenceDate}`,
    { method: "PUT" }
  );
}

export function uncompleteTaskRecurrence(
  taskId: string,
  occurrenceDate: string
): Promise<void> {
  return apiRequest<void>(`/tasks/${taskId}/recurrence-completions/${occurrenceDate}`, {
    method: "DELETE"
  });
}
