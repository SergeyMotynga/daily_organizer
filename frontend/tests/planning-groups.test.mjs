import assert from "node:assert/strict";
import { test } from "node:test";
import { groupPlanningTasks } from "../src/features/tasks/planning-groups.ts";

const task = (id, planned_date, extra = {}) => ({ id, planned_date, ...extra });

test("deadline and creation sorts keep the API sequence across planning dates", () => {
  const items = [task("a", "2026-10-22"), task("b", "2026-10-23"), task("c", "2026-10-22")];
  for (const sort of ["deadline_date_asc", "created_at_desc", "created_at_asc"]) {
    const groups = groupPlanningTasks(items, sort, "2026-10-21");
    assert.deepEqual(groups.flatMap(group => group.tasks.map(task => task.id)), ["a", "b", "c"]);
    assert.equal(groups[0].showPlan, true);
    assert.equal(groups[0].label, "");
  }
});

test("future dates in different years never share a group or ambiguous label", () => {
  const groups = groupPlanningTasks([task("a", "2026-10-22"), task("b", "2027-10-22")], "planned_date_asc", "2026-10-21");
  assert.equal(groups.length, 2);
  assert.notEqual(groups[0].key, groups[1].key);
  assert.notEqual(groups[0].label, groups[1].label);
  assert.match(groups[1].label, /2027/);
});

test("past, today and undated tasks retain approved groups and occurrence dates", () => {
  const groups = groupPlanningTasks([task("a", "2026-10-19"), task("b", "2026-10-20"), task("r", "2026-10-01", { occurrence_date: "2026-10-21" }), task("c", null)], "planned_date_asc", "2026-10-21");
  assert.deepEqual(groups.map(group => [group.label, group.tasks.length, group.showPlan]), [["Ранее", 2, true], ["Сегодня", 1, false], ["Без даты", 1, false]]);
});
