import type { Task, TaskSort } from "../../entities/task/types";

type PlanningGroup = { key: string; label: string; showPlan: boolean; tasks: Task[] };

export function groupPlanningTasks(tasks: Task[], sort: TaskSort, today: string): PlanningGroup[] {
  if (sort !== "planned_date_asc") return [{ key: "all", label: "", showPlan: true, tasks }];

  const groups = new Map<string, PlanningGroup>();
  for (const task of tasks) {
    const date = task.occurrence_date ?? task.planned_date;
    const key = !date ? "undated" : date < today ? "past" : date;
    let group = groups.get(key);
    if (!group) {
      const label = !date ? "Без даты" : date < today ? "Ранее" : date === today ? "Сегодня" : new Intl.DateTimeFormat("ru-RU", {
        day: "numeric", month: "short", ...(date.slice(0,4) !== today.slice(0,4) ? { year: "numeric" } : {})
      }).format(new Date(`${date}T12:00:00`)).replace(".", "");
      group = { key, label, showPlan: key === "past", tasks: [] };
      groups.set(key, group);
    }
    group.tasks.push(task);
  }
  return [...groups.values()];
}
