import type { CreateTaskPayload, Task, TaskStatus } from "../../entities/task/types";
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
