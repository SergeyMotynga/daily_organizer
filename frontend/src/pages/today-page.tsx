import { useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  AlertCircle,
  Archive,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Inbox,
  Plus,
  RotateCcw
} from "lucide-react";
import { Link } from "react-router";

import type { TaskStatusCode } from "../entities/task/types";
import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import { TaskDetailsDrawer } from "../features/tasks/task-details-drawer";
import { useUpdateTaskMutation } from "../features/tasks/queries";
import { useTodayViewQuery } from "../features/today/queries";
import type { Task, TodayViewResponse } from "../features/today/types";

type SummaryCard = {
  label: string;
  value: number;
  icon: LucideIcon;
  tone: "primary" | "neutral" | "warning" | "danger" | "success";
  to?: string;
};

type TodaySort = "created_at_desc" | "planned_date_asc" | "deadline_date_asc";

const todaySortOptions: { value: TodaySort; label: string }[] = [
  { value: "created_at_desc", label: "Сначала новые" },
  { value: "planned_date_asc", label: "По плановой дате" },
  { value: "deadline_date_asc", label: "По дедлайну" }
];

type TaskGroupProps = {
  title: string;
  tasks: Task[];
  today: string;
  tone?: "default" | "danger" | "warning" | "success";
  emptyMessage: string;
  pendingTaskId: string | null;
  onOpenTask: (taskId: string) => void;
  onStatusChange: (taskId: string, status: TaskStatusCode) => void;
};

function formatPageDate(date: string): string {
  const formatted = new Intl.DateTimeFormat("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "UTC"
  }).format(new Date(`${date}T00:00:00Z`));

  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

function formatTaskDate(date: string, today: string): string {
  if (date === today) {
    return "Сегодня";
  }

  const tomorrow = new Date(`${today}T00:00:00Z`);
  tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);

  if (date === tomorrow.toISOString().slice(0, 10)) {
    return "Завтра";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    timeZone: "UTC"
  }).format(new Date(`${date}T00:00:00Z`));
}

function sortTasks(tasks: Task[], sort: TodaySort): Task[] {
  return [...tasks].sort((left, right) => {
    if (sort === "created_at_desc") {
      return right.created_at.localeCompare(left.created_at);
    }

    const field = sort === "planned_date_asc" ? "planned_date" : "deadline_date";
    const leftDate = left[field];
    const rightDate = right[field];
    if (!leftDate && !rightDate) return 0;
    if (!leftDate) return 1;
    if (!rightDate) return -1;
    const dateComparison = leftDate.localeCompare(rightDate);
    if (dateComparison !== 0 || sort !== "planned_date_asc") {
      return dateComparison;
    }
    if (!left.planned_time && !right.planned_time) return 0;
    if (!left.planned_time) return 1;
    if (!right.planned_time) return -1;
    return left.planned_time.localeCompare(right.planned_time);
  });
}

function TaskRow({
  task,
  today,
  isPending,
  onOpen,
  onStatusChange
}: {
  task: Task;
  today: string;
  isPending: boolean;
  onOpen: () => void;
  onStatusChange: (status: TaskStatusCode) => void;
}) {
  const isDone = task.status === "done";
  const displayDate = task.deadline_date ?? task.planned_date;

  return (
    <li className={isDone ? "today-task today-task--done" : "today-task"}>
      <button
        className="today-task__check"
        type="button"
        aria-label={isDone ? `Вернуть в активные: ${task.title}` : `Отметить выполненной: ${task.title}`}
        title={isDone ? "Вернуть в активные" : "Отметить выполненной"}
        onClick={() => onStatusChange(isDone ? "todo" : "done")}
        disabled={isPending}
      >
        {isDone ? <CheckCircle2 size={17} /> : null}
      </button>
      <button className="today-task__title" type="button" onClick={onOpen} disabled={isPending}>
        {task.title}
      </button>
      {displayDate ? (
        <span className="today-task__date">
          <CalendarDays size={15} />
          {formatTaskDate(displayDate, today)} · {task.planned_time ?? "—"}
        </span>
      ) : (
        <span className="today-task__date today-task__date--muted">
          Без даты · {task.planned_time ?? "—"}
        </span>
      )}
      <button
        className="today-task__archive"
        type="button"
        aria-label={`Архивировать: ${task.title}`}
        title="Архивировать"
        onClick={() => onStatusChange("archived")}
        disabled={isPending}
      >
        <Archive size={15} aria-hidden="true" />
      </button>
    </li>
  );
}

function TaskGroup({
  title,
  tasks,
  today,
  tone = "default",
  emptyMessage,
  pendingTaskId,
  onOpenTask,
  onStatusChange
}: TaskGroupProps) {
  return (
    <section className={`today-group today-group--${tone}`}>
      <div className="today-group__header">
        <h2>{title}</h2>
        <span>{tasks.length}</span>
      </div>
      {tasks.length > 0 ? (
        <ul className="today-task-list">
          {tasks.map((task) => (
            <TaskRow
              key={task.id}
              task={task}
              today={today}
              isPending={pendingTaskId === task.id}
              onOpen={() => onOpenTask(task.id)}
              onStatusChange={(status) => onStatusChange(task.id, status)}
            />
          ))}
        </ul>
      ) : (
        <p className="today-group__empty">{emptyMessage}</p>
      )}
    </section>
  );
}

