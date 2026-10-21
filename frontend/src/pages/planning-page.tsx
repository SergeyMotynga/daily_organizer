import { useEffect, useRef, useState } from "react";
import { AlertCircle, CalendarDays, Plus, RotateCcw, Search, SlidersHorizontal, X } from "lucide-react";
import { useSearchParams } from "react-router";
import type { Task, TaskDeadlinePreset, TaskListParams, TaskListPreset, TaskSort, TaskStatusCode } from "../entities/task/types";
import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import { TaskListItem } from "../features/tasks/task-list-item";
import { groupPlanningTasks } from "../features/tasks/planning-groups";
import { TaskDateFilters } from "../features/tasks/task-date-filters";
import { useRecurrenceCompletionMutation, useTasksQuery, useUpdateTaskMutation } from "../features/tasks/queries";
import { isTaskRecurring } from "../features/tasks/recurrence";
import { useProjectsQuery } from "../features/projects/queries";
import { formatCompactDate, getTodayValue } from "../shared/date-values";
import { Pagination } from "../shared/ui/pagination";
import { SelectCombobox } from "../shared/ui/select-combobox";

const sortOptions = [
  { value: "planned_date_asc", label: "По плановой дате" },
  { value: "deadline_date_asc", label: "Ближайшие дедлайны" },
  { value: "created_at_desc", label: "Сначала новые" },
  { value: "created_at_asc", label: "Сначала старые" }
];
const presets = [
  { value: "all", label: "Все даты" }, { value: "today", label: "Сегодня" },
  { value: "tomorrow", label: "Завтра" }, { value: "week", label: "Эта неделя" },
  { value: "no_date", label: "Без даты" }, { value: "overdue", label: "Просроченные" }
];
const dateParam = (value: string | null) => value && /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : undefined;

