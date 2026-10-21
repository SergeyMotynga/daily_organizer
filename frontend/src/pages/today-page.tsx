import { useState } from "react";
import { AlertCircle, ChevronLeft, ChevronRight, Clock3, Plus, RotateCcw } from "lucide-react";
import { Link, useNavigate } from "react-router";
import { appRoutePaths } from "../app/route-paths";
import type { Task, TaskStatusCode } from "../entities/task/types";
import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import { TaskDetailsDrawer } from "../features/tasks/task-details-drawer";
import { TaskListItem } from "../features/tasks/task-list-item";
import { useRecurrenceCompletionMutation, useUpdateTaskMutation } from "../features/tasks/queries";
import { isTaskRecurring } from "../features/tasks/recurrence";
import { useTodayViewQuery } from "../features/today/queries";
import { formatCompactDate, formatDateValue, parseDateValue } from "../shared/date-values";
import { Checkbox } from "../shared/ui/checkbox";
import { InlineCalendar } from "../shared/ui/inline-calendar";
import { SelectCombobox } from "../shared/ui/select-combobox";

export function TodayPage() {
  const navigate = useNavigate();
  const query = useTodayViewQuery();
  const update = useUpdateTaskMutation();
  const completion = useRecurrenceCompletionMutation();
  const [creating, setCreating] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [details, setDetails] = useState<string | null>(null);
  const [showDone, setShowDone] = useState(false);
  const [sort, setSort] = useState("planned_time");
  const data = query.data;
  const pendingId = update.isPending ? update.variables.taskId : completion.isPending ? completion.variables.taskId : null;
  function changeStatus(task: Task, status: TaskStatusCode) {
    if (isTaskRecurring(task) && task.occurrence_date) completion.mutate({ taskId: task.id, occurrenceDate: task.occurrence_date, completed: status === "done" });
    else update.mutate({ taskId: task.id, payload: { status } });
  }
  function openDate(value: string) {
    navigate(`${appRoutePaths.tasks.planning}?planned_date=${value}&statuses=todo`);
  }
  function shiftDay(offset: number) {
    const date = parseDateValue(data?.date) ?? new Date();
    date.setDate(date.getDate() + offset);
    openDate(formatDateValue(date));
  }
  const planned = [...(data?.blocks.planned_today ?? [])].sort((a, b) => sort === "created_at_desc" ? b.created_at.localeCompare(a.created_at) : sort === "deadline_date_asc" ? (a.deadline_date ?? "9999").localeCompare(b.deadline_date ?? "9999") : (a.planned_time ?? "99").localeCompare(b.planned_time ?? "99"));
  const timed = planned.filter((task) => task.planned_time);
  const untimed = planned.filter((task) => !task.planned_time);
  const row = (task: Task, showTime = true) => <TaskListItem key={`${task.id}-${task.occurrence_date}`} task={task} expanded={expanded === task.id} onExpand={() => setExpanded(expanded === task.id ? null : task.id)} onStatusChange={(status) => changeStatus(task, status)} isPending={pendingId === task.id} showTime={showTime} />;
  return <>
    <section className="today-page">
      <header className="today-page__header">
        <div className="route-heading-left"><h1>Сегодня</h1><div className="route-date-arrows"><button type="button" aria-label="Предыдущий день" onClick={() => shiftDay(-1)}><ChevronLeft size={22} /></button><button type="button" aria-label="Следующий день" onClick={() => shiftDay(1)}><ChevronRight size={22} /></button></div><span>{data ? new Intl.DateTimeFormat("ru-RU", { weekday: "short", day: "numeric", month: "long" }).format(parseDateValue(data.date)).replace(/^./, (s) => s.toUpperCase()) : "Ваш план на день"}</span></div>
        <div className="route-heading-actions"><span>{planned.length} в плане · {data?.summary.done_today ?? 0} выполнены</span><button className="today-page__new-task" type="button" onClick={() => setCreating(true)}><Plus size={22} aria-hidden="true" />Новая задача</button></div>
      </header>
      {query.isPending ? <div className="today-loading" role="status"><div className="today-loading__panel" aria-hidden="true" />Загружаем задачи на сегодня…</div> : null}
      {query.isError ? <section className="today-error" role="alert"><AlertCircle size={28} /><div><h2>Не удалось загрузить задачи</h2><p>Проверьте подключение и попробуйте ещё раз.</p></div><button type="button" onClick={() => void query.refetch()}><RotateCcw size={18} />Повторить</button></section> : null}
      {update.isError || completion.isError ? <p className="today-quick-error" role="alert">Не удалось изменить задачу. Попробуйте ещё раз.</p> : null}
      {data ? <div className="route-today-grid">
        <section className="route-panel route-today-main" aria-label="План на день">
          <header className="route-section-heading"><div className="route-day-plan-title"><h2>План на день</h2><SelectCombobox className="route-today-sort" label="Сортировка плана на день" value={sort} options={[{ value: "planned_time", label: "По времени" }, { value: "created_at_desc", label: "Сначала новые" }, { value: "deadline_date_asc", label: "По дедлайну" }]} onChange={setSort} /></div><div className="route-attention"><Link to={`${appRoutePaths.tasks.planning}?deadline_preset=today&statuses=todo`}><Clock3 size={20} />{data.summary.today_deadline} дедлайна сегодня</Link><Link to={`${appRoutePaths.tasks.planning}?deadline_preset=overdue&statuses=todo`}><AlertCircle size={20} />{data.summary.overdue} просрочено</Link></div></header>
          <div className="route-task-scroll">
            {timed.map((task) => row(task))}
            {untimed.length ? <><h3 className="route-group-label">Без времени · {untimed.length}</h3>{untimed.map((task) => row(task, false))}</> : null}
            {!planned.length ? <div className="route-empty"><h2>На сегодня всё спокойно</h2><p>Запланированных задач пока нет.</p><button type="button" onClick={() => setCreating(true)}>Создать задачу</button></div> : null}
            <button type="button" className="route-completed-toggle" aria-expanded={showDone} onClick={() => setShowDone(!showDone)}><ChevronRight size={20} style={{ transform: showDone ? "rotate(90deg)" : undefined }} aria-hidden="true" />Выполнено сегодня · {data.blocks.done_today.length}</button>
            {showDone ? data.blocks.done_today.map((task) => row(task, false)) : null}
          </div>
        </section>
        <aside className="route-panel route-context" aria-label="Календарь и задачи">
          <InlineCalendar value={data.date} onChange={openDate} />
          <section className="route-side-section"><h3>Входящие <span className="muted small">· {data.blocks.inbox.length}</span></h3>{data.blocks.inbox.slice(0,3).map((task) => <div className="route-side-task" key={task.id}><Checkbox className="route-task__check" aria-label={`Выполнить: ${task.title}`} isDisabled={pendingId === task.id || isTaskRecurring(task)} onChange={() => changeStatus(task, "done")} /><button type="button" onClick={() => setDetails(task.id)}>{task.title}</button></div>)}{!data.blocks.inbox.length ? <p className="small muted">Входящих задач нет.</p> : null}<Link to={`${appRoutePaths.tasks.planning}?preset=no_date&statuses=todo`}>Все входящие →</Link></section>
          <section className="route-side-section"><h3>Ближайшие дедлайны</h3>{data.blocks.soon_deadline.slice(0,3).map((task) => <div className="route-side-task" key={task.id}><button type="button" onClick={() => setDetails(task.id)}>{task.title}</button><span>{task.deadline_date ? formatCompactDate(task.deadline_date) : ""}</span></div>)}{!data.blocks.soon_deadline.length ? <p className="small muted">Ближайших дедлайнов нет.</p> : null}{data.blocks.soon_deadline.length > 3 ? <Link to={`${appRoutePaths.tasks.planning}?deadline_preset=soon&statuses=todo`}>Все дедлайны →</Link> : null}</section>
        </aside>
      </div> : null}
    </section>
    {creating ? <CreateTaskDrawer onClose={() => setCreating(false)} /> : null}
    {details ? <TaskDetailsDrawer taskId={details} onClose={() => setDetails(null)} /> : null}
  </>;
}
