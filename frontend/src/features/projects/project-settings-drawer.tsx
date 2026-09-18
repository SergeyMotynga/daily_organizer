import { useEffect, useState, type FormEvent } from "react";
import { ArrowDown, ArrowUp, CheckCircle2, GripVertical, Plus, Trash2, X } from "lucide-react";
import { useNavigate } from "react-router";

import type { ProjectDetail } from "../../entities/project/types";
import { appRoutePaths } from "../../app/route-paths";
import { useTaskDrawerTransition } from "../tasks/task-drawer-transition";
import {
  useDeleteProjectMutation,
  useProjectColumnMutations,
  useUpdateProjectMutation
} from "./queries";

export function ProjectSettingsDrawer({ project, onClose: onDismiss }: { project: ProjectDetail; onClose: () => void }) {
  const navigate = useNavigate();
  const { onClose, isClosing } = useTaskDrawerTransition(onDismiss);
  const updateProject = useUpdateProjectMutation(project.id);
  const deleteProject = useDeleteProjectMutation(project.id);
  const columns = useProjectColumnMutations(project.id);
  const [title, setTitle] = useState(project.title);
  const [description, setDescription] = useState(project.description ?? "");
  const [newColumn, setNewColumn] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const pending = updateProject.isPending || deleteProject.isPending || columns.create.isPending || columns.update.isPending || columns.remove.isPending || columns.reorder.isPending;

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previousOverflow; };
  }, []);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) { setError("Введите название проекта."); return; }
    try { await updateProject.mutateAsync({ title: title.trim(), description: description.trim() || null }); onClose(); }
    catch { setError("Не удалось сохранить настройки."); }
  }

  async function addColumn() {
    if (!newColumn.trim()) return;
    try { await columns.create.mutateAsync(newColumn.trim()); setNewColumn(""); }
    catch { setError("Не удалось добавить колонку."); }
  }

  async function renameColumn(columnId: string, currentTitle: string) {
    const next = window.prompt("Название колонки", currentTitle)?.trim();
    if (!next || next === currentTitle) return;
    try { await columns.update.mutateAsync({ columnId, payload: { title: next } }); }
    catch { setError("Не удалось переименовать колонку."); }
  }

  async function changeOrder(index: number, direction: -1 | 1) {
    const ordered = [...project.columns].sort((a, b) => a.position - b.position);
    const target = index + direction;
    if (!ordered[target]) return;
    [ordered[index], ordered[target]] = [ordered[target], ordered[index]];
    try { await columns.reorder.mutateAsync(ordered.map((column) => column.id)); }
    catch { setError("Не удалось изменить порядок колонок."); }
  }

  async function removeColumn(columnId: string) {
    try { await columns.remove.mutateAsync(columnId); }
    catch { setError("Колонку можно удалить только когда она пуста и не завершает задачи."); }
  }

  async function removeProject() {
    try { await deleteProject.mutateAsync(); navigate(appRoutePaths.projects.all); }
    catch { setError("Не удалось удалить проект."); }
  }

  return <div className={`task-drawer-layer${isClosing ? " task-drawer-layer--closing" : ""}`}>
    <button className="task-drawer-backdrop" type="button" aria-label="Закрыть настройки" onClick={onClose} disabled={pending} />
    <aside className="task-drawer project-settings" role="dialog" aria-modal="true" aria-labelledby="project-settings-title" inert={isClosing}>
      <header className="task-drawer__header"><div><h2 id="project-settings-title">Настройки проекта</h2><p>{project.title}</p></div><button className="task-drawer__close" type="button" onClick={onClose} aria-label="Закрыть"><X size={20} /></button></header>
      <form className="task-create-form" onSubmit={save}>
        <div className="task-create-form__body">
          <section className="project-settings__section"><h3>Основное</h3><label className="task-create-field"><span>Название</span><input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={255} /></label><label className="task-create-field"><span>Описание</span><textarea rows={3} value={description} onChange={(event) => setDescription(event.target.value)} /></label></section>
          <section className="project-settings__section"><h3>Колонки доски</h3><p>Порядок этапов применяется к доске и списку.</p><div className="project-settings__columns">{[...project.columns].sort((a, b) => a.position - b.position).map((column, index) => <div key={column.id} className="project-settings__column"><GripVertical size={16} /><button type="button" className="project-settings__column-name" onClick={() => void renameColumn(column.id, column.title)}>{column.title}</button>{column.is_completion_column ? <span className="project-settings__completion"><CheckCircle2 size={13} />Завершает</span> : <button type="button" className="project-settings__make-completion" onClick={() => columns.update.mutate({ columnId: column.id, payload: { is_completion_column: true } })}>Сделать завершающей</button>}<button type="button" aria-label="Выше" disabled={index === 0 || pending} onClick={() => void changeOrder(index, -1)}><ArrowUp size={14} /></button><button type="button" aria-label="Ниже" disabled={index === project.columns.length - 1 || pending} onClick={() => void changeOrder(index, 1)}><ArrowDown size={14} /></button><button type="button" aria-label="Удалить колонку" disabled={column.is_completion_column || pending} onClick={() => void removeColumn(column.id)}><Trash2 size={14} /></button></div>)}</div><div className="project-settings__add"><input value={newColumn} maxLength={255} onChange={(event) => setNewColumn(event.target.value)} placeholder="Название новой колонки" /><button type="button" onClick={() => void addColumn()} disabled={!newColumn.trim() || pending}><Plus size={16} />Добавить</button></div></section>
          <section className="project-settings__section project-settings__danger"><h3>Опасная зона</h3><button type="button" onClick={() => updateProject.mutate({ archived: !project.archived_at })}>{project.archived_at ? "Восстановить проект" : "Архивировать проект"}</button>{deleteConfirm ? <div className="project-settings__confirm"><p>Проект и колонки будут удалены. Задачи останутся без проекта.</p><button type="button" onClick={() => setDeleteConfirm(false)}>Отмена</button><button type="button" onClick={() => void removeProject()}>Удалить</button></div> : <button className="danger" type="button" onClick={() => setDeleteConfirm(true)}><Trash2 size={16} />Удалить проект</button>}</section>
          {error ? <div className="task-create-error" role="alert">{error}</div> : null}
        </div>
        <footer className="task-create-form__footer"><button className="task-create-button task-create-button--secondary" type="button" onClick={onClose}>Отмена</button><button className="task-create-button task-create-button--primary" type="submit" disabled={pending}>{updateProject.isPending ? "Сохраняем…" : "Сохранить изменения"}</button></footer>
      </form>
    </aside>
  </div>;
}
