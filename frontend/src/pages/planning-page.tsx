import { useEffect, useState } from "react";
import {
  AlertCircle,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock3,
  MoreVertical,
  Plus,
  RotateCcw,
  Search,
  Settings2
} from "lucide-react";

import type {
  Task,
  TaskListParams,
  TaskListPreset,
  TaskSort,
  TaskStatusCode
} from "../entities/task/types";
import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import { EditTaskDrawer } from "../features/tasks/edit-task-drawer";
import { useTasksQuery, useTaskStatusesQuery } from "../features/tasks/queries";

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

function getDeadlineTone(date: string | null): "danger" | "warning" | "default" {
  if (!date) {
    return "default";
  }
  if (date < getLocalDate()) {
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
  onOpen
}: {
  task: Task;
  statusTitle: string;
  onOpen: () => void;
}) {
  const deadlineTone = getDeadlineTone(task.deadline_date);

  return (
    <tr className={`planning-task-row planning-task-row--${deadlineTone}`}>
      <td className="planning-task-cell planning-task-cell--title">
        <span
          className={`planning-task-check planning-task-check--${task.status}`}
          aria-hidden="true"
        />
        <button type="button" onClick={onOpen}>
          {task.title}
        </button>
      </td>
      <td>
        <span className={`planning-status planning-status--${task.status}`}>{statusTitle}</span>
      </td>
      <td>
        <span className={task.planned_date ? "planning-date" : "planning-date planning-date--muted"}>
          <CalendarDays size={15} aria-hidden="true" />
          {getPlannedDateLabel(task.planned_date)}
        </span>
      </td>
      <td>
        {task.deadline_date ? (
          <span className={`planning-deadline planning-deadline--${deadlineTone}`}>
            {formatShortDate(task.deadline_date)}
            <Clock3 size={15} aria-hidden="true" />
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
  const [preset, setPreset] = useState<TaskListPreset>("all");
  const [selectedStatuses, setSelectedStatuses] = useState<TaskStatusCode[]>(["todo", "done"]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [sort, setSort] = useState<TaskSort>("deadline_date_asc");
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const statusesQuery = useTaskStatusesQuery();

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedSearch(search);
      setOffset(0);
    }, 300);
    return () => window.clearTimeout(timeoutId);
  }, [search]);

  const queryParams: TaskListParams = {
    preset,
    statuses: selectedStatuses,
    q: debouncedSearch,
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
      setOffset(Math.max(0, (Math.ceil(total / limit) - 1) * limit));
    }
  }, [limit, offset, total]);

  function changePreset(value: TaskListPreset) {
    setPreset(value);
    setOffset(0);
  }

  function toggleStatus(status: TaskStatusCode) {
    setSelectedStatuses((current) => {
      if (current.includes(status)) {
        return current.length === 1 ? current : current.filter((item) => item !== status);
      }
      return [...current, status];
    });
    setOffset(0);
  }

  function changeSort(value: TaskSort) {
    setSort(value);
    setOffset(0);
  }

  function changeLimit(value: number) {
    setLimit(value);
    setOffset(0);
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
                onChange={(event) => setSearch(event.target.value)}
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
                        <span className="planning-table__heading-task">
                          <span className="planning-task-check" aria-hidden="true" />
                          Задача
                        </span>
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
                        statusTitle={statusTitles.get(task.status) ?? task.status}
                        onOpen={() => setSelectedTaskId(task.id)}
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
                  onClick={() => setOffset(Math.max(0, offset - limit))}
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
                  onClick={() => setOffset(offset + limit)}
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
        <EditTaskDrawer taskId={selectedTaskId} onClose={() => setSelectedTaskId(null)} />
      ) : null}
    </>
  );
}
