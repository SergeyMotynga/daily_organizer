export type TaskStatus = "todo" | "done" | "archived";

export type Task = {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  planned_date: string | null;
  deadline_date: string | null;
  completed_at: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TodayViewSummary = {
  total_active: number;
  done_today: number;
  overdue: number;
  today_deadline: number;
};

export type TodayViewBlocks = {
  planned_today: Task[];
  inbox: Task[];
  soon_deadline: Task[];
  today_deadline: Task[];
  overdue: Task[];
  done_today: Task[];
};

export type TodayViewResponse = {
  date: string;
  summary: TodayViewSummary;
  blocks: TodayViewBlocks;
};
