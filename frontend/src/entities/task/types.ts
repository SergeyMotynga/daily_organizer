export type TaskStatusCode = "todo" | "done" | "archived";

export type Task = {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatusCode;
  planned_date: string | null;
  deadline_date: string | null;
  completed_at: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskStatus = {
  code: TaskStatusCode;
  title: string;
  sort_order: number;
};

export type TaskListPreset = "today" | "tomorrow" | "week" | "no_date" | "all";

export type TaskSort =
  | "created_at_desc"
  | "created_at_asc"
  | "planned_date_asc"
  | "deadline_date_asc";

export type TaskListParams = {
  preset: TaskListPreset;
  statuses: TaskStatusCode[];
  deadline_date?: string;
  q: string;
  sort: TaskSort;
  limit: number;
  offset: number;
};

export type TaskListResponse = {
  items: Task[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
  };
};

export type CreateTaskPayload = {
  title: string;
  description: string | null;
  status: TaskStatusCode;
  planned_date: string | null;
  deadline_date: string | null;
};

export type UpdateTaskPayload = Partial<CreateTaskPayload>;
