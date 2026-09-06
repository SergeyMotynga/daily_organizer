import { useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Inbox,
  Plus,
  RotateCcw
} from "lucide-react";

import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import { useTodayViewQuery } from "../features/today/queries";
import type { Task, TodayViewResponse } from "../features/today/types";

type SummaryCard = {
  label: string;
  value: number;
  icon: LucideIcon;
  tone: "primary" | "neutral" | "warning" | "danger" | "success";
};

type TaskGroupProps = {
  title: string;
  tasks: Task[];
  today: string;
  tone?: "default" | "danger" | "warning" | "success";
  emptyMessage: string;
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

function TaskRow({ task, today }: { task: Task; today: string }) {
  const isDone = task.status === "done";
  const displayDate = task.deadline_date ?? task.planned_date;

  return (
    <li className={isDone ? "today-task today-task--done" : "today-task"}>
      <span className="today-task__check" aria-hidden="true">
        {isDone ? <CheckCircle2 size={17} /> : null}
      </span>
      <span className="today-task__title">{task.title}</span>
      {displayDate ? (
        <span className="today-task__date">
          <CalendarDays size={15} />
          {formatTaskDate(displayDate, today)}
        </span>
      ) : (
        <span className="today-task__date today-task__date--muted">Без даты</span>
      )}
    </li>
  );
}

function TaskGroup({
  title,
  tasks,
  today,
  tone = "default",
  emptyMessage
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
            <TaskRow key={task.id} task={task} today={today} />
          ))}
        </ul>
      ) : (
        <p className="today-group__empty">{emptyMessage}</p>
      )}
    </section>
  );
}

function TodayContent({ data }: { data: TodayViewResponse }) {
  const { blocks, summary } = data;
  const summaryCards: SummaryCard[] = [
    {
      label: "Активные",
      value: summary.total_active,
      icon: CalendarDays,
      tone: "primary"
    },
    { label: "Входящие", value: blocks.inbox.length, icon: Inbox, tone: "neutral" },
    {
      label: "Дедлайн сегодня",
      value: summary.today_deadline,
      icon: Clock3,
      tone: "warning"
    },
    { label: "Просрочено", value: summary.overdue, icon: AlertCircle, tone: "danger" },
    { label: "Выполнено", value: summary.done_today, icon: CheckCircle2, tone: "success" }
  ];
  const taskCount = Object.values(blocks).reduce((total, tasks) => total + tasks.length, 0);

  return (
    <>
      <div className="today-summary" aria-label="Сводка задач">
        {summaryCards.map(({ label, value, icon: Icon, tone }) => (
          <article className={`today-summary-card today-summary-card--${tone}`} key={label}>
            <div>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
            <Icon size={22} strokeWidth={1.8} aria-hidden="true" />
          </article>
        ))}
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
            <TaskGroup
              title="План на сегодня"
              tasks={blocks.planned_today}
              today={data.date}
              emptyMessage="Запланированных задач нет."
            />
            <TaskGroup
              title="Выполнено сегодня"
              tasks={blocks.done_today}
              today={data.date}
              tone="success"
              emptyMessage="Выполненных задач пока нет."
            />
          </div>

          <aside className="today-board__aside" aria-label="Дополнительные блоки задач">
            <TaskGroup
              title="Дедлайн сегодня"
              tasks={blocks.today_deadline}
              today={data.date}
              tone="warning"
              emptyMessage="Срочных дедлайнов нет."
            />
            <TaskGroup
              title="Просрочено"
              tasks={blocks.overdue}
              today={data.date}
              tone="danger"
              emptyMessage="Просроченных задач нет."
            />
            <TaskGroup
              title="Входящие"
              tasks={blocks.inbox}
              today={data.date}
              emptyMessage="Входящих задач нет."
            />
            <TaskGroup
              title="Скоро дедлайн"
              tasks={blocks.soon_deadline}
              today={data.date}
              emptyMessage="Ближайших дедлайнов нет."
            />
          </aside>
        </div>
      )}
    </>
  );
}

export function TodayPage() {
  const todayViewQuery = useTodayViewQuery();
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);

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

        {todayViewQuery.data ? <TodayContent data={todayViewQuery.data} /> : null}
      </section>
      {isCreateTaskOpen ? (
        <CreateTaskDrawer onClose={() => setIsCreateTaskOpen(false)} />
      ) : null}
    </>
  );
}
