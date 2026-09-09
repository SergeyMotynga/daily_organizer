import { useEffect, useState } from "react";
import {
  AlertCircle,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  Clock3,
  MoreVertical,
  Plus,
  Repeat2,
  RotateCcw,
  Search,
  Settings2
} from "lucide-react";
import { useSearchParams } from "react-router";

import type {
  Task,
  TaskDeadlinePreset,
  TaskListParams,
  TaskListPreset,
  TaskSort,
  TaskStatusCode
} from "../entities/task/types";
import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import { TaskDetailsDrawer } from "../features/tasks/task-details-drawer";
import {
  useRecurrenceCompletionMutation,
  useTasksQuery,
  useTaskStatusesQuery,
  useUpdateTaskMutation
} from "../features/tasks/queries";
import { getRecurrenceLabel, isTaskRecurring } from "../features/tasks/recurrence";

const presets: { value: TaskListPreset; label: string }[] = [
  { value: "today", label: "Сегодня" },
  { value: "tomorrow", label: "Завтра" },
  { value: "week", label: "Эта неделя" },
  { value: "no_date", label: "Без даты" },
  { value: "all", label: "Все" }
];

const sortOptions: { value: TaskSort; label: string }[] = [
  { value: "deadline_date_asc", label: "Ближайшие дедлайны" },
  { value: "planned_date_asc", label: "По плановой дате" },
  { value: "created_at_desc", label: "Сначала новые" },
  { value: "created_at_asc", label: "Сначала старые" }
];

const deadlinePresetLabels: Record<TaskDeadlinePreset, string> = {
  overdue: "просрочено",
  today: "сегодня",
  soon: "в ближайшие 3 дня"
};

function getPreset(searchParams: URLSearchParams): TaskListPreset {
  const preset = searchParams.get("preset");
  return presets.some((option) => option.value === preset) ? (preset as TaskListPreset) : "all";
}

function getStatuses(searchParams: URLSearchParams): TaskStatusCode[] {
  const supportedStatuses: TaskStatusCode[] = ["todo", "done"];
  const statuses = searchParams
    .get("statuses")
    ?.split(",")
    .filter((status): status is TaskStatusCode =>
      supportedStatuses.includes(status as TaskStatusCode)
    );

  return statuses?.length ? statuses : ["todo", "done"];
}

function getSort(searchParams: URLSearchParams): TaskSort {
  const sort = searchParams.get("sort");
  return sortOptions.some((option) => option.value === sort)
    ? (sort as TaskSort)
    : "deadline_date_asc";
}

function getLimit(searchParams: URLSearchParams): number {
  const limit = Number(searchParams.get("limit"));
  return [10, 20, 50].includes(limit) ? limit : 20;
}

function getOffset(searchParams: URLSearchParams): number {
  const offset = Number(searchParams.get("offset"));
  return Number.isInteger(offset) && offset >= 0 ? offset : 0;
}

function getDeadlineDate(searchParams: URLSearchParams): string | undefined {
  const deadlineDate = searchParams.get("deadline_date");
  return deadlineDate && /^\d{4}-\d{2}-\d{2}$/.test(deadlineDate) ? deadlineDate : undefined;
}

function getDeadlinePreset(searchParams: URLSearchParams): TaskDeadlinePreset | undefined {
  const deadlinePreset = searchParams.get("deadline_preset");
  return deadlinePreset && deadlinePreset in deadlinePresetLabels
    ? (deadlinePreset as TaskDeadlinePreset)
    : undefined;
}

function getLocalDate(offset = 0): string {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatShortDate(date: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    timeZone: "UTC"
  })
    .format(new Date(`${date}T00:00:00Z`))
    .replace(".", "");
}

function formatUpdatedAt(date: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  })
    .format(new Date(date))
    .replace(".", "");
}

function getPlannedDateLabel(date: string | null): string {
  if (!date) {
    return "Без даты";
  }

  const today = getLocalDate();
  if (date === today) {
    return "Сегодня";
  }
  if (date === getLocalDate(1)) {
    return "Завтра";
  }

  const daysUntilWeekEnd = 7 - (new Date().getDay() || 7);
  if (date > today && date <= getLocalDate(daysUntilWeekEnd)) {
    return "Эта неделя";
  }
  if (date > getLocalDate(daysUntilWeekEnd) && date <= getLocalDate(daysUntilWeekEnd + 7)) {
    return "Следующая неделя";
  }

  return formatShortDate(date);
}

