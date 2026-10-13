import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { ProjectDetail } from "../../entities/project/types";
import type { TaskListResponse, TaskStatusCode } from "../../entities/task/types";
import { calendarQueryKeys } from "../calendar/queries";
import { getTasks } from "../tasks/api";
import { taskQueryKeys } from "../tasks/queries";
import { todayQueryKeys } from "../today/queries";
import {
  bulkMoveProjectTasks,
  bulkSetProjectTaskStatus,
  createProject,
  createProjectColumn,
  deleteProject,
  deleteProjectColumn,
  getProject,
  getProjects,
  moveProjectTask,
  reorderProjectColumns,
  updateProject,
  updateProjectColumn
} from "./api";

export const projectQueryKeys = {
  all: ["projects"] as const,
  lists: ["projects", "list"] as const,
  list: (archived: boolean, q: string) => ["projects", "list", { archived, q }] as const,
  detail: (projectId: string) => ["projects", "detail", projectId] as const,
  tasksPrefix: (projectId: string) => ["projects", "tasks", projectId] as const,
  tasks: (projectId: string, limit: number, offset: number) =>
    ["projects", "tasks", projectId, { limit, offset }] as const
};

export function useProjectsQuery(archived: boolean, q = "") {
  return useQuery({
    queryKey: projectQueryKeys.list(archived, q),
    queryFn: () => getProjects(archived, q)
  });
}

export function useProjectQuery(projectId: string) {
  return useQuery({
    queryKey: projectQueryKeys.detail(projectId),
    queryFn: () => getProject(projectId),
    enabled: Boolean(projectId)
  });
}

export function useProjectTasksQuery(projectId: string, limit = 100, offset = 0) {
  return useQuery({
    queryKey: projectQueryKeys.tasks(projectId, limit, offset),
    queryFn: () =>
      getTasks({
        preset: "all",
        statuses: ["todo", "done"],
        q: "",
        sort: "created_at_asc",
        limit,
        offset,
        project_id: projectId
      }),
    enabled: Boolean(projectId),
    placeholderData: (previousData) => previousData
  });
}

function optimisticMove(
  response: TaskListResponse,
  detail: ProjectDetail | undefined,
  taskId: string,
  targetColumnId: string,
  targetPosition: number
): TaskListResponse {
  const moved = response.items.find((task) => task.id === taskId);
  if (!moved) return response;
  const sourceColumnId = moved.project_column_id;
  const withoutMoved = response.items.filter((task) => task.id !== taskId);
  const target = withoutMoved
    .filter((task) => task.project_column_id === targetColumnId)
    .sort((a, b) => (a.project_position ?? 0) - (b.project_position ?? 0));
  const position = Math.min(targetPosition, target.length);
  const completion = detail?.columns.find((column) => column.id === targetColumnId)
    ?.is_completion_column;
  const optimisticTask = {
    ...moved,
    project_column_id: targetColumnId,
    status: completion ? ("done" as const) : ("todo" as const),
    completed_at: completion ? moved.completed_at ?? new Date().toISOString() : null
  };
  target.splice(position, 0, optimisticTask);
  const normalizedIds = new Map<string, number>();
  for (const columnId of new Set([sourceColumnId, targetColumnId])) {
    withoutMoved
      .filter((task) => task.project_column_id === columnId)
      .sort((a, b) => (a.project_position ?? 0) - (b.project_position ?? 0))
      .forEach((task, index) => normalizedIds.set(task.id, index));
  }
  target.forEach((task, index) => normalizedIds.set(task.id, index));
  const targetById = new Map(target.map((task) => [task.id, task]));
  return {
    ...response,
    items: response.items.map((task) => {
      const replacement = targetById.get(task.id) ?? task;
      return normalizedIds.has(task.id)
        ? { ...replacement, project_position: normalizedIds.get(task.id) ?? 0 }
        : replacement;
    })
  };
}