export function PlanningPage() {
  const [params, setParams] = useSearchParams();
  const [creating, setCreating] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const filterRef = useRef<HTMLElement>(null);
  const update = useUpdateTaskMutation();
  const completion = useRecurrenceCompletionMutation();
  const projects = useProjectsQuery(false);
  const presetValue = params.get("preset") ?? "all";
  const preset: TaskListPreset = ["all", "today", "tomorrow", "week", "no_date"].includes(presetValue) ? presetValue as TaskListPreset : "all";
  const statusParam = params.get("statuses")?.split(",").filter((value): value is TaskStatusCode => value === "todo" || value === "done");
  const statuses: TaskStatusCode[] = statusParam?.length ? statusParam : ["todo"];
  const sort = sortOptions.some((option) => option.value === params.get("sort")) ? params.get("sort") as TaskSort : "planned_date_asc";
  const limit = [10,20,50].includes(Number(params.get("limit"))) ? Number(params.get("limit")) : 20;
  const offset = Math.max(0, Number(params.get("offset")) || 0);
  const deadlinePreset = ["overdue", "today", "soon"].includes(params.get("deadline_preset") ?? "") ? params.get("deadline_preset") as TaskDeadlinePreset : undefined;
  const plannedDate = dateParam(params.get("planned_date"));
  const range = { from: dateParam(params.get("planned_from")), to: dateParam(params.get("planned_to")) };
  const search = params.get("q") ?? "";
  const projectId = params.get("project_id") ?? "";
  const queryParams: TaskListParams = { preset, statuses, q: search, sort, limit, offset, planned_date: plannedDate, planned_from: range.from, planned_to: range.to, deadline_date: dateParam(params.get("deadline_date")), deadline_preset: deadlinePreset, project_id: projectId || undefined, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC" };
  const query = useTasksQuery(queryParams);
  const total = query.data?.pagination.total ?? 0;
  const pendingId = update.isPending ? update.variables.taskId : completion.isPending ? completion.variables.taskId : null;
  function change(values: Record<string, string | null>, replace = false) {
    const next = new URLSearchParams(params);
    for (const [key,value] of Object.entries(values)) { if (value) next.set(key,value); else next.delete(key); }
    setParams(next, { replace });
  }
  useEffect(() => {
    if (query.data && offset > 0 && offset >= total) {
      const next = new URLSearchParams(params);
      next.set("offset", String(Math.max(0,(Math.ceil(total / limit) - 1) * limit)));
      setParams(next, { replace: true });
    }
  }, [query.data, total, offset, limit, params, setParams]);
  function changeStatus(task: Task, status: TaskStatusCode) {
    if (isTaskRecurring(task) && task.occurrence_date) completion.mutate({ taskId: task.id, occurrenceDate: task.occurrence_date, completed: status === "done" });
    else update.mutate({ taskId: task.id, payload: { status } });
  }
  function changePreset(value: string) {
    change({ preset: value === "overdue" ? "all" : value, deadline_preset: value === "overdue" ? "overdue" : null, deadline_date: null, planned_date: null, planned_from: null, planned_to: null, offset: null });
  }
  const groups = groupPlanningTasks(query.data?.items ?? [], sort, getTodayValue());
  const hasDates = Boolean(plannedDate || range.from || range.to || deadlinePreset || queryParams.deadline_date);
  const hasFilters = hasDates || preset !== "all" || search || projectId;
  return <>
    <section className="planning-page route-planning">
      <header className="planning-page__header"><div><h1>Задачи</h1><p>Все задачи и планы</p></div><button className="planning-page__new-task" type="button" onClick={() => setCreating(true)}><Plus size={22} aria-hidden="true" />Новая задача</button></header>
      <div className="route-planning-toolbar"><label className="route-search"><Search size={22} aria-hidden="true" /><input type="search" aria-label="Поиск по названию и описанию" placeholder="Поиск по задачам" value={search} onChange={(event) => change({ q: event.target.value, offset: null },true)} /></label><div className="route-segment" aria-label="Быстрые фильтры">{presets.map((option) => <button key={option.value} type="button" aria-pressed={option.value === "overdue" ? deadlinePreset === "overdue" : !hasDates && preset === option.value} onClick={() => changePreset(option.value)}>{option.label}</button>)}</div><button className="route-filter-button" type="button" onClick={() => filterRef.current?.focus()}><SlidersHorizontal size={20} aria-hidden="true" />Фильтры</button></div>
      <div className="route-planning-layout">
        <section className="route-panel route-planning-main" aria-label="Список задач" aria-busy={query.isFetching}>
          <header className="route-section-heading"><div className="route-status-tabs" aria-label="Статус задач">{[{value:"todo",label:"Активные"},{value:"done",label:"Выполненные"},{value:"todo,done",label:"Все"}].map((tab) => <button type="button" key={tab.value} aria-pressed={tab.value === (statuses.length === 2 ? "todo,done" : statuses[0])} onClick={() => change({ statuses: tab.value, offset: null })}>{tab.label}</button>)}</div><SelectCombobox className="route-planning-sort" label="Сортировка задач" value={sort} options={sortOptions} onChange={(value) => change({ sort: value, offset: null })} /></header>
          {hasFilters ? <div className="route-applied-filters" role="status"><span>{plannedDate ? `Дата: ${formatCompactDate(plannedDate)}` : range.from || range.to ? `Период: ${range.from ? formatCompactDate(range.from) : "…"}–${range.to ? formatCompactDate(range.to) : "…"}` : deadlinePreset ? `Дедлайн: ${{overdue:"просрочено",today:"сегодня",soon:"в ближайшие 3 дня"}[deadlinePreset]}` : "Применены фильтры"}</span><button type="button" onClick={() => setParams({ statuses: statuses.join(","), sort })}><X size={16} aria-hidden="true" />Сбросить фильтры</button></div> : null}
          {update.isError || completion.isError ? <p className="planning-mutation-error" role="alert">Не удалось изменить статус задачи. Попробуйте ещё раз.</p> : null}
          {query.isPending ? <div className="planning-loading" role="status"><div aria-hidden="true" />Загружаем задачи…</div> : null}
          {query.isError ? <div className="planning-error" role="alert"><AlertCircle size={28} /><div><h2>Не удалось загрузить задачи</h2><p>Проверьте подключение и попробуйте ещё раз.</p></div><button type="button" onClick={() => void query.refetch()}><RotateCcw size={18} />Повторить</button></div> : null}
          {query.data ? <><div className="route-task-scroll">{query.data.items.length ? groups.map(({key,label,tasks,showPlan}) => <section key={key}>{label ? <h3 className="route-group-label">{label} · {tasks.length}</h3> : null}{tasks.map((task) => <TaskListItem key={`${task.id}-${task.occurrence_date}`} task={task} expanded={expanded === `${task.id}-${task.occurrence_date}`} onExpand={() => setExpanded(expanded === `${task.id}-${task.occurrence_date}` ? null : `${task.id}-${task.occurrence_date}`)} isPending={pendingId === task.id} onStatusChange={(status) => changeStatus(task,status)} showPlan={showPlan} />)}</section>) : <div className="route-empty"><CalendarDays size={36} /><h2>Задачи не найдены</h2><p>Измените фильтры или создайте новую задачу.</p><button type="button" onClick={() => setCreating(true)}>Создать задачу</button></div>}</div><Pagination className="planning-pagination" label="Всего задач" total={total} limit={limit} offset={offset} onLimitChange={(value) => change({ limit:String(value), offset:null })} onOffsetChange={(value) => change({ offset:String(value) })} /></> : null}
        </section>
        <aside className="route-panel route-context route-filters" ref={filterRef} tabIndex={-1} aria-label="Фильтры задач"><h2>Фильтры</h2><h3>Проект</h3><SelectCombobox label="Фильтр по проекту" value={projectId} options={[{value:"",label:"Все проекты"},...(projects.data?.items.map((project) => ({value:project.id,label:project.title})) ?? [])]} onChange={(value) => change({project_id:value,offset:null})} /><TaskDateFilters key={`${plannedDate}-${range.from}-${range.to}`} date={plannedDate} range={range} onApply={(value) => change({ planned_date: value.date ?? null, planned_from: value.range?.from ?? null, planned_to: value.range?.to ?? null, deadline_date:null, deadline_preset:null, preset:null, offset:null })} /></aside>
      </div>
    </section>
    {creating ? <CreateTaskDrawer onClose={() => setCreating(false)} /> : null}
  </>;
}
