import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { arrayMove } from "@dnd-kit/helpers";
import { DragDropProvider, type DragEndEvent } from "@dnd-kit/react";
import { isSortable, useSortable } from "@dnd-kit/react/sortable";
import { ArrowDown, ArrowUp, Check, CheckCircle2, GripVertical, Plus, Trash2, X } from "lucide-react";
import { useNavigate } from "react-router";

import type { ProjectColumn, ProjectDetail } from "../../entities/project/types";
import { appRoutePaths } from "../../app/route-paths";
import { useTaskDrawerTransition } from "../tasks/task-drawer-transition";
import {
  useDeleteProjectMutation,
  useProjectColumnMutations,
  useUpdateProjectMutation
} from "./queries";

function SortableProjectColumn({ column, index, disabled, children }: { column: ProjectColumn; index: number; disabled: boolean; children: ReactNode }) {
  const sortable = useSortable({ id: column.id, index, group: column.project_id, disabled });
  return <div ref={sortable.ref} className={`project-settings__column${sortable.isDragging || sortable.isDropping ? " project-settings__column--dragging" : ""}`}>
    <button ref={sortable.handleRef} className="project-settings__column-handle" type="button" aria-label={`Переместить колонку ${column.title}`} title="Перетащите, чтобы изменить порядок" disabled={disabled}><GripVertical size={16} /></button>
    {children}
  </div>;
}

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
  const [editingColumn, setEditingColumn] = useState<{ id: string; title: string } | null>(null);
  const [renameError, setRenameError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [orderRevision, setOrderRevision] = useState(0);
  const columnNameRefs = useRef(new Map<string, HTMLButtonElement>());
  const lastEditingColumnId = useRef<string | null>(null);
  const orderedColumns = [...project.columns].sort((a, b) => a.position - b.position);
  const pending = updateProject.isPending || deleteProject.isPending || columns.create.isPending || columns.update.isPending || columns.remove.isPending || columns.reorder.isPending;
  const controlsDisabled = pending || isDragging || editingColumn !== null;

  useEffect(() => {
    if (editingColumn) lastEditingColumnId.current = editingColumn.id;
    else if (lastEditingColumnId.current) {
      columnNameRefs.current.get(lastEditingColumnId.current)?.focus();
      lastEditingColumnId.current = null;
    }
  }, [editingColumn]);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = previousOverflow; };
  }, []);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (controlsDisabled) return;
    if (!title.trim()) { setError("Введите название проекта."); return; }
    try { await updateProject.mutateAsync({ title: title.trim(), description: description.trim() || null }); onClose(); }
    catch { setError("Не удалось сохранить настройки."); }
  }

  async function addColumn() {
    if (!newColumn.trim()) return;
    try { await columns.create.mutateAsync(newColumn.trim()); setNewColumn(""); }
    catch { setError("Не удалось добавить колонку."); }
  }

  async function renameColumn() {
    if (!editingColumn || pending) return;
    const next = editingColumn.title.trim();
    if (!next) { setRenameError("Введите название колонки."); return; }
    if (next === project.columns.find((column) => column.id === editingColumn.id)?.title) {
      setEditingColumn(null);
      return;
    }
    setRenameError(null);
    try {
      await columns.update.mutateAsync({ columnId: editingColumn.id, payload: { title: next } });
      setEditingColumn(null);
    } catch { setRenameError("Не удалось сохранить название. Попробуйте ещё раз."); }
  }

  async function reorderColumns(ordered: ProjectColumn[]): Promise<boolean> {
    setError(null);
    try { await columns.reorder.mutateAsync(ordered.map((column) => column.id)); return true; }
    catch { setError("Не удалось изменить порядок колонок. Попробуйте ещё раз."); return false; }
  }

  async function handleColumnDragEnd(event: DragEndEvent) {
    setIsDragging(false);
    const { source, target } = event.operation;
    if (event.canceled || !source || !isSortable(source)) return;
    const initialIndex = orderedColumns.findIndex((column) => column.id === source.id);
    if (!target || initialIndex < 0) {
      event.suspend().abort();
      setOrderRevision((revision) => revision + 1);
      return;
    }
    if (initialIndex === source.index) return;
    const suspension = event.suspend();
    if (await reorderColumns(arrayMove(orderedColumns, initialIndex, source.index))) {
      suspension.resume();
    } else {
      suspension.abort();
      // После ошибки пересоздаём список из серверного порядка, убирая перестановки DOM от dnd-kit.
      setOrderRevision((revision) => revision + 1);
    }
  }

  async function changeOrder(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (!orderedColumns[target] || controlsDisabled) return;
    await reorderColumns(arrayMove(orderedColumns, index, target));
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
    <button className="task-drawer-backdrop" type="button" aria-label="Закрыть настройки" onClick={onClose} disabled={pending || isDragging} />
    <aside className="task-drawer project-settings" role="dialog" aria-modal="true" aria-labelledby="project-settings-title" inert={isClosing}>
      <header className="task-drawer__header"><div><h2 id="project-settings-title">Настройки проекта</h2><p>{project.title}</p></div><button className="task-drawer__close" type="button" onClick={onClose} aria-label="Закрыть" disabled={pending || isDragging}><X size={20} /></button></header>
      <form className="task-create-form" onSubmit={save}>
        <div className="task-create-form__body">
          <section className="project-settings__section"><h3>Основное</h3><label className="task-create-field"><span>Название</span><input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={255} /></label><label className="task-create-field"><span>Описание</span><textarea rows={3} value={description} onChange={(event) => setDescription(event.target.value)} /></label></section>
          <section className="project-settings__section">
            <h3>Колонки доски</h3>
            <p>Перетаскивайте колонки за точки или используйте стрелки. Нажмите название, чтобы переименовать.</p>
            <DragDropProvider onDragStart={() => { setIsDragging(true); setError(null); }} onDragEnd={handleColumnDragEnd}>
              <div key={orderRevision} className="project-settings__columns">{orderedColumns.map((column, index) => <SortableProjectColumn key={column.id} column={column} index={index} disabled={pending || editingColumn !== null}>
                {editingColumn?.id === column.id ? <div className="project-settings__column-edit">
                  <input autoFocus aria-label="Название колонки" aria-invalid={Boolean(renameError)} aria-describedby={renameError ? `column-title-error-${column.id}` : undefined} value={editingColumn.title} maxLength={255} disabled={pending} onChange={(event) => { setEditingColumn({ id: column.id, title: event.target.value }); setRenameError(null); }} onKeyDown={(event) => {
                    if (event.key === "Enter") { event.preventDefault(); void renameColumn(); }
                    if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); setEditingColumn(null); setRenameError(null); }
                  }} />
                  <button type="button" aria-label="Сохранить название колонки" title="Сохранить название" disabled={pending} onClick={() => void renameColumn()}><Check size={16} /></button>
                  <button type="button" aria-label="Отменить переименование" title="Отменить" disabled={pending} onClick={() => { setEditingColumn(null); setRenameError(null); }}><X size={16} /></button>
                  {renameError ? <span id={`column-title-error-${column.id}`} role="alert">{renameError}</span> : null}
                </div> : <>
                  <button ref={(node) => { if (node) columnNameRefs.current.set(column.id, node); else columnNameRefs.current.delete(column.id); }} type="button" className="project-settings__column-name" title={column.title} disabled={controlsDisabled} onClick={() => { setEditingColumn({ id: column.id, title: column.title }); setRenameError(null); }}>{column.title}</button>
                  {column.is_completion_column ? <span className="project-settings__completion"><CheckCircle2 size={13} />Завершает</span> : <button type="button" className="project-settings__make-completion" disabled={controlsDisabled} onClick={() => columns.update.mutate({ columnId: column.id, payload: { is_completion_column: true } })}>Сделать завершающей</button>}
                  <button type="button" aria-label={`Переместить ${column.title} выше`} disabled={index === 0 || controlsDisabled} onClick={() => void changeOrder(index, -1)}><ArrowUp size={14} /></button>
                  <button type="button" aria-label={`Переместить ${column.title} ниже`} disabled={index === orderedColumns.length - 1 || controlsDisabled} onClick={() => void changeOrder(index, 1)}><ArrowDown size={14} /></button>
                  <button type="button" aria-label={`Удалить колонку ${column.title}`} disabled={column.is_completion_column || controlsDisabled} onClick={() => void removeColumn(column.id)}><Trash2 size={14} /></button>
                </>}
              </SortableProjectColumn>)}</div>
            </DragDropProvider>
            <div className="project-settings__add"><input value={newColumn} maxLength={255} onChange={(event) => setNewColumn(event.target.value)} placeholder="Название новой колонки" disabled={controlsDisabled} /><button type="button" onClick={() => void addColumn()} disabled={!newColumn.trim() || controlsDisabled}><Plus size={16} />Добавить</button></div>
          </section>
          <section className="project-settings__section project-settings__danger"><h3>Опасная зона</h3><button type="button" disabled={controlsDisabled} onClick={() => updateProject.mutate({ archived: !project.archived_at })}>{project.archived_at ? "Восстановить проект" : "Архивировать проект"}</button>{deleteConfirm ? <div className="project-settings__confirm"><p>Проект и колонки будут удалены. Задачи останутся без проекта.</p><button type="button" disabled={controlsDisabled} onClick={() => setDeleteConfirm(false)}>Отмена</button><button type="button" disabled={controlsDisabled} onClick={() => void removeProject()}>Удалить</button></div> : <button className="danger" type="button" disabled={controlsDisabled} onClick={() => setDeleteConfirm(true)}><Trash2 size={16} />Удалить проект</button>}</section>
          {error ? <div className="task-create-error" role="alert">{error}</div> : null}
        </div>
        <footer className="task-create-form__footer"><button className="task-create-button task-create-button--secondary" type="button" onClick={onClose} disabled={pending || isDragging}>Отмена</button><button className="task-create-button task-create-button--primary" type="submit" disabled={controlsDisabled}>{updateProject.isPending ? "Сохраняем…" : "Сохранить изменения"}</button></footer>
      </form>
    </aside>
  </div>;
}
