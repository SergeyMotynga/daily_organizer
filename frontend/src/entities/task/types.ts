export type TaskStatusCode = "todo" | "done";
export type TaskRecurrenceTypeCode = "none" | "daily" | "weekdays" | "weekly";

export type Task = {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatusCode;
  planned_date: string | null;
  planned_time: string | null;
  deadline_date: string | null;
  deadline_time: string | null;
  recurrence_type_code: TaskRecurrenceTypeCode;
  recurrence_interval: number;
  recurrence_start_date: string | null;
  recurrence_end_date: string | null;
  occurrence_date: string | null;
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

export type TaskRecurrenceType = {
  code: TaskRecurrenceTypeCode;
  title: string;
  sort_order: number;
};

export type TaskRecurrenceCompletion = {
  id: string;
  task_id: string;
  occurrence_date: string;
  completed_at: string;
  created_at: string;
};

export type TaskListPreset = "today" | "tomorrow" | "week" | "no_date" | "all";
export type TaskDeadlinePreset = "overdue" | "today" | "soon";

export type TaskSort =
  | "created_at_desc"
  | "created_at_asc"
  | "planned_date_asc"
  | "deadline_date_asc";

export type TaskListParams = {
  preset: TaskListPreset;
  statuses: TaskStatusCode[];
  archived?: boolean;
  planned_date?: string;
  planned_from?: string;
  planned_to?: string;
  deadline_date?: string;
  deadline_preset?: TaskDeadlinePreset;
  timezone?: string;
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
  planned_time: string | null;
  deadline_date: string | null;
  deadline_time: string | null;
  recurrence_type_code: TaskRecurrenceTypeCode;
  recurrence_interval: number;
  recurrence_start_date: string | null;
  recurrence_end_date: string | null;
};

export type UpdateTaskPayload = Partial<CreateTaskPayload> & {
  archived?: boolean;
};

export type CalendarTask = {
  id: string;
  title: string;
  description: string | null;
  planned_date: string | null;
  planned_time: string | null;
  deadline_date: string | null;
  deadline_time: string | null;
  recurrence_type_code: TaskRecurrenceTypeCode;
  recurrence_interval: number;
  recurrence_start_date: string | null;
  recurrence_end_date: string | null;
  created_at: string;
  updated_at: string;
};

export type CalendarTaskItem = {
  task: CalendarTask;
  status: TaskStatusCode;
  occurrence_date: string | null;
};

export type CalendarViewResponse = {
  date_from: string;
  date_to: string;
  planned: CalendarTaskItem[];
  deadlines: CalendarTaskItem[];
  recurrences: CalendarTaskItem[];
};
