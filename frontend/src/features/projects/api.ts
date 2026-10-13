import type {
  CreateProjectPayload,
  ProjectColumn,
  ProjectDetail,
  ProjectListResponse,
  UpdateProjectColumnPayload,
  UpdateProjectPayload
} from "../../entities/project/types";
import type { Task, TaskStatusCode } from "../../entities/task/types";
import { apiRequest } from "../../shared/api";

export function getProjects(archived: boolean, q = ""): Promise<ProjectListResponse> {
  const params = new URLSearchParams({ archived: String(archived) });
  if (q.trim()) params.set("q", q.trim());
  return apiRequest<ProjectListResponse>(`/projects?${params.toString()}`);
}

export function getProject(projectId: string): Promise<ProjectDetail> {
  return apiRequest<ProjectDetail>(`/projects/${projectId}`);
}

export function createProject(payload: CreateProjectPayload): Promise<ProjectDetail> {
  return apiRequest<ProjectDetail>("/projects", { method: "POST", body: payload });
}

export function updateProject(
  projectId: string,
  payload: UpdateProjectPayload
): Promise<ProjectDetail> {
  return apiRequest<ProjectDetail>(`/projects/${projectId}`, {
    method: "PATCH",
    body: payload
  });
}

export function deleteProject(projectId: string): Promise<void> {
  return apiRequest<void>(`/projects/${projectId}`, { method: "DELETE" });
}

export function createProjectColumn(projectId: string, title: string): Promise<ProjectColumn> {
  return apiRequest<ProjectColumn>(`/projects/${projectId}/columns`, {
    method: "POST",
    body: { title }
  });
}

export function updateProjectColumn(
  projectId: string,
  columnId: string,
  payload: UpdateProjectColumnPayload
): Promise<ProjectColumn> {
  return apiRequest<ProjectColumn>(`/projects/${projectId}/columns/${columnId}`, {
    method: "PATCH",
    body: payload
  });
}

export function deleteProjectColumn(projectId: string, columnId: string): Promise<void> {
  return apiRequest<void>(`/projects/${projectId}/columns/${columnId}`, {
    method: "DELETE"
  });
}

export function reorderProjectColumns(
  projectId: string,
  columnIds: string[]
): Promise<ProjectColumn[]> {
  return apiRequest<ProjectColumn[]>(`/projects/${projectId}/columns/order`, {
    method: "PUT",
    body: { column_ids: columnIds }
  });
}

export function moveProjectTask(
  taskId: string,
  projectId: string,
  targetColumnId: string,
  targetPosition: number
): Promise<Task> {
  return apiRequest<Task>(`/tasks/${taskId}/move`, {
    method: "POST",
    body: {
      project_id: projectId,
      target_column_id: targetColumnId,
      target_position: targetPosition
    }
  });
}

export function bulkMoveProjectTasks(
  projectId: string,
  taskIds: string[],
  targetColumnId: string
): Promise<Task[]> {
  return apiRequest<Task[]>(`/projects/${projectId}/tasks/bulk-move`, {
    method: "POST",
    body: { task_ids: taskIds, target_column_id: targetColumnId }
  });
}

export function bulkSetProjectTaskStatus(
  projectId: string,
  taskIds: string[],
  status: TaskStatusCode
): Promise<Task[]> {
  return apiRequest<Task[]>(`/projects/${projectId}/tasks/bulk-status`, {
    method: "POST",
    body: { task_ids: taskIds, status }
  });
}
