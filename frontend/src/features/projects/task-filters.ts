import type { Task } from "../../entities/task/types";

export type DateFilter = "all" | "today" | "tomorrow" | "week" | "overdue" | "exact";

function dateValue(offset = 0): string {
  const value = new Date();
  value.setDate(value.getDate() + offset);
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function filterProjectTasks(tasks: Task[], query: string, dateFilter: DateFilter, selectedDate: string | undefined, stage: string, status: string): Task[] {
  const today = dateValue();
  const tomorrow = dateValue(1);
  const weekEnd = dateValue(6);
  return tasks.filter((task) => {
    if (query && !`${task.title} ${task.description ?? ""}`.toLowerCase().includes(query.toLowerCase())) return false;
    if (stage && task.project_column_id !== stage) return false;
    if (status && task.status !== status) return false;
    if (dateFilter === "today" && task.planned_date !== today && task.deadline_date !== today) return false;
    if (dateFilter === "tomorrow" && task.planned_date !== tomorrow && task.deadline_date !== tomorrow) return false;
    if (dateFilter === "week" && !((task.planned_date && task.planned_date >= today && task.planned_date <= weekEnd) || (task.deadline_date && task.deadline_date >= today && task.deadline_date <= weekEnd))) return false;
    if (dateFilter === "overdue" && !(task.status === "todo" && task.deadline_date && task.deadline_date < today)) return false;
    if (dateFilter === "exact" && selectedDate && task.planned_date !== selectedDate && task.deadline_date !== selectedDate) return false;
    return true;
  });
}
