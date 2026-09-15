import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Archive,
  CalendarDays,
  Plus,
  RotateCcw,
  Search
} from "lucide-react";

import type { Task, TaskListParams, TaskSort } from "../entities/task/types";
import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import { TaskDetailsDrawer } from "../features/tasks/task-details-drawer";
import {
  useDeleteTaskMutation,
  useTasksQuery,
  useUpdateTaskMutation
} from "../features/tasks/queries";
import { Pagination } from "../shared/ui/pagination";
import { DatePickerPopover } from "../shared/ui/date-picker-popover";
import { InputGroup, InputGroupAddon, InputGroupInput } from "../shared/ui/input-group";
import { SelectCombobox } from "../shared/ui/select-combobox";

const sortOptions: { value: TaskSort; label: string }[] = [
  { value: "created_at_desc", label: "Сначала новые задачи" },
  { value: "created_at_asc", label: "Сначала старые задачи" }
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
  onDeleteConfirm,
  onOpen
}: {
  task: Task;
  isRestoring: boolean;
  isDeleting: boolean;
  isDeleteConfirmOpen: boolean;
  onRestore: () => void;
  onDeleteRequest: () => void;
  onDeleteCancel: () => void;
  onDeleteConfirm: () => void;
  onOpen: () => void;
}) {
  const deleteButtonRef = useRef<HTMLButtonElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  const restoreFocusRef = useRef(false);

  useEffect(() => {
    if (isDeleteConfirmOpen) {
      cancelButtonRef.current?.focus({ preventScroll: true });
    } else if (restoreFocusRef.current) {
      restoreFocusRef.current = false;
      deleteButtonRef.current?.focus({ preventScroll: true });
    }
  }, [isDeleteConfirmOpen]);

  function cancelDelete() {
    if (isDeleting) return;
    restoreFocusRef.current = true;
    onDeleteCancel();
  }

  return (
    <tr>
      <td>
        <span className="archive-task-title">
          <button type="button" title={task.title} onClick={onOpen}>
            {task.title}
          </button>
        </span>
      </td>
      <td>
        <span className={task.planned_date ? "archive-date" : "archive-date archive-date--muted"}>
          {task.planned_date ? <CalendarDays size={14} aria-hidden="true" /> : null}
          {task.planned_date ? formatDate(task.planned_date) : "Без даты"}
          {task.planned_time ? `, ${task.planned_time.slice(0, 5)}` : ""}
        </span>
      </td>
      <td>
        <span className="archive-date archive-date--muted">{formatDate(task.deadline_date)}</span>
      </td>
      <td>
        <span className="archive-date archive-date--muted">{formatDateTime(task.archived_at)}</span>
      </td>
      <td className="archive-actions">
        <span className="archive-action-switch" onKeyDown={(event) => {
          if (event.key === "Escape" && isDeleteConfirmOpen && !isDeleting) {
            event.preventDefault();
            event.stopPropagation();
            cancelDelete();
          }
        }}>
          <span
            id={`archive-delete-${task.id}`}
            role="group"
            aria-label={`Подтверждение удаления: ${task.title}`}
            aria-busy={isDeleting}
            className={`archive-delete-confirm${isDeleteConfirmOpen ? " archive-action-layer--visible" : ""}`}
            aria-hidden={!isDeleteConfirmOpen}
            inert={!isDeleteConfirmOpen}
          >
            <span>Удалить?</span>
            <button ref={cancelButtonRef} type="button" onClick={cancelDelete} disabled={isDeleting}>
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
          <span
            className={`archive-action-group${!isDeleteConfirmOpen ? " archive-action-layer--visible" : ""}`}
            aria-hidden={isDeleteConfirmOpen}
            inert={isDeleteConfirmOpen}
          >
            <button
              className="archive-action archive-action--restore"
              type="button"
              onClick={onRestore}
              disabled={isRestoring || isDeleting}
            >
              {isRestoring ? "Возвращаем…" : "Вернуть"}
            </button>
            <button
              ref={deleteButtonRef}
              className="archive-action archive-action--danger"
              type="button"
              aria-expanded={isDeleteConfirmOpen}
              aria-controls={`archive-delete-${task.id}`}
              onClick={onDeleteRequest}
              disabled={isRestoring || isDeleting}
            >
              Удалить
            </button>
          </span>
        </span>
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
  const [plannedDate, setPlannedDate] = useState("");
  const [deleteConfirmTaskId, setDeleteConfirmTaskId] = useState<string | null>(null);
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
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
    statuses: ["todo", "done"],
    archived: true,
    planned_date: plannedDate || undefined,
    q: debouncedSearch,
    sort,
    limit,
    offset
  };
  const tasksQuery = useTasksQuery(queryParams);
  const total = tasksQuery.data?.pagination.total ?? 0;
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
    restoreTaskMutation.mutate({ taskId, payload: { archived: false } });
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
          <InputGroup className="archive-search">
            <InputGroupInput
              type="search"
              aria-label="Поиск в архиве по названию и описанию"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Поиск по названию и описанию"
            />
            <InputGroupAddon aria-hidden="true"><Search size={16} /></InputGroupAddon>
            {search.trim() ? <InputGroupAddon align="inline-end" className="ui-input-group__results" aria-live="polite">
              Найдено: {tasksQuery.isFetching ? "…" : tasksQuery.data ? total : "—"}
            </InputGroupAddon> : null}
          </InputGroup>
          <details className="archive-filters">
            <summary>Фильтры</summary>
            <div className="archive-filters__body">
              <DatePickerPopover mode="single" label="Плановая дата" buttonLabel={plannedDate ? formatDate(plannedDate) : "Выберите дату"} value={plannedDate} onChange={(value) => { setPlannedDate(value); setOffset(0); }} />
              <button type="button" onClick={() => { setPlannedDate(""); setOffset(0); }}>Сбросить</button>
            </div>
          </details>
          <div className="archive-sort">
            <span>Сортировка</span>
            <SelectCombobox label="Сортировка" value={sort} options={sortOptions} onChange={(value) => changeSort(value as TaskSort)} />
          </div>
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
                        <span className="archive-table__heading-task">Задача</span>
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
                        onOpen={() => setSelectedTaskId(task.id)}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="archive-empty">
                <Archive size={30} aria-hidden="true" />
                <h2>Архив пока пуст</h2>
                <p>Здесь появятся задачи, которые вы отправите в архив.</p>
              </div>
            )}

            <Pagination className="archive-pagination" label="Всего в архиве" total={total} limit={limit} offset={offset} onLimitChange={changeLimit} onOffsetChange={setOffset} />
          </section>
        ) : null}
      {selectedTaskId ? (
        <TaskDetailsDrawer taskId={selectedTaskId} onClose={() => setSelectedTaskId(null)} />
      ) : null}
      {isCreateTaskOpen ? (
        <CreateTaskDrawer onClose={() => setIsCreateTaskOpen(false)} />
      ) : null}
    </section>
  );
}
