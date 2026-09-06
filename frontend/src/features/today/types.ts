import type { Task } from "../../entities/task/types";

export type { Task } from "../../entities/task/types";

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
