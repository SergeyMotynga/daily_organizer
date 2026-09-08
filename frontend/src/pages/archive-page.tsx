import { useEffect, useState } from "react";
import {
  AlertCircle,
  Archive,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Plus,
  RotateCcw,
  Search
} from "lucide-react";

import type { Task, TaskListParams, TaskSort } from "../entities/task/types";
import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import {
  useDeleteTaskMutation,
  useTasksQuery,
  useUpdateTaskMutation
} from "../features/tasks/queries";

const sortOptions: { value: TaskSort; label: string }[] = [
  { value: "created_at_desc", label: "Сначала новые задачи" },
  { value: "created_at_asc", label: "Сначала старые задачи" },
  { value: "planned_date_asc", label: "По плановой дате" },
  { value: "deadline_date_asc", label: "По дедлайну" }
];

function formatDate(date: string | null): string {
  if (!date) {
    return "—";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC"
  })
    .format(new Date(`${date}T00:00:00Z`))
    .replace(".", "");
}

function formatDateTime(date: string | null): string {
  if (!date) {
    return "—";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  })
    .format(new Date(date))
    .replace(".", "");
}

function ArchiveTaskRow({
  task,
  isRestoring,
  isDeleting,
  isDeleteConfirmOpen,
  onRestore,
  onDeleteRequest,
  onDeleteCancel,
  onDeleteConfirm
}: {
  task: Task;
  isRestoring: boolean;
  isDeleting: boolean;
  isDeleteConfirmOpen: boolean;
  onRestore: () => void;
  onDeleteRequest: () => void;
  onDeleteCancel: () => void;
  onDeleteConfirm: () => void;
}) {
  return (
    <tr>
      <td>
        <span className="archive-task-title">
          <span className="archive-task-check" aria-hidden="true" />
          <span title={task.title}>{task.title}</span>
        </span>
      </td>
      <td>
        <span className={task.planned_date ? "archive-date" : "archive-date archive-date--muted"}>
          {task.planned_date ? <CalendarDays size={14} aria-hidden="true" /> : null}
          {task.planned_date ? formatDate(task.planned_date) : "Без даты"}
        </span>
      </td>
      <td>
        <span className="archive-date archive-date--muted">{formatDate(task.deadline_date)}</span>
      </td>
      <td>
        <span className="archive-date archive-date--muted">{formatDateTime(task.archived_at)}</span>
      </td>
      <td className="archive-actions">
        {isDeleteConfirmOpen ? (
          <span className="archive-delete-confirm">
            <span>Удалить?</span>
            <button type="button" onClick={onDeleteCancel} disabled={isDeleting}>
              Нет
            </button>
            <button
              className="archive-action archive-action--danger"
              type="button"
              onClick={onDeleteConfirm}
              disabled={isDeleting}
            >
              {isDeleting ? "Удаляем…" : "Да"}
            </button>
          </span>
        ) : (
          <span className="archive-action-group">
            <button
              className="archive-action archive-action--restore"
              type="button"
              onClick={onRestore}
              disabled={isRestoring || isDeleting}
            >
              {isRestoring ? "Возвращаем…" : "Вернуть"}
            </button>
            <button
              className="archive-action archive-action--danger"
              type="button"
              onClick={onDeleteRequest}
              disabled={isRestoring || isDeleting}
            >
              Удалить
            </button>
          </span>
        )}
      </td>
    </tr>
  );
}