function getDeadlineTone(
  date: string | null,
  deadlineTime: string | null
): "danger" | "warning" | "default" {
  if (!date) {
    return "default";
  }
  const today = getLocalDate();
  const currentTime = new Date().toTimeString().slice(0, 5);
  if (date < today || (date === today && deadlineTime !== null && deadlineTime < currentTime)) {
    return "danger";
  }
  if (date <= getLocalDate(3)) {
    return "warning";
  }
  return "default";
}

function PlanningTaskRow({
  task,
  statusTitle,
  isPending,
  onOpen,
  onStatusChange
}: {
  task: Task;
  statusTitle: string;
  isPending: boolean;
  onOpen: () => void;
  onStatusChange: (status: TaskStatusCode) => void;
}) {
  const deadlineTone = getDeadlineTone(task.deadline_date, task.deadline_time);
  const isRecurring = isTaskRecurring(task);
  const hasOccurrence = Boolean(task.occurrence_date);
  const isDone = task.status === "done";
  const effectiveStatus = isDone ? "done" : "todo";
  const planningDate = task.occurrence_date ?? task.planned_date;

  return (
    <tr className={`planning-task-row planning-task-row--${deadlineTone}`}>
      <td className="planning-task-cell planning-task-cell--title">
        <button
          type="button"
          className={`planning-task-check planning-task-check--${effectiveStatus}`}
          aria-label={isDone ? `Вернуть в активные: ${task.title}` : `Выполнить: ${task.title}`}
          title={
            isRecurring && !hasOccurrence
              ? "Для выбранного периода нет occurrence"
              : isDone
                ? "Снять выполнение сегодня"
                : "Отметить выполненной"
          }
          disabled={isPending || (isRecurring && !hasOccurrence)}
          onClick={() => onStatusChange(isDone ? "todo" : "done")}
        >
          {isDone ? <Check size={11} strokeWidth={3} aria-hidden="true" /> : null}
        </button>
        <button type="button" title={task.title} onClick={onOpen}>
          {task.title}
        </button>
        {isRecurring ? (
          <span className="task-recurrence-badge">
            <Repeat2 size={13} aria-hidden="true" />
            {getRecurrenceLabel(task.recurrence_type_code, task.recurrence_interval)}
          </span>
        ) : null}
      </td>
      <td>
        <span className={`planning-status planning-status--${effectiveStatus}`}>{statusTitle}</span>
      </td>
      <td>
        <span className={planningDate ? "planning-date" : "planning-date planning-date--muted"}>
          <CalendarDays size={15} aria-hidden="true" />
          {getPlannedDateLabel(planningDate)} · {task.planned_time ?? "—"}
        </span>
      </td>
      <td>
        {task.deadline_date ? (
          <span className={`planning-deadline planning-deadline--${deadlineTone}`}>
            {formatShortDate(task.deadline_date)}
            <Clock3 size={15} aria-hidden="true" />
            {task.deadline_time ? <span>{task.deadline_time}</span> : null}
          </span>
        ) : (
          <span className="planning-date planning-date--muted">—</span>
        )}
      </td>
      <td className="planning-task-updated">{formatUpdatedAt(task.updated_at)}</td>
      <td className="planning-task-actions">
        <button type="button" aria-label={`Открыть задачу: ${task.title}`} onClick={onOpen}>
          <MoreVertical size={17} aria-hidden="true" />
        </button>
      </td>
    </tr>
  );
}

