import type {
  CreateTaskPayload,
  Task,
  TaskStatus,
  UpdateTaskPayload
} from "../../entities/task/types";
import { apiRequest } from "../../shared/api";

export function getTaskStatuses(): Promise<TaskStatus[]> {
  return apiRequest<TaskStatus[]>("/task-statuses");
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
