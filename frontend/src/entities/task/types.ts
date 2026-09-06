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

export type CreateTaskPayload = {
  title: string;
  description: string | null;
  status: TaskStatusCode;
  planned_date: string | null;
  deadline_date: string | null;
};