export function PlanningPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const preset = getPreset(searchParams);
  const selectedStatuses = getStatuses(searchParams);
  const search = searchParams.get("q") ?? "";
  const sort = getSort(searchParams);
  const limit = getLimit(searchParams);
  const offset = getOffset(searchParams);
  const deadlineDate = getDeadlineDate(searchParams);
  const deadlinePreset = getDeadlinePreset(searchParams);
  const timezone = deadlinePreset
    ? Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
    : undefined;
  const hasActiveFilters =
    preset !== "all" ||
    search.trim().length > 0 ||
    Boolean(deadlineDate) ||
    Boolean(deadlinePreset) ||
    selectedStatuses.length !== 2 ||
    !selectedStatuses.includes("todo") ||
    !selectedStatuses.includes("done");
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const statusesQuery = useTaskStatusesQuery();
  const quickUpdateMutation = useUpdateTaskMutation();
  const recurrenceCompletionMutation = useRecurrenceCompletionMutation();
  const pendingTaskId = quickUpdateMutation.isPending
    ? quickUpdateMutation.variables.taskId
    : recurrenceCompletionMutation.isPending
      ? recurrenceCompletionMutation.variables.taskId
      : null;

  const queryParams: TaskListParams = {
    preset,
    statuses: selectedStatuses,
    deadline_date: deadlineDate,
    deadline_preset: deadlinePreset,
    timezone,
    q: search,
    sort,
    limit,
    offset
  };
  const tasksQuery = useTasksQuery(queryParams);
  const total = tasksQuery.data?.pagination.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / limit));
  const currentPage = Math.floor(offset / limit) + 1;

  useEffect(() => {
    if (total > 0 && offset >= total) {
      const nextSearchParams = new URLSearchParams(searchParams);
      nextSearchParams.set("offset", String(Math.max(0, (Math.ceil(total / limit) - 1) * limit)));
      setSearchParams(nextSearchParams, { replace: true });
    }
  }, [limit, offset, searchParams, setSearchParams, total]);

  function updateSearchParams(
    updates: Record<string, string | null>,
    options: { replace?: boolean } = {}
  ) {
    const nextSearchParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (value === null || value === "") {
        nextSearchParams.delete(key);
      } else {
        nextSearchParams.set(key, value);
      }
    });
    setSearchParams(nextSearchParams, { replace: options.replace });
  }

  function changePreset(value: TaskListPreset) {
    updateSearchParams({
      preset: value,
      deadline_date: null,
      deadline_preset: null,
      offset: null
    });
  }

  function toggleStatus(status: TaskStatusCode) {
    const nextStatuses = selectedStatuses.includes(status)
      ? selectedStatuses.length === 1
        ? selectedStatuses
        : selectedStatuses.filter((item) => item !== status)
      : [...selectedStatuses, status];
    updateSearchParams({ statuses: nextStatuses.join(","), offset: null });
  }

  function changeSort(value: TaskSort) {
    updateSearchParams({ sort: value, offset: null });
  }

  function changeLimit(value: number) {
    updateSearchParams({ limit: String(value), offset: null });
  }

  function resetFilters() {
    const nextSearchParams = new URLSearchParams(searchParams);
    ["preset", "statuses", "q", "deadline_date", "deadline_preset", "offset"].forEach((key) =>
      nextSearchParams.delete(key)
    );
    setSearchParams(nextSearchParams);
  }

  function changeTaskStatus(task: Task, status: TaskStatusCode) {
    if (isTaskRecurring(task) && task.occurrence_date) {
      recurrenceCompletionMutation.mutate({
        taskId: task.id,
        occurrenceDate: task.occurrence_date,
        completed: status === "done"
      });
      return;
    }
    quickUpdateMutation.mutate({ taskId: task.id, payload: { status } });
  }

  const statusTitles = new Map(
    statusesQuery.data?.map((status) => [status.code, status.title] as const) ?? []
  );

  return (
    <>
      <section className="planning-page">
        <header className="planning-page__header">
          <div>
            <h1>Планирование</h1>
            <p>Все задачи, даты и фильтры</p>
          </div>
          <button
            className="planning-page__new-task"
            type="button"
            onClick={() => setIsCreateTaskOpen(true)}
          >
            <Plus size={18} aria-hidden="true" />
            Новая задача
          </button>
        </header>

        <div className="planning-toolbar">
          <div className="planning-filter planning-filter--presets">
            <span className="planning-filter__label">Быстрые фильтры</span>
            <div className="planning-preset-options">
              {presets.map((option) => (
                <button
                  className={preset === option.value ? "planning-option--active" : undefined}
                  type="button"
                  key={option.value}
                  aria-pressed={preset === option.value}
                  onClick={() => changePreset(option.value)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="planning-filter planning-filter--statuses">
            <span className="planning-filter__label">Статусы</span>
            {statusesQuery.isPending ? <span className="planning-filter__state">Загрузка…</span> : null}
            {statusesQuery.isError ? (
              <button
                className="planning-filter__retry"
                type="button"
                onClick={() => void statusesQuery.refetch()}
              >
                Повторить
              </button>
            ) : null}
            {statusesQuery.data ? (
              <div className="planning-status-options">
                {[...statusesQuery.data]
                  .sort((left, right) => left.sort_order - right.sort_order)
                  .map((status) => (
                    <label key={status.code}>
                      <input
                        type="checkbox"
                        checked={selectedStatuses.includes(status.code)}
                        onChange={() => toggleStatus(status.code)}
                      />
                      <span>{status.title}</span>
                    </label>
                  ))}
              </div>
            ) : null}
          </div>

          <label className="planning-filter planning-search">
            <span>Поиск</span>
            <span className="planning-search__control">
              <Search size={17} aria-hidden="true" />
              <input
                type="search"
                value={search}
                onChange={(event) =>
                  updateSearchParams(
                    { q: event.target.value || null, offset: null },
                    { replace: true }
                  )
                }
                placeholder="Поиск по задачам"
              />
            </span>
          </label>

          <label className="planning-filter planning-sort">
            <span>Сортировка</span>
            <select value={sort} onChange={(event) => changeSort(event.target.value as TaskSort)}>
              {sortOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {hasActiveFilters ? (
          <div className="planning-active-filter" role="status">
            <span>
              {deadlinePreset
                ? `Дедлайн: ${deadlinePresetLabels[deadlinePreset]}`
                : deadlineDate
                ? `Дедлайн: ${searchParams.get("deadline_date") === "today" ? "сегодня" : formatShortDate(deadlineDate)}`
                : "Применены фильтры"}
            </span>
            <button type="button" onClick={resetFilters}>
              Сбросить фильтры
            </button>
          </div>
        ) : null}

        {quickUpdateMutation.isError || recurrenceCompletionMutation.isError ? (
          <div className="planning-mutation-error" role="alert">
            Не удалось изменить статус задачи. Попробуйте ещё раз.
          </div>
        ) : null}

        {tasksQuery.isPending ? (
          <div className="planning-loading" aria-live="polite" aria-label="Загрузка задач">
            <div aria-hidden="true" />
            <span>Загружаем задачи…</span>
          </div>
        ) : null}

        {tasksQuery.isError ? (
          <section className="planning-error" role="alert">
            <AlertCircle size={26} aria-hidden="true" />
            <div>
              <h2>Не удалось загрузить задачи</h2>
              <p>Проверьте подключение и попробуйте ещё раз.</p>
            </div>
            <button type="button" onClick={() => void tasksQuery.refetch()}>
              <RotateCcw size={16} aria-hidden="true" />
              Повторить
            </button>
          </section>
        ) : null}

        {tasksQuery.data ? (
          <section className="planning-table-card" aria-busy={tasksQuery.isFetching}>
            {tasksQuery.data.items.length > 0 ? (
              <div className="planning-table-scroll">
                <table className="planning-table">
                  <thead>
                    <tr>
                      <th>
                        <span className="planning-table__heading-task">Задача</span>
                      </th>
                      <th>Статус</th>
                      <th>Когда делать</th>
                      <th>Дедлайн</th>
                      <th>Обновлено</th>
                      <th className="planning-table__settings">
                        <Settings2 size={15} aria-label="Настройки таблицы" />
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {tasksQuery.data.items.map((task) => (
                      <PlanningTaskRow
                        key={task.id}
                        task={task}
                        statusTitle={
                          isTaskRecurring(task)
                            ? task.status === "done"
                              ? "Выполнена"
                              : "Активная"
                            : statusTitles.get(task.status) ?? task.status
                        }
                        isPending={pendingTaskId === task.id}
                        onOpen={() => setSelectedTaskId(task.id)}
                        onStatusChange={(status) => changeTaskStatus(task, status)}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="planning-empty">
                <CalendarDays size={28} aria-hidden="true" />
                <h2>Задачи не найдены</h2>
                <p>Измените фильтры или создайте новую задачу.</p>
              </div>
            )}

            <footer className="planning-pagination">
              <span>Всего задач: {total}</span>
              <div>
                <label>
                  <span>На странице</span>
                  <select value={limit} onChange={(event) => changeLimit(Number(event.target.value))}>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                </label>
                <button
                  type="button"
                  aria-label="Предыдущая страница"
                  disabled={currentPage === 1}
                  onClick={() =>
                    updateSearchParams({ offset: String(Math.max(0, offset - limit)) })
                  }
                >
                  <ChevronLeft size={17} aria-hidden="true" />
                </button>
                <span className="planning-pagination__page">
                  {currentPage} / {pageCount}
                </span>
                <button
                  type="button"
                  aria-label="Следующая страница"
                  disabled={currentPage >= pageCount}
                  onClick={() => updateSearchParams({ offset: String(offset + limit) })}
                >
                  <ChevronRight size={17} aria-hidden="true" />
                </button>
              </div>
            </footer>
          </section>
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
