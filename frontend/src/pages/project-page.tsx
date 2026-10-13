import { useMemo, useState } from "react";
import { arrayMove } from "@dnd-kit/helpers";
import {
  DragDropProvider,
  DragOverlay,
  useDroppable,
  type DragEndEvent
} from "@dnd-kit/react";
import { isSortableOperation, useSortable } from "@dnd-kit/react/sortable";
import { CalendarDays, CheckCircle2, GripVertical, MoreHorizontal, Plus, Search, Settings2 } from "lucide-react";
import { Link, useLocation, useNavigate, useParams } from "react-router";

import type { ProjectColumn } from "../entities/project/types";
import type { Task, TaskStatusCode } from "../entities/task/types";
import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import { TaskDetailsDrawer } from "../features/tasks/task-details-drawer";
import { ProjectSettingsDrawer } from "../features/projects/project-settings-drawer";
import {
  useMoveProjectTaskMutation,
  useProjectBulkMutations,
  useProjectQuery,
  useProjectTasksQuery
} from "../features/projects/queries";
import { appRoutePaths } from "../app/route-paths";
import { Pagination } from "../shared/ui/pagination";
import { SelectCombobox } from "../shared/ui/select-combobox";
import { Checkbox } from "../shared/ui/checkbox";
import { DatePickerPopover } from "../shared/ui/date-picker-popover";
import { formatCompactDate } from "../shared/date-values";

type DateFilter = "all" | "today" | "tomorrow" | "week" | "overdue" | "exact";

function dateValue(offset = 0): string {
  const value = new Date();
  value.setDate(value.getDate() + offset);
  return value.toISOString().slice(0, 10);
}

