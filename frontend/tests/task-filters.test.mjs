import assert from "node:assert/strict";
import { test } from "node:test";
import { filterProjectTasks } from "../src/features/projects/task-filters.ts";

process.env.TZ = "Asia/Omsk";
const tasks = [
  { id: "today", title: "Сегодня", planned_date: "2026-10-14", deadline_date: null, status: "todo" },
  { id: "tomorrow", title: "Завтра", planned_date: "2026-10-15", deadline_date: null, status: "todo" },
  { id: "past", title: "Просрочено", planned_date: null, deadline_date: "2026-10-13", status: "todo" },
  { id: "deadline", title: "Дедлайн", planned_date: null, deadline_date: "2026-10-14", status: "todo" }
];

for (const [filter, expected] of [
  ["today", ["today", "deadline"]],
  ["tomorrow", ["tomorrow"]],
  ["overdue", ["past"]],
  ["week", ["today", "tomorrow", "deadline"]]
]) {
  test(`${filter} uses the local day before UTC midnight`, (t) => {
    t.mock.timers.enable({ apis: ["Date"], now: new Date("2026-10-13T23:30:00Z").getTime() });
    assert.deepEqual(filterProjectTasks(tasks, "", filter, undefined, "", "").map((task) => task.id), expected);
  });
}
