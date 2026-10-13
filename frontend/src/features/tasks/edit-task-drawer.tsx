import { useEffect, useState, type FormEvent } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Trash2,
  X
} from "lucide-react";

import type { TaskRecurrenceTypeCode, TaskStatusCode } from "../../entities/task/types";
import {
  useDeleteTaskMutation,
  useTaskQuery,
  useTaskRecurrenceTypesQuery,
  useTaskStatusesQuery,
  useUpdateTaskMutation
} from "./queries";
import { taskRecurrenceTypeFallback } from "./recurrence";
import { TaskFormFields } from "./task-form-fields";
import { isComboboxHandlingEscape, useTaskDrawerTransition } from "./task-drawer-transition";

type EditTaskDrawerProps = {
  taskId: string;
  onClose: () => void;
};

export function EditTaskDrawer({ taskId, onClose: onDismiss }: EditTaskDrawerProps) {
  const { onClose, isClosing } = useTaskDrawerTransition(onDismiss);
  const taskQuery = useTaskQuery(taskId);
  const statusesQuery = useTaskStatusesQuery();
  const recurrenceTypesQuery = useTaskRecurrenceTypesQuery();
  const updateTaskMutation = useUpdateTaskMutation();
  const deleteTaskMutation = useDeleteTaskMutation();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<TaskStatusCode>("todo");
  const [plannedDate, setPlannedDate] = useState("");
  const [plannedTime, setPlannedTime] = useState("");
  const [deadlineDate, setDeadlineDate] = useState("");
  const [deadlineTime, setDeadlineTime] = useState("");
  const [recurrenceType, setRecurrenceType] = useState<TaskRecurrenceTypeCode>("none");
  const [recurrenceInterval, setRecurrenceInterval] = useState(1);
  const [recurrenceStartDate, setRecurrenceStartDate] = useState("");
  const [recurrenceEndDate, setRecurrenceEndDate] = useState("");
  const [projectId, setProjectId] = useState("");
  const [projectColumnId, setProjectColumnId] = useState("");
  const [titleError, setTitleError] = useState<string | null>(null);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const isMutating = updateTaskMutation.isPending || deleteTaskMutation.isPending;
  const hasDateWarning = Boolean(plannedDate && deadlineDate && plannedDate > deadlineDate);
  const recurrenceTypes = recurrenceTypesQuery.data ?? taskRecurrenceTypeFallback;

  useEffect(() => {
    if (!taskQuery.data) {
      return;
    }

    setTitle(taskQuery.data.title);
    setDescription(taskQuery.data.description ?? "");
    setStatus(taskQuery.data.status);
    setPlannedDate(taskQuery.data.planned_date ?? "");
    setPlannedTime(taskQuery.data.planned_time ?? "");
    setDeadlineDate(taskQuery.data.deadline_date ?? "");
    setDeadlineTime(taskQuery.data.deadline_time ?? "");
    setRecurrenceType(taskQuery.data.recurrence_type_code);
    setRecurrenceInterval(taskQuery.data.recurrence_interval);
    setRecurrenceStartDate(taskQuery.data.recurrence_start_date ?? "");
    setRecurrenceEndDate(taskQuery.data.recurrence_end_date ?? "");
    setProjectId(taskQuery.data.project_id ?? "");
    setProjectColumnId(taskQuery.data.project_column_id ?? "");
  }, [taskQuery.data]);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (isComboboxHandlingEscape(event)) return;
      if (event.key === "Escape" && !event.defaultPrevented && !isMutating) {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown, true);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown, true);
    };
  }, [isMutating, onClose]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedTitle = title.trim();

    if (!trimmedTitle) {
      setTitleError("Введите название задачи.");
      return;
    }

    if (deadlineTime && !deadlineDate) {
      setScheduleError("Укажите дату дедлайна или очистите время.");
      return;
    }
    if (recurrenceType !== "none" && !recurrenceStartDate) {
      setScheduleError("Для повторения нужна дата начала.");
      return;
    }
    if (recurrenceStartDate && recurrenceEndDate && recurrenceEndDate < recurrenceStartDate) {
      setScheduleError("Дата окончания повторения не может быть раньше начала.");
      return;
    }

    setTitleError(null);
    setScheduleError(null);

    try {
      await updateTaskMutation.mutateAsync({
        taskId,
        payload: {
          title: trimmedTitle,
          description: description.trim() || null,
          status,
          planned_date: plannedDate || null,
          planned_time: plannedTime || null,
          deadline_date: deadlineDate || null,
          deadline_time: deadlineTime || null,
          recurrence_type_code: recurrenceType,
          recurrence_interval: recurrenceType === "weekdays" ? 1 : recurrenceInterval,
          recurrence_start_date: recurrenceType === "none" ? null : recurrenceStartDate || null,
          recurrence_end_date: recurrenceType === "none" ? null : recurrenceEndDate || null,
          project_id: projectId || null,
          project_column_id: projectId ? projectColumnId || null : null
        }
      });
      onClose();
    } catch {
      // Ошибка mutation отображается в форме.
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
    <div className={`task-drawer-layer${isClosing ? " task-drawer-layer--closing" : ""}`}>
      <button
        className="task-drawer-backdrop"
        type="button"
        aria-label="Закрыть задачу"
        onClick={onClose}
        disabled={isMutating}
      />
      <aside
        className="task-drawer"
        inert={isClosing}
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-task-title"
      >
        <header className="task-drawer__header">
          <h2 id="edit-task-title">Редактирование задачи</h2>
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

        {taskQuery.data ? (
          <form className="task-create-form" onSubmit={handleSubmit} noValidate>
            <div className="task-create-form__body">
              <TaskFormFields
                title={title} description={description} status={status}
                plannedDate={plannedDate} plannedTime={plannedTime} deadlineDate={deadlineDate} deadlineTime={deadlineTime}
                recurrenceType={recurrenceType} recurrenceInterval={recurrenceInterval}
                recurrenceStartDate={recurrenceStartDate} recurrenceEndDate={recurrenceEndDate}
                projectId={projectId} projectColumnId={projectColumnId}
                titleError={titleError} statuses={statusesQuery.data} statusLoading={statusesQuery.isPending} statusError={statusesQuery.isError}
                onRetryStatuses={() => void statusesQuery.refetch()} recurrenceTypes={recurrenceTypes}
                onTitleChange={(value) => { setTitle(value); setTitleError(null); }} onDescriptionChange={setDescription} onStatusChange={setStatus}
                onPlannedDateChange={setPlannedDate} onPlannedTimeChange={setPlannedTime}
                onDeadlineDateChange={(value) => { setDeadlineDate(value); setScheduleError(null); }}
                onDeadlineTimeChange={(value) => { setDeadlineTime(value); setScheduleError(null); }}
                onRecurrenceTypeChange={(value) => { setRecurrenceType(value); setStatus("todo"); setRecurrenceInterval(1); setScheduleError(null); }}
                onRecurrenceIntervalChange={setRecurrenceInterval}
                onRecurrenceStartDateChange={(value) => { setRecurrenceStartDate(value); setScheduleError(null); }}
                onRecurrenceEndDateChange={setRecurrenceEndDate}
                onProjectChange={setProjectId} onProjectColumnChange={setProjectColumnId}
              />

            {scheduleError ? (
                <div className="task-create-error" role="alert">
                  {scheduleError}
                </div>
              ) : null}

              {hasDateWarning ? (
                <div className="task-create-warning" role="status">
                  <AlertTriangle size={17} aria-hidden="true" />
                  <span>Плановая дата позже дедлайна. Задачу всё равно можно сохранить.</span>
                </div>
              ) : null}

              {updateTaskMutation.isError ? (
                <div className="task-create-error" role="alert">
                  Не удалось сохранить задачу. Проверьте данные и попробуйте ещё раз.
                </div>
              ) : null}

              <div className="task-edit-delete">
                {!isDeleteConfirmOpen ? (
                  <button
                    className="task-edit-delete__trigger"
                    type="button"
                    onClick={() => setIsDeleteConfirmOpen(true)}
                  >
                    <Trash2 size={16} aria-hidden="true" />
                    Удалить задачу
                  </button>
                ) : (
                  <div className="task-edit-delete__confirm" role="alert">
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
                        className="task-edit-delete__danger"
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
              </div>
            </div>

            <footer className="task-create-form__footer">
              <button
                className="task-create-button task-create-button--secondary"
                type="button"
                onClick={onClose}
                disabled={isMutating}
              >
                Отмена
              </button>
              <button
                className="task-create-button task-create-button--primary"
                type="submit"
                disabled={
                  isMutating ||
                  statusesQuery.isPending ||
                  statusesQuery.isError ||
                  recurrenceTypesQuery.isPending
                }
              >
                {updateTaskMutation.isPending ? "Сохраняем…" : "Сохранить"}
              </button>
            </footer>
          </form>
        ) : null}
      </aside>
    </div>
  );
}