function AttentionCard({
  todayDeadline,
  overdue
}: {
  todayDeadline: number;
  overdue: number;
}) {
  return (
    <section className="today-compact-card today-attention-card">
      <header>
        <h2>Требует внимания</h2>
        <AlertCircle size={18} aria-hidden="true" />
      </header>
      <Link
        className="today-attention-row today-attention-row--link"
        to="/app/planning?deadline_preset=today&statuses=todo"
      >
        <span>Дедлайн сегодня</span>
        <strong className="today-attention-row--warning">{todayDeadline}</strong>
        <ChevronRight size={16} aria-hidden="true" />
      </Link>
      <Link
        className="today-attention-row today-attention-row--link"
        to="/app/planning?deadline_preset=overdue&statuses=todo"
      >
        <span>Просрочено</span>
        <strong className="today-attention-row--danger">{overdue}</strong>
        <ChevronRight size={16} aria-hidden="true" />
      </Link>
    </section>
  );
}

function CompactTaskCard({
  title,
  tasks,
  today,
  showDeadline = false,
  moreTo,
  onOpenTask
}: {
  title: string;
  tasks: Task[];
  today: string;
  showDeadline?: boolean;
  moreTo: string;
  onOpenTask: (taskId: string) => void;
}) {
  const isTruncated = tasks.length > 3;
  const visibleTasks = tasks.slice(0, 3);

  return (
    <section className="today-compact-card">
      <header>
        <h2>{title}</h2>
        <span>{tasks.length}</span>
      </header>
      {visibleTasks.length > 0 ? (
        <>
          <ul className="today-compact-list">
            {visibleTasks.map((task) => (
              <li key={task.id}>
                <button type="button" onClick={() => onOpenTask(task.id)}>
                  {task.title}
                </button>
                <span>
                  {showDeadline && task.deadline_date
                    ? `${formatTaskDate(task.deadline_date, today)} · `
                    : ""}
                  {task.planned_time ?? "—"}
                </span>
              </li>
            ))}
          </ul>
          {isTruncated ? (
            <Link className="today-compact-card__more" to={moreTo}>
              Показать больше
            </Link>
          ) : null}
        </>
      ) : (
        <p className="today-compact-card__empty">Задач пока нет.</p>
      )}
    </section>
  );
}

