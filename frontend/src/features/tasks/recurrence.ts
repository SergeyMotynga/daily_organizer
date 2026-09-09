import type {
  Task,
  TaskRecurrenceType,
  TaskRecurrenceTypeCode
} from "../../entities/task/types";

export const taskRecurrenceTypeFallback: TaskRecurrenceType[] = [
  { code: "none", title: "Не повторять", sort_order: 10 },
  { code: "daily", title: "По дням", sort_order: 20 },
  { code: "weekdays", title: "По будням", sort_order: 30 },
  { code: "weekly", title: "По неделям", sort_order: 40 }
];

export function isTaskRecurring(task: Task): boolean {
  return task.recurrence_type_code !== "none";
}

export function getRecurrenceLabel(
  recurrenceType: TaskRecurrenceTypeCode,
  interval: number
): string {
  if (recurrenceType === "daily") {
    return interval === 1 ? "Каждый день" : `Каждые ${interval} дн.`;
  }
  if (recurrenceType === "weekdays") {
    return "По будням";
  }
  if (recurrenceType === "weekly") {
    return interval === 1 ? "Каждую неделю" : `Раз в ${interval} нед.`;
  }
  return "Не повторять";
}

export function isRecurrenceDueOn(task: Task, occurrenceDate: string): boolean {
  if (!isTaskRecurring(task) || !task.recurrence_start_date) {
    return false;
  }
  if (occurrenceDate < task.recurrence_start_date) {
    return false;
  }
  if (task.recurrence_end_date && occurrenceDate > task.recurrence_end_date) {
    return false;
  }

  const occurrence = new Date(`${occurrenceDate}T00:00:00Z`);
  const start = new Date(`${task.recurrence_start_date}T00:00:00Z`);
  const daysSinceStart = Math.round((occurrence.getTime() - start.getTime()) / 86_400_000);

  if (task.recurrence_type_code === "daily") {
    return daysSinceStart % task.recurrence_interval === 0;
  }
  if (task.recurrence_type_code === "weekdays") {
    const weekday = occurrence.getUTCDay();
    return weekday >= 1 && weekday <= 5;
  }
  return daysSinceStart % (7 * task.recurrence_interval) === 0;
}
