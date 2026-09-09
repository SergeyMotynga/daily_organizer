import { useEffect, useState, type FormEvent } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CalendarDays,
  Clock3,
  Info,
  Repeat2,
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
import { getRecurrenceLabel, taskRecurrenceTypeFallback } from "./recurrence";

type EditTaskDrawerProps = {
  taskId: string;
  onClose: () => void;
};

export function EditTaskDrawer({ taskId, onClose }: EditTaskDrawerProps) {
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
  }, [taskQuery.data]);

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
          recurrence_end_date: recurrenceType === "none" ? null : recurrenceEndDate || null
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
    <div className="task-drawer-layer">
      <button
        className="task-drawer-backdrop"
        type="button"
        aria-label="Закрыть задачу"
        onClick={onClose}
        disabled={isMutating}
      />
      <aside
        className="task-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-task-title"
      >
        <header className="task-drawer__header">
          <h2 id="edit-task-title">Задача</h2>
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
              <label className="task-create-field">
                <span>
                  Название <b aria-hidden="true">*</b>
                </span>
                <input
                  autoFocus
                  value={title}
                  onChange={(event) => {
                    setTitle(event.target.value);
                    if (titleError) {
                      setTitleError(null);
                    }
                  }}
                  aria-invalid={Boolean(titleError)}
                  aria-describedby={titleError ? "edit-task-title-error" : undefined}
                  placeholder="Введите название задачи"
                  maxLength={255}
                />
                {titleError ? (
                  <small id="edit-task-title-error" className="task-create-field__error">
                    {titleError}
                  </small>
                ) : null}
              </label>

              <label className="task-create-field">
                <span>Описание</span>
                <textarea
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Краткое описание задачи (необязательно)"
                  rows={4}
                />
              </label>

              {recurrenceType === "none" ? (
                <fieldset className="task-create-fieldset">
                  <legend>Статус</legend>
                {statusesQuery.isPending ? (
                  <p className="task-create-fieldset__state">Загружаем статусы…</p>
                ) : null}
                {statusesQuery.isError ? (
                  <div className="task-create-fieldset__error" role="alert">
                    <span>Не удалось загрузить статусы.</span>
                    <button type="button" onClick={() => void statusesQuery.refetch()}>
                      Повторить
                    </button>
                  </div>
                ) : null}
                {statusesQuery.data ? (
                  <div className="task-status-options">
                    {[...statusesQuery.data]
                      .sort((left, right) => left.sort_order - right.sort_order)
                      .map((option) => (
                        <label
                          className={
                            status === option.code
                              ? "task-status-option task-status-option--active"
                              : "task-status-option"
                          }
                          key={option.code}
                        >
                          <input
                            type="radio"
                            name="edit-task-status"
                            value={option.code}
                            checked={status === option.code}
                            onChange={() => setStatus(option.code)}
                          />
                          <span>{option.title}</span>
                        </label>
                      ))}
                  </div>
                ) : null}
                </fieldset>
              ) : null}

              <div className="task-create-field">
                <span>Когда делать (план)</span>
                <div className="task-plan-inputs">
                  <label className="task-date-input">
                    <CalendarDays size={17} aria-hidden="true" />
                    <input
                      type="date"
                      value={plannedDate}
                      onChange={(event) => setPlannedDate(event.target.value)}
                      aria-label="Плановая дата"
                    />
                  </label>
                  <label className="task-date-input">
                    <Clock3 size={17} aria-hidden="true" />
                    <input
                      type="time"
                      value={plannedTime}
                      onChange={(event) => setPlannedTime(event.target.value)}
                      aria-label="Плановое время"
                    />
                  </label>
                </div>
              </div>

              <div className="task-create-field">
                <span>Дедлайн</span>
                <div className="task-plan-inputs">
                  <label className="task-date-input">
                    <CalendarDays size={17} aria-hidden="true" />
                    <input
                      type="date"
                      value={deadlineDate}
                      onChange={(event) => {
                        setDeadlineDate(event.target.value);
                        setScheduleError(null);
                      }}
                      aria-label="Дата дедлайна"
                    />
                  </label>
                  <label className="task-date-input">
                    <Clock3 size={17} aria-hidden="true" />
                    <input
                      type="time"
                      value={deadlineTime}
                      onChange={(event) => {
                        setDeadlineTime(event.target.value);
                        setScheduleError(null);
                      }}
                      aria-label="Время дедлайна"
                    />
                  </label>
                </div>
              </div>

              <fieldset className="task-create-fieldset">
                <legend>Повторение</legend>
                <label className="task-recurrence-select">
                  <Repeat2 size={17} aria-hidden="true" />
                  <select
                    value={recurrenceType}
                    onChange={(event) => {
                      const nextType = event.target.value as TaskRecurrenceTypeCode;
                      setRecurrenceType(nextType);
                      setStatus("todo");
                      setRecurrenceInterval(1);
                      setScheduleError(null);
                    }}
                  >
                    {[...recurrenceTypes]
                      .sort((left, right) => left.sort_order - right.sort_order)
                      .map((option) => (
                        <option value={option.code} key={option.code}>
                          {getRecurrenceLabel(option.code, 1)}
                        </option>
                      ))}
                  </select>
                </label>
                {recurrenceTypesQuery.isError ? (
                  <small className="task-create-field__note">
                    Используется встроенный список типов повторения.
                  </small>
                ) : null}
                {recurrenceType !== "none" ? (
                  <div className="task-recurrence-inputs">
                    {recurrenceType === "daily" || recurrenceType === "weekly" ? (
                      <label className="task-create-field">
                        <span>
                          {recurrenceType === "daily"
                            ? "Интервал в днях"
                            : "Интервал в неделях"}
                        </span>
                        <input
                          type="number"
                          min={1}
                          value={recurrenceInterval}
                          onChange={(event) =>
                            setRecurrenceInterval(Math.max(1, Number(event.target.value) || 1))
                          }
                        />
                      </label>
                    ) : null}
                    <div className="task-plan-inputs">
                      <label className="task-create-field">
                        <span>Начало</span>
                        <input
                          type="date"
                          value={recurrenceStartDate}
                          onChange={(event) => {
                            setRecurrenceStartDate(event.target.value);
                            setScheduleError(null);
                          }}
                        />
                      </label>
                      <label className="task-create-field">
                        <span>Окончание</span>
                        <input
                          type="date"
                          min={recurrenceStartDate || undefined}
                          value={recurrenceEndDate}
                          onChange={(event) => setRecurrenceEndDate(event.target.value)}
                        />
                      </label>
                    </div>
                  </div>
                ) : null}
              </fieldset>

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
              ) : (
                <div className="task-create-hint">
                  <Info size={17} aria-hidden="true" />
                  <span>
                    Когда делать — это план.
                    <br />
                    Дедлайн — когда задача должна быть готова.
                  </span>
                </div>
              )}

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