function TodayContent({
  data,
  sort,
  pendingTaskId,
  onOpenTask,
  onStatusChange,
  onSortChange
}: {
  data: TodayViewResponse;
  sort: TodaySort;
  pendingTaskId: string | null;
  onOpenTask: (taskId: string) => void;
  onStatusChange: (taskId: string, status: TaskStatusCode) => void;
  onSortChange: (sort: TodaySort) => void;
}) {
  const { blocks, summary } = data;
  const summaryCards: SummaryCard[] = [
    {
      label: "Сегодня",
      value: blocks.planned_today.length,
      icon: CalendarDays,
      tone: "primary",
      to: "/app/planning?preset=today&statuses=todo"
    },
    {
      label: "Входящие",
      value: blocks.inbox.length,
      icon: Inbox,
      tone: "neutral",
      to: "/app/planning?preset=no_date&statuses=todo"
    },
    {
      label: "Дедлайн сегодня",
      value: summary.today_deadline,
      icon: Clock3,
      tone: "warning",
      to: "/app/planning?deadline_preset=today&statuses=todo"
    },
    {
      label: "Просрочено",
      value: summary.overdue,
      icon: AlertCircle,
      tone: "danger",
      to: "/app/planning?deadline_preset=overdue&statuses=todo"
    },
    {
      label: "Выполнено",
      value: summary.done_today,
      icon: CheckCircle2,
      tone: "success",
      to: "/app/planning?preset=all&statuses=done"
    }
  ];
  const taskCount = Object.values(blocks).reduce((total, tasks) => total + tasks.length, 0);
  const plannedToday = sortTasks(blocks.planned_today, sort);
  const doneToday = sortTasks(blocks.done_today, sort);
  const inbox = sortTasks(blocks.inbox, sort);
  const soonDeadline = sortTasks(blocks.soon_deadline, sort);

  return (
    <>
      <div className="today-summary" aria-label="Сводка задач">
        {summaryCards.map(({ label, value, icon: Icon, tone, to }) => {
          const content = (
            <>
              <div>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
              <Icon size={22} strokeWidth={1.8} aria-hidden="true" />
            </>
          );

          return to ? (
            <Link className={`today-summary-card today-summary-card--${tone}`} to={to} key={label}>
              {content}
            </Link>
          ) : (
            <article className={`today-summary-card today-summary-card--${tone}`} key={label}>
              {content}
            </article>
          );
        })}
      </div>

      {taskCount === 0 ? (
        <section className="today-empty-state">
          <CheckCircle2 size={30} strokeWidth={1.6} aria-hidden="true" />
          <h2>На сегодня всё спокойно</h2>
          <p>Запланированных, входящих и срочных задач пока нет.</p>
        </section>
      ) : (
        <div className="today-board">
          <div className="today-board__main">
            <div className="today-board__toolbar">
              <span>Задачи</span>
              <label>
                <span>Сортировка</span>
                <select
                  value={sort}
                  onChange={(event) => onSortChange(event.target.value as TodaySort)}
                >
                  {todaySortOptions.map((option) => (
                    <option value={option.value} key={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <TaskGroup
              title="План на сегодня"
              tasks={plannedToday}
              today={data.date}
              emptyMessage="Запланированных задач нет."
              pendingTaskId={pendingTaskId}
              onOpenTask={onOpenTask}
              onStatusChange={onStatusChange}
            />
            <TaskGroup
              title="Выполнено сегодня"
              tasks={doneToday}
              today={data.date}
              tone="success"
              emptyMessage="Выполненных задач пока нет."
              pendingTaskId={pendingTaskId}
              onOpenTask={onOpenTask}
              onStatusChange={onStatusChange}
            />
          </div>

          <aside className="today-board__aside" aria-label="Дополнительные блоки задач">
            <AttentionCard
              todayDeadline={blocks.today_deadline.length}
              overdue={blocks.overdue.length}
            />
            <CompactTaskCard
              title="Входящие"
              tasks={inbox}
              today={data.date}
              moreTo="/app/planning?preset=no_date&statuses=todo"
              onOpenTask={onOpenTask}
            />
            <CompactTaskCard
              title="Скоро дедлайн"
              tasks={soonDeadline}
              today={data.date}
              showDeadline
              moreTo="/app/planning?deadline_preset=soon&statuses=todo"
              onOpenTask={onOpenTask}
            />
          </aside>
        </div>
      )}
    </>
  );
}

export function TodayPage() {
  const todayViewQuery = useTodayViewQuery();
  const quickUpdateMutation = useUpdateTaskMutation();
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [sort, setSort] = useState<TodaySort>("created_at_desc");
  const pendingTaskId = quickUpdateMutation.isPending
    ? quickUpdateMutation.variables.taskId
    : null;

  function handleQuickStatusChange(taskId: string, status: TaskStatusCode) {
    quickUpdateMutation.mutate({ taskId, payload: { status } });
  }

  return (
    <>
      <section className="today-page">
        <header className="today-page__header">
          <div>
            <h1>Сегодня</h1>
            <p>
              {todayViewQuery.data ? formatPageDate(todayViewQuery.data.date) : "Ваш план на день"}
            </p>
          </div>
          <button
            className="today-page__new-task"
            type="button"
            onClick={() => setIsCreateTaskOpen(true)}
          >
            <Plus size={18} aria-hidden="true" />
            Новая задача
          </button>
        </header>

        {todayViewQuery.isPending ? (
          <div className="today-loading" aria-live="polite" aria-label="Загрузка задач">
            <div className="today-loading__cards" aria-hidden="true">
              {Array.from({ length: 5 }, (_, index) => (
                <span key={index} />
              ))}
            </div>
            <div className="today-loading__panel" aria-hidden="true" />
            <p>Загружаем задачи на сегодня…</p>
          </div>
        ) : null}

        {todayViewQuery.isError ? (
          <section className="today-error" role="alert">
            <AlertCircle size={28} aria-hidden="true" />
            <div>
              <h2>Не удалось загрузить задачи</h2>
              <p>Проверьте подключение и попробуйте ещё раз.</p>
            </div>
            <button type="button" onClick={() => void todayViewQuery.refetch()}>
              <RotateCcw size={16} aria-hidden="true" />
              Повторить
            </button>
          </section>
        ) : null}

        {quickUpdateMutation.isError ? (
          <div className="today-quick-error" role="alert">
            Не удалось изменить статус задачи. Попробуйте ещё раз.
          </div>
        ) : null}

        {todayViewQuery.data ? (
          <TodayContent
            data={todayViewQuery.data}
            sort={sort}
            pendingTaskId={pendingTaskId}
            onOpenTask={setSelectedTaskId}
            onStatusChange={handleQuickStatusChange}
            onSortChange={setSort}
          />
        ) : null}
      </section>
      {isCreateTaskOpen ? (
        <CreateTaskDrawer onClose={() => setIsCreateTaskOpen(false)} />
      ) : null}
      {selectedTaskId ? (
        <TaskDetailsDrawer taskId={selectedTaskId} onClose={() => setSelectedTaskId(null)} />
      ) : null}
    </>
  );
}