export function useMoveProjectTaskMutation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      taskId,
      targetColumnId,
      targetPosition
    }: {
      taskId: string;
      targetColumnId: string;
      targetPosition: number;
    }) => moveProjectTask(taskId, projectId, targetColumnId, targetPosition),
    onMutate: async (variables) => {
      const prefix = projectQueryKeys.tasksPrefix(projectId);
      await queryClient.cancelQueries({ queryKey: prefix });
      const previous = queryClient.getQueriesData<TaskListResponse>({ queryKey: prefix });
      const detail = queryClient.getQueryData<ProjectDetail>(projectQueryKeys.detail(projectId));
      queryClient.setQueriesData<TaskListResponse>({ queryKey: prefix }, (current) =>
        current
          ? optimisticMove(
              current,
              detail,
              variables.taskId,
              variables.targetColumnId,
              variables.targetPosition
            )
          : current
      );
      return { previous };
    },
    onError: (_error, _variables, context) => {
      context?.previous.forEach(([key, data]) => queryClient.setQueryData(key, data));
    },
    onSettled: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: projectQueryKeys.tasksPrefix(projectId) }),
        queryClient.invalidateQueries({ queryKey: projectQueryKeys.detail(projectId) }),
        queryClient.invalidateQueries({ queryKey: projectQueryKeys.lists }),
        queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists }),
        queryClient.invalidateQueries({ queryKey: calendarQueryKeys.all }),
        queryClient.invalidateQueries({ queryKey: todayQueryKeys.all })
      ]);
    }
  });
}

export function useCreateProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createProject,
    onSuccess: async () => queryClient.invalidateQueries({ queryKey: projectQueryKeys.lists })
  });
}

export function useUpdateProjectMutation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof updateProject>[1]) => updateProject(projectId, payload),
    onSuccess: async (project) => {
      queryClient.setQueryData(projectQueryKeys.detail(projectId), project);
      await queryClient.invalidateQueries({ queryKey: projectQueryKeys.lists });
    }
  });
}

export function useDeleteProjectMutation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => deleteProject(projectId),
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: projectQueryKeys.detail(projectId) });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: projectQueryKeys.lists }),
        queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists })
      ]);
    }
  });
}

export function useProjectColumnMutations(projectId: string) {
  const queryClient = useQueryClient();
  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.detail(projectId) }),
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.tasksPrefix(projectId) }),
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.lists })
    ]);
  };
  return {
    create: useMutation({
      mutationFn: (title: string) => createProjectColumn(projectId, title),
      onSuccess: invalidate
    }),
    update: useMutation({
      mutationFn: ({ columnId, payload }: { columnId: string; payload: Parameters<typeof updateProjectColumn>[2] }) =>
        updateProjectColumn(projectId, columnId, payload),
      onSuccess: invalidate
    }),
    remove: useMutation({
      mutationFn: (columnId: string) => deleteProjectColumn(projectId, columnId),
      onSuccess: invalidate
    }),
    reorder: useMutation({
      mutationFn: (columnIds: string[]) => reorderProjectColumns(projectId, columnIds),
      onSuccess: invalidate
    })
  };
}

export function useProjectBulkMutations(projectId: string) {
  const queryClient = useQueryClient();
  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.tasksPrefix(projectId) }),
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.detail(projectId) }),
      queryClient.invalidateQueries({ queryKey: projectQueryKeys.lists }),
      queryClient.invalidateQueries({ queryKey: taskQueryKeys.lists }),
      queryClient.invalidateQueries({ queryKey: todayQueryKeys.all }),
      queryClient.invalidateQueries({ queryKey: calendarQueryKeys.all })
    ]);
  };
  return {
    move: useMutation({
      mutationFn: ({ taskIds, targetColumnId }: { taskIds: string[]; targetColumnId: string }) =>
        bulkMoveProjectTasks(projectId, taskIds, targetColumnId),
      onSuccess: invalidate
    }),
    status: useMutation({
      mutationFn: ({ taskIds, status }: { taskIds: string[]; status: TaskStatusCode }) =>
        bulkSetProjectTaskStatus(projectId, taskIds, status),
      onSuccess: invalidate
    })
  };
}
