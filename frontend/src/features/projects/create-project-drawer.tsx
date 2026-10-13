import { useEffect, useState, type FormEvent } from "react";
import { X } from "lucide-react";

import { useCreateProjectMutation } from "./queries";
import { isComboboxHandlingEscape, useTaskDrawerTransition } from "../tasks/task-drawer-transition";

const defaultColumns = ["Бэклог", "К выполнению", "В работе", "На проверке", "Готово"];

export function CreateProjectDrawer({ onClose: onDismiss }: { onClose: () => void }) {
  const { onClose, isClosing } = useTaskDrawerTransition(onDismiss);
  const mutation = useCreateProjectMutation();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function handleKeyDown(event: KeyboardEvent) {
      if (isComboboxHandlingEscape(event)) return;
      if (event.key === "Escape" && !mutation.isPending) onClose();
    }
    document.addEventListener("keydown", handleKeyDown, true);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown, true);
    };
  }, [mutation.isPending, onClose]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) {
      setError("Введите название проекта.");
      return;
    }
    setError(null);
    try {
      await mutation.mutateAsync({ title: title.trim(), description: description.trim() || null });
      onClose();
    } catch {
      setError("Не удалось создать проект. Попробуйте ещё раз.");
    }
  }

  return (
    <div className={`task-drawer-layer${isClosing ? " task-drawer-layer--closing" : ""}`}>
      <button className="task-drawer-backdrop" type="button" aria-label="Закрыть" onClick={onClose} />
      <aside className="task-drawer" role="dialog" aria-modal="true" aria-labelledby="new-project-title" inert={isClosing}>
        <header className="task-drawer__header">
          <div><h2 id="new-project-title">Новый проект</h2><p>Создайте пространство для связанных задач</p></div>
          <button className="task-drawer__close" type="button" onClick={onClose} aria-label="Закрыть"><X size={20} /></button>
        </header>
        <form className="task-create-form" onSubmit={submit}>
          <div className="task-create-form__body">
            <label className="task-create-field"><span>Название <b>*</b></span><input autoFocus maxLength={255} value={title} onChange={(event) => { setTitle(event.target.value); setError(null); }} placeholder="Название проекта" /></label>
            <label className="task-create-field"><span>Описание</span><textarea rows={5} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Коротко о цели проекта" /></label>
            <section className="project-create-preview">
              <strong>Колонки доски</strong>
              <p>После создания будут добавлены стандартные этапы</p>
              <div>{defaultColumns.map((column) => <span key={column}>{column}</span>)}</div>
              <small>Этапы можно изменить в настройках проекта.</small>
            </section>
            {error ? <div className="task-create-error" role="alert">{error}</div> : null}
          </div>
          <footer className="task-create-form__footer">
            <button className="task-create-button task-create-button--secondary" type="button" onClick={onClose}>Отмена</button>
            <button className="task-create-button task-create-button--primary" type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Создаём…" : "Создать проект"}</button>
          </footer>
        </form>
      </aside>
    </div>
  );
}