export function ArchivePage() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [sort, setSort] = useState<TaskSort>("created_at_desc");
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [deleteConfirmTaskId, setDeleteConfirmTaskId] = useState<string | null>(null);
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const restoreTaskMutation = useUpdateTaskMutation();
  const deleteTaskMutation = useDeleteTaskMutation();

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedSearch(search);
      setOffset(0);
    }, 300);
    return () => window.clearTimeout(timeoutId);
  }, [search]);

  const queryParams: TaskListParams = {
    preset: "all",
    statuses: ["archived"],
    q: debouncedSearch,
    sort,
    limit,
    offset
  };
  const tasksQuery = useTasksQuery(queryParams);
  const total = tasksQuery.data?.pagination.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / limit));
  const currentPage = Math.floor(offset / limit) + 1;
  const restoringTaskId = restoreTaskMutation.isPending
    ? restoreTaskMutation.variables.taskId
    : null;
  const deletingTaskId = deleteTaskMutation.isPending ? deleteTaskMutation.variables : null;

  useEffect(() => {
    if (total > 0 && offset >= total) {
      setOffset(Math.max(0, (Math.ceil(total / limit) - 1) * limit));
    }
  }, [limit, offset, total]);

  function changeSort(value: TaskSort) {
    setSort(value);
    setOffset(0);
  }

  function changeLimit(value: number) {
    setLimit(value);
    setOffset(0);
  }

  function restoreTask(taskId: string) {
    restoreTaskMutation.mutate({ taskId, payload: { status: "todo" } });
  }

  async function deleteTask(taskId: string) {
    try {
      await deleteTaskMutation.mutateAsync(taskId);
      setDeleteConfirmTaskId(null);
    } catch {
      // Ошибка mutation отображается над таблицей.
    }
  }

  return (
    <>
      <section className="archive-page">
        <header className="archive-page__header">
          <div>
            <h1>Архив</h1>
            <p>Завершённые и скрытые задачи</p>
          </div>
          <button
            className="archive-page__new-task"
            type="button"
            onClick={() => setIsCreateTaskOpen(true)}
          >
            <Plus size={18} aria-hidden="true" />
            Новая задача
          </button>
        </header>

        <div className="archive-toolbar">
          <label className="archive-search">
            <Search size={17} aria-hidden="true" />
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Поиск по архиву"
            />
          </label>
          <label className="archive-sort">
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

        {restoreTaskMutation.isError || deleteTaskMutation.isError ? (
          <div className="archive-mutation-error" role="alert">
            Не удалось изменить задачу. Попробуйте ещё раз.
          </div>
        ) : null}

        {tasksQuery.isPending ? (
          <div className="archive-loading" aria-live="polite" aria-label="Загрузка архива">
            <div aria-hidden="true" />
            <span>Загружаем архив…</span>
          </div>
        ) : null}

        {tasksQuery.isError ? (
          <section className="archive-error" role="alert">
            <AlertCircle size={26} aria-hidden="true" />
            <div>
              <h2>Не удалось загрузить архив</h2>
              <p>Проверьте подключение и попробуйте ещё раз.</p>
            </div>
            <button type="button" onClick={() => void tasksQuery.refetch()}>
              <RotateCcw size={16} aria-hidden="true" />
              Повторить
            </button>
          </section>
        ) : null}

        {tasksQuery.data ? (
          <section className="archive-table-card" aria-busy={tasksQuery.isFetching}>
            {tasksQuery.data.items.length > 0 ? (
              <div className="archive-table-scroll">
                <table className="archive-table">
                  <thead>
                    <tr>
                      <th>
                        <span className="archive-table__heading-task">
                          <span className="archive-task-check" aria-hidden="true" />
                          Задача
                        </span>
                      </th>
                      <th>Когда была запланирована</th>
                      <th>Дедлайн</th>
                      <th>Архивировано</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tasksQuery.data.items.map((task) => (
                      <ArchiveTaskRow
                        key={task.id}
                        task={task}
                        isRestoring={restoringTaskId === task.id}
                        isDeleting={deletingTaskId === task.id}
                        isDeleteConfirmOpen={deleteConfirmTaskId === task.id}
                        onRestore={() => restoreTask(task.id)}
                        onDeleteRequest={() => setDeleteConfirmTaskId(task.id)}
                        onDeleteCancel={() => setDeleteConfirmTaskId(null)}
                        onDeleteConfirm={() => void deleteTask(task.id)}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="archive-empty">
                <Archive size={30} aria-hidden="true" />
                <h2>Архив пока пуст</h2>
                <p>Здесь появятся завершённые и скрытые задачи.</p>
              </div>
            )}

            <footer className="archive-pagination">
              <span>Всего в архиве: {total}</span>
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
                <span className="archive-pagination__page">
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
    </>
  );
}
