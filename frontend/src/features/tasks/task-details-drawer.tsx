import { useEffect, useState } from "react";
import {
  AlertCircle,
  Archive,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Pencil,
  RotateCcw,
  Trash2,
  X
} from "lucide-react";

import type { TaskStatusCode } from "../../entities/task/types";
import { EditTaskDrawer } from "./edit-task-drawer";
import {
  useDeleteTaskMutation,
  useTaskQuery,
  useTaskStatusesQuery,
  useUpdateTaskMutation
} from "./queries";

type TaskDetailsDrawerProps = {
  taskId: string;
  onClose: () => void;
};

function formatDate(date: string | null): string {
  if (!date) {
    return "Не указана";
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

function formatTime(time: string | null): string {
  return time ? time.slice(0, 5) : "Время не указано";
}

function formatDateTime(date: string | null): string {
  if (!date) {
    return "Не указано";
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

export function TaskDetailsDrawer({ taskId, onClose }: TaskDetailsDrawerProps) {
  const taskQuery = useTaskQuery(taskId);
  const statusesQuery = useTaskStatusesQuery();
  const updateTaskMutation = useUpdateTaskMutation();
  const deleteTaskMutation = useDeleteTaskMutation();
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const isMutating = updateTaskMutation.isPending || deleteTaskMutation.isPending;

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isMutating) {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMutating, onClose]);

  if (isEditing) {
    return <EditTaskDrawer taskId={taskId} onClose={onClose} />;
  }

  const task = taskQuery.data;
  const statusTitle = task
    ? statusesQuery.data?.find((status) => status.code === task.status)?.title ?? task.status
    : "";

  async function changeStatus(status: TaskStatusCode) {
    try {
      await updateTaskMutation.mutateAsync({ taskId, payload: { status } });
    } catch {
      // Ошибка mutation отображается в drawer.
    }
  }

  async function handleDelete() {
    try {
      await deleteTaskMutation.mutateAsync(taskId);
      onClose();
    } catch {
      // Ошибка mutation отображается рядом с подтверждением.
    }
  }

  return (
    <div className="task-drawer-layer">
      <button
        className="task-drawer-backdrop"
        type="button"
        aria-label="Закрыть задачу"
        onClick={onClose}
        disabled={isMutating}
      />
      <aside
        className="task-drawer task-details"
        role="dialog"
        aria-modal="true"
        aria-labelledby="task-details-title"
      >
        <header className="task-drawer__header task-details__header">
          <span>Задача</span>
          <button
            className="task-drawer__close"
            type="button"
            aria-label="Закрыть"
            onClick={onClose}
            disabled={isMutating}
          >
            <X size={20} />
          </button>
        </header>

        {taskQuery.isPending ? (
          <div className="task-edit-state" aria-live="polite">
            <span className="task-edit-state__loader" aria-hidden="true" />
            <p>Загружаем задачу…</p>
          </div>
        ) : null}

        {taskQuery.isError ? (
          <div className="task-edit-state task-edit-state--error" role="alert">
            <AlertCircle size={24} aria-hidden="true" />
            <strong>Не удалось загрузить задачу</strong>
            <p>Проверьте подключение и попробуйте ещё раз.</p>
            <button type="button" onClick={() => void taskQuery.refetch()}>
              Повторить
            </button>
          </div>
        ) : null}

        {task ? (
          <div className="task-details__layout">
            <div className="task-details__body">
              <section className="task-details__intro">
                <h2 id="task-details-title">{task.title}</h2>
                <div>
                  <h3>Описание</h3>
                  {task.description ? (
                    <p className="task-details__description">{task.description}</p>
                  ) : (
                    <p className="task-details__description task-details__description--empty">
                      Описание не добавлено.
                    </p>
                  )}
                </div>
              </section>

              <dl className="task-details__meta">
                <div className="task-details__status-row">
                  <dt>Статус</dt>
                  <dd>
                    <span className={`task-details__status task-details__status--${task.status}`}>
                      {statusTitle}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>
                    <CalendarDays size={18} aria-hidden="true" />
                    Когда делать
                  </dt>
                  <dd>
                    {formatDate(task.planned_date)}, {formatTime(task.planned_time)}
                  </dd>
                </div>
                <div>
                  <dt>
                    <CalendarDays size={18} aria-hidden="true" />
                    Дедлайн
                  </dt>
                  <dd>{formatDate(task.deadline_date)}</dd>
                </div>
                <div>
                  <dt>
                    <Clock3 size={18} aria-hidden="true" />
                    Создано
                  </dt>
                  <dd>{formatDateTime(task.created_at)}</dd>
                </div>
                <div>
                  <dt>
                    <Clock3 size={18} aria-hidden="true" />
                    Обновлено
                  </dt>
                  <dd>{formatDateTime(task.updated_at)}</dd>
                </div>
                {task.completed_at ? (
                  <div>
                    <dt>
                      <CheckCircle2 size={18} aria-hidden="true" />
                      Выполнено
                    </dt>
                    <dd>{formatDateTime(task.completed_at)}</dd>
                  </div>
                ) : null}
                {task.archived_at ? (
                  <div>
                    <dt>
                      <Archive size={18} aria-hidden="true" />
                      Архивировано
                    </dt>
                    <dd>{formatDateTime(task.archived_at)}</dd>
                  </div>
                ) : null}
              </dl>

              {updateTaskMutation.isError ? (
                <div className="task-create-error" role="alert">
                  Не удалось изменить задачу. Попробуйте ещё раз.
                </div>
              ) : null}
            </div>

            <footer className="task-details__actions">
              <button
                className="task-details-action task-details-action--primary"
                type="button"
                onClick={() => setIsEditing(true)}
                disabled={isMutating}
              >
                <Pencil size={17} aria-hidden="true" />
                Редактировать
              </button>

              <div className="task-details__action-row">
                {task.status !== "archived" ? (
                  <button
                    className="task-details-action"
                    type="button"
                    onClick={() => void changeStatus(task.status === "done" ? "todo" : "done")}
                    disabled={isMutating}
                  >
                    {task.status === "done" ? (
                      <RotateCcw size={17} aria-hidden="true" />
                    ) : (
                      <CheckCircle2 size={17} aria-hidden="true" />
                    )}
                    {task.status === "done" ? "Вернуть в активные" : "Выполнить"}
                  </button>
                ) : null}

                <button
                  className="task-details-action"
                  type="button"
                  onClick={() => void changeStatus(task.status === "archived" ? "todo" : "archived")}
                  disabled={isMutating}
                >
                  {task.status === "archived" ? (
                    <RotateCcw size={17} aria-hidden="true" />
                  ) : (
                    <Archive size={17} aria-hidden="true" />
                  )}
                  {task.status === "archived" ? "Вернуть из архива" : "Архивировать"}
                </button>
              </div>

              {!isDeleteConfirmOpen ? (
                <button
                  className="task-details-action task-details-action--danger"
                  type="button"
                  onClick={() => setIsDeleteConfirmOpen(true)}
                  disabled={isMutating}
                >
                  <Trash2 size={17} aria-hidden="true" />
                  Удалить
                </button>
              ) : (
                <div className="task-details__delete-confirm" role="alert">
                  <span>Удалить задачу без возможности восстановления?</span>
                  <div>
                    <button
                      type="button"
                      onClick={() => setIsDeleteConfirmOpen(false)}
                      disabled={deleteTaskMutation.isPending}
                    >
                      Отмена
                    </button>
                    <button
                      className="task-details__delete-button"
                      type="button"
                      onClick={() => void handleDelete()}
                      disabled={deleteTaskMutation.isPending}
                    >
                      {deleteTaskMutation.isPending ? "Удаляем…" : "Удалить"}
                    </button>
                  </div>
                  {deleteTaskMutation.isError ? (
                    <small>Не удалось удалить задачу. Попробуйте ещё раз.</small>
                  ) : null}
                </div>
              )}
            </footer>
          </div>
        ) : null}
      </aside>
    </div>
  );
}