function formatDate(value: string | null, time: string | null): string {
  if (!value) return "Без даты";
  const label = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`)).replace(".", "");
  return time ? `${label}, ${time.slice(0, 5)}` : label;
}

function filterTasks(tasks: Task[], query: string, dateFilter: DateFilter, selectedDate: string | undefined, stage: string, status: string): Task[] {
  const today = dateValue();
  const tomorrow = dateValue(1);
  const weekEnd = dateValue(6);
  return tasks.filter((task) => {
    if (query && !`${task.title} ${task.description ?? ""}`.toLowerCase().includes(query.toLowerCase())) return false;
    if (stage && task.project_column_id !== stage) return false;
    if (status && task.status !== status) return false;
    if (dateFilter === "today" && task.planned_date !== today && task.deadline_date !== today) return false;
    if (dateFilter === "tomorrow" && task.planned_date !== tomorrow && task.deadline_date !== tomorrow) return false;
    if (dateFilter === "week" && !((task.planned_date && task.planned_date >= today && task.planned_date <= weekEnd) || (task.deadline_date && task.deadline_date >= today && task.deadline_date <= weekEnd))) return false;
    if (dateFilter === "overdue" && !(task.status === "todo" && task.deadline_date && task.deadline_date < today)) return false;
    if (dateFilter === "exact" && selectedDate && task.planned_date !== selectedDate && task.deadline_date !== selectedDate) return false;
    return true;
  });
}

function ProjectTaskCard({ task, column, index, disabled, onOpen }: { task: Task; column: ProjectColumn; index: number; disabled: boolean; onOpen: () => void }) {
  const sortable = useSortable({ id: task.id, index, group: column.id, data: { taskId: task.id, columnId: column.id }, disabled });
  return <article ref={sortable.ref} className={`project-task-card${sortable.isDragging ? " project-task-card--dragging" : ""}`}>
    <button className="project-task-card__content" type="button" onClick={onOpen}><strong>{task.title}</strong><span><CalendarDays size={15} />{formatDate(task.planned_date, task.planned_time)}</span>{task.deadline_date ? <small>Дедлайн: {formatDate(task.deadline_date, task.deadline_time)}</small> : null}</button>
    <button ref={sortable.handleRef} className="project-task-card__handle" type="button" aria-label={`Переместить задачу ${task.title}`}><GripVertical size={17} /></button>
  </article>;
}

function ProjectColumnView({ column, tasks, disabled, onOpenTask, onCreateTask }: { column: ProjectColumn; tasks: Task[]; disabled: boolean; onOpenTask: (taskId: string) => void; onCreateTask: (columnId: string) => void }) {
  const droppable = useDroppable({ id: `column:${column.id}`, data: { columnId: column.id } });
  return <section ref={droppable.ref} className={`project-column project-column--${column.position % 5}${droppable.isDropTarget ? " project-column--over" : ""}`}>
    <header><h2>{column.title} <span>{tasks.length}</span></h2><MoreHorizontal size={18} /></header>
    <div className="project-column__tasks">{tasks.map((task, index) => <ProjectTaskCard key={task.id} task={task} column={column} index={index} disabled={disabled} onOpen={() => onOpenTask(task.id)} />)}{tasks.length === 0 ? <div className="project-column__empty">Перетащите задачу сюда</div> : null}</div>
    <button className="project-column__add" type="button" onClick={() => onCreateTask(column.id)}><Plus size={17} />Добавить задачу</button>
  </section>;
}

function ProjectBoard({ projectId, columns, tasks, onOpenTask, onCreateTask }: { projectId: string; columns: ProjectColumn[]; tasks: Task[]; onOpenTask: (taskId: string) => void; onCreateTask: (columnId: string) => void }) {
  const mutation = useMoveProjectTaskMutation(projectId);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [dndError, setDndError] = useState<string | null>(null);
  const activeTask = tasks.find((task) => task.id === activeTaskId);

  async function handleDragEnd(event: DragEndEvent) {
    if (event.canceled || !event.operation.source || !event.operation.target) {
      setActiveTaskId(null);
      return;
    }
    const taskId = String(event.operation.source.id);
    const task = tasks.find((item) => item.id === taskId);
    if (!task) {
      setActiveTaskId(null);
      return;
    }
    let targetColumnId: string | undefined;
    let targetPosition = 0;
    if (isSortableOperation(event.operation)) {
      targetColumnId = String(event.operation.target.sortable.group);
      targetPosition = event.operation.target.sortable.index;
      if (task.project_column_id === targetColumnId) {
        const orderedIds = tasks.filter((item) => item.project_column_id === targetColumnId).sort((a, b) => (a.project_position ?? 0) - (b.project_position ?? 0)).map((item) => item.id);
        const next = arrayMove(orderedIds, orderedIds.indexOf(taskId), targetPosition);
        targetPosition = next.indexOf(taskId);
      }
    } else {
      const data = event.operation.target.data as { columnId?: string } | undefined;
      targetColumnId = data?.columnId;
      targetPosition = tasks.filter((item) => item.project_column_id === targetColumnId).length;
    }
    if (!targetColumnId) {
      setActiveTaskId(null);
      return;
    }
    const targetColumn = columns.find((column) => column.id === targetColumnId);
    if (task.recurrence_type_code !== "none" && targetColumn?.is_completion_column) {
      setDndError("Повторяющуюся задачу нельзя переносить в завершающий этап.");
      setActiveTaskId(null);
      return;
    }
    if (task.project_column_id === targetColumnId && task.project_position === targetPosition) {
      setActiveTaskId(null);
      return;
    }
    setDndError(null);
    const suspension = event.suspend();
    try {
      await mutation.mutateAsync({ taskId, targetColumnId, targetPosition });
      suspension.resume();
    } catch {
      suspension.abort();
    } finally {
      setActiveTaskId(null);
    }
  }

  return <>
    {dndError || mutation.isError ? <div className="project-board__error" role="alert">{dndError ?? "Не удалось переместить задачу. Порядок восстановлен."}</div> : null}
    <DragDropProvider onDragStart={(event) => setActiveTaskId(String(event.operation.source?.id ?? ""))} onDragEnd={handleDragEnd}>
      <div className="project-board">{columns.map((column) => <ProjectColumnView key={column.id} column={column} tasks={tasks.filter((task) => task.project_column_id === column.id).sort((a, b) => (a.project_position ?? 0) - (b.project_position ?? 0))} disabled={mutation.isPending} onOpenTask={onOpenTask} onCreateTask={onCreateTask} />)}</div>
      <DragOverlay>{activeTask ? <div className="project-task-card project-task-card--overlay"><strong>{activeTask.title}</strong><span>{formatDate(activeTask.planned_date, activeTask.planned_time)}</span></div> : null}</DragOverlay>
    </DragDropProvider>
  </>;
}

function ProjectList({ projectId, columns, tasks, onOpenTask }: { projectId: string; columns: ProjectColumn[]; tasks: Task[]; onOpenTask: (taskId: string) => void }) {
  const bulk = useProjectBulkMutations(projectId);
  const [selected, setSelected] = useState<string[]>([]);
  const [targetColumn, setTargetColumn] = useState(columns[0]?.id ?? "");
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const page = tasks.slice(offset, offset + limit);
  const allPageSelected = page.length > 0 && page.every((task) => selected.includes(task.id));
  return <div className="project-list-panel">
    {selected.length ? <div className="project-list-bulk"><strong>Выбрано: {selected.length}</strong><SelectCombobox label="Переместить в этап" value={targetColumn} onChange={setTargetColumn} options={columns.map((column) => ({ value: column.id, label: column.title }))} /><button type="button" onClick={() => bulk.move.mutate({ taskIds: selected, targetColumnId: targetColumn })}>Переместить</button><button type="button" onClick={() => bulk.status.mutate({ taskIds: selected, status: "done" })}><CheckCircle2 size={16} />Отметить выполненными</button><button type="button" onClick={() => setSelected([])}>Снять выделение</button></div> : null}
    <div className="project-list-scroll"><table className="project-list-table"><thead><tr><th><Checkbox aria-label="Выбрать страницу" isSelected={allPageSelected} onChange={(checked) => setSelected(checked ? [...new Set([...selected, ...page.map((task) => task.id)])] : selected.filter((id) => !page.some((task) => task.id === id)))} /></th><th>Задача</th><th>Этап</th><th>Когда делать</th><th>Дедлайн</th><th>Обновлено</th></tr></thead><tbody>{page.map((task) => <tr key={task.id} className={task.deadline_date && task.deadline_date < dateValue() && task.status === "todo" ? "overdue" : ""}><td><Checkbox aria-label={`Выбрать ${task.title}`} isSelected={selected.includes(task.id)} onChange={(checked) => setSelected(checked ? [...selected, task.id] : selected.filter((id) => id !== task.id))} /></td><td><button type="button" onClick={() => onOpenTask(task.id)}>{task.title}</button></td><td><span>{columns.find((column) => column.id === task.project_column_id)?.title ?? "—"}</span></td><td>{formatDate(task.planned_date, task.planned_time)}</td><td>{formatDate(task.deadline_date, task.deadline_time)}</td><td>{new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(task.updated_at))}</td></tr>)}</tbody></table></div>
    <Pagination className="project-list-pagination" total={tasks.length} label="Всего задач" limit={limit} offset={offset} onLimitChange={(value) => { setLimit(value); setOffset(0); }} onOffsetChange={setOffset} />
  </div>;
}

export function ProjectPage() {
  const { projectId = "" } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const isList = location.pathname.endsWith("/list");
  const projectQuery = useProjectQuery(projectId);
  const tasksQuery = useProjectTasksQuery(projectId);
  const [query, setQuery] = useState("");
  const [dateFilter, setDateFilter] = useState<DateFilter>("all");
  const [selectedDate, setSelectedDate] = useState<string>();
  const [stage, setStage] = useState("");
  const [status, setStatus] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [createColumnId, setCreateColumnId] = useState<string | null>(null);
  const [taskDetailsId, setTaskDetailsId] = useState<string | null>(null);
  const project = projectQuery.data;
  const columns = useMemo(() => [...(project?.columns ?? [])].sort((a, b) => a.position - b.position), [project]);
  const tasks = useMemo(
    () => filterTasks(tasksQuery.data?.items ?? [], query, dateFilter, selectedDate, stage, status),
    [tasksQuery.data, query, dateFilter, selectedDate, stage, status]
  );
  const dateOptions: { value: DateFilter; label: string }[] = [
    { value: "all", label: "Все даты" },
    ...(selectedDate ? [{ value: "exact" as const, label: `Дата: ${formatCompactDate(selectedDate)}` }] : []),
    { value: "today", label: "Сегодня" },
    { value: "tomorrow", label: "Завтра" },
    { value: "week", label: "Эта неделя" },
    { value: "overdue", label: "Просроченные" }
  ];

  if (projectQuery.isPending || tasksQuery.isPending) return <div className="projects-state">Загружаем проект…</div>;
  if (projectQuery.isError || !project) return <div className="projects-state projects-state--error"><strong>Не удалось загрузить проект</strong><Link to={appRoutePaths.projects.all}>К списку проектов</Link></div>;
  return <div className="project-page">
    <header className="project-page__header"><div><p><Link to={appRoutePaths.projects.all}>Проекты</Link> / {project.title}</p><h1>{project.title}</h1><span>{project.description || "Без описания"}</span></div><div><button type="button" className="project-icon-button" aria-label="Настройки проекта" onClick={() => setSettingsOpen(true)}><Settings2 size={19} /></button><button type="button" className="projects-primary-button" onClick={() => setCreateColumnId(columns[0]?.id ?? "")}><Plus size={18} />Новая задача</button></div></header>
    <div className="project-toolbar">
      <div className="project-view-switch"><button className={!isList ? "active" : ""} type="button" onClick={() => navigate(appRoutePaths.projects.board(project.id))}>Доска</button><button className={isList ? "active" : ""} type="button" onClick={() => navigate(appRoutePaths.projects.list(project.id))}>Список</button></div>
      <label className="projects-search"><Search size={16} /><input placeholder="Поиск по проекту" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
      <div className="project-toolbar__filters">
        <div className="project-date-filter">
          <SelectCombobox
            label="Даты"
            value={dateFilter}
            onChange={(value) => {
              const nextFilter = value as DateFilter;
              setDateFilter(nextFilter);
              if (nextFilter !== "exact") setSelectedDate(undefined);
            }}
            options={dateOptions}
          />
          <DatePickerPopover
            className="project-date-picker"
            mode="single"
            label="Выбрать конкретную дату"
            buttonLabel="Календарь"
            value={selectedDate}
            onChange={(value) => {
              setSelectedDate(value);
              setDateFilter("exact");
            }}
          />
        </div>
        <SelectCombobox label="Этап" value={stage} onChange={setStage} options={[{ value: "", label: "Все этапы" }, ...columns.map((column) => ({ value: column.id, label: column.title }))]} />
        <SelectCombobox label="Статус" value={status} onChange={setStatus} options={[{ value: "", label: "Все статусы" }, { value: "todo", label: "Активные" }, { value: "done", label: "Выполненные" }]} />
      </div>
    </div>
    {tasksQuery.isError ? <div className="project-board__error">Не удалось загрузить задачи проекта.</div> : isList ? <ProjectList projectId={project.id} columns={columns} tasks={tasks} onOpenTask={setTaskDetailsId} /> : <ProjectBoard projectId={project.id} columns={columns} tasks={tasks} onOpenTask={setTaskDetailsId} onCreateTask={setCreateColumnId} />}
    {settingsOpen ? <ProjectSettingsDrawer project={project} onClose={() => setSettingsOpen(false)} /> : null}
    {createColumnId !== null ? <CreateTaskDrawer initialProjectId={project.id} initialProjectColumnId={createColumnId} onClose={() => setCreateColumnId(null)} /> : null}
    {taskDetailsId ? <TaskDetailsDrawer taskId={taskDetailsId} onClose={() => setTaskDetailsId(null)} /> : null}
  </div>;
}
