import { useEffect, useState, type FormEvent } from "react";
import { AlertTriangle, CalendarDays, Clock3, Info, X } from "lucide-react";

import type { TaskStatusCode } from "../../entities/task/types";
import { useCreateTaskMutation, useTaskStatusesQuery } from "./queries";

type CreateTaskDrawerProps = {
  onClose: () => void;
};

function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function getRelativeDate(dayOffset: number): string {
  const date = new Date();
  date.setDate(date.getDate() + dayOffset);
  return formatLocalDate(date);
}

export function CreateTaskDrawer({ onClose }: CreateTaskDrawerProps) {
  const statusesQuery = useTaskStatusesQuery();
  const createTaskMutation = useCreateTaskMutation();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<TaskStatusCode>("todo");
  const [plannedDate, setPlannedDate] = useState("");
  const [plannedTime, setPlannedTime] = useState("");
  const [deadlineDate, setDeadlineDate] = useState("");
  const [titleError, setTitleError] = useState<string | null>(null);
  const todayDate = getRelativeDate(0);
  const tomorrowDate = getRelativeDate(1);
  const hasDateWarning = Boolean(plannedDate && deadlineDate && plannedDate > deadlineDate);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !createTaskMutation.isPending) {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [createTaskMutation.isPending, onClose]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedTitle = title.trim();

    if (!trimmedTitle) {
      setTitleError("Введите название задачи.");
      return;
    }

    setTitleError(null);

    try {
      await createTaskMutation.mutateAsync({
        title: trimmedTitle,
        description: description.trim() || null,
        status,
        planned_date: plannedDate || null,
        planned_time: plannedTime || null,
        deadline_date: deadlineDate || null
      });
      onClose();
    } catch {
      // Ошибка mutation отображается в форме.
    }
  }

  return (
    <div className="task-drawer-layer">
      <button
        className="task-drawer-backdrop"
        type="button"
        aria-label="Закрыть форму создания задачи"
        onClick={onClose}
        disabled={createTaskMutation.isPending}
      />
      <aside
        className="task-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-task-title"
      >
        <header className="task-drawer__header">
          <h2 id="create-task-title">Новая задача</h2>
          <button
            className="task-drawer__close"
            type="button"
            aria-label="Закрыть"
            onClick={onClose}
            disabled={createTaskMutation.isPending}
          >
            <X size={20} />
          </button>
        </header>

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
                aria-describedby={titleError ? "create-task-title-error" : undefined}
                placeholder="Введите название задачи"
                maxLength={255}
              />
              {titleError ? (
                <small id="create-task-title-error" className="task-create-field__error">
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
                          name="task-status"
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

            <fieldset className="task-create-fieldset">
              <legend>Когда делать (план)</legend>
              <div className="task-date-shortcuts">
                <button
                  className={plannedDate === todayDate ? "task-date-shortcut--active" : undefined}
                  type="button"
                  aria-pressed={plannedDate === todayDate}
                  onClick={() => setPlannedDate(todayDate)}
                >
                  Сегодня
                </button>
                <button
                  className={plannedDate === tomorrowDate ? "task-date-shortcut--active" : undefined}
                  type="button"
                  aria-pressed={plannedDate === tomorrowDate}
                  onClick={() => setPlannedDate(tomorrowDate)}
                >
                  Завтра
                </button>
                <button
                  className={plannedDate === "" ? "task-date-shortcut--active" : undefined}
                  type="button"
                  aria-pressed={plannedDate === ""}
                  onClick={() => setPlannedDate("")}
                >
                  Без даты
                </button>
              </div>
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
            </fieldset>

            <label className="task-create-field">
              <span>Дедлайн</span>
              <span className="task-date-input">
                <CalendarDays size={17} aria-hidden="true" />
                <input
                  type="date"
                  value={deadlineDate}
                  onChange={(event) => setDeadlineDate(event.target.value)}
                  aria-label="Дедлайн"
                />
              </span>
            </label>

            {hasDateWarning ? (
              <div className="task-create-warning" role="status">
                <AlertTriangle size={17} aria-hidden="true" />
                <span>Плановая дата позже дедлайна. Задачу всё равно можно создать.</span>
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

            {createTaskMutation.isError ? (
              <div className="task-create-error" role="alert">
                Не удалось создать задачу. Проверьте данные и попробуйте ещё раз.
              </div>
            ) : null}
          </div>

          <footer className="task-create-form__footer">
            <button
              className="task-create-button task-create-button--secondary"
              type="button"
              onClick={onClose}
              disabled={createTaskMutation.isPending}
            >
              Отмена
            </button>
            <button
              className="task-create-button task-create-button--primary"
              type="submit"
              disabled={
                createTaskMutation.isPending || statusesQuery.isPending || statusesQuery.isError
              }
            >
              {createTaskMutation.isPending ? "Создаём…" : "Создать"}
            </button>
          </footer>
        </form>
      </aside>
    </div>
  );
}
