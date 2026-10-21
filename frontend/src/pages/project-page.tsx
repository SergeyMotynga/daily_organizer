import { Fragment, useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { arrayMove } from "@dnd-kit/helpers";
import {
  DragDropProvider,
  DragOverlay,
  useDragOperation,
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
import { TaskInlineDetails } from "../features/tasks/task-list-item";
import { useUpdateTaskMutation } from "../features/tasks/queries";
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
import { formatCompactDate, getTodayValue } from "../shared/date-values";

import { filterProjectTasks, type DateFilter } from "../features/projects/task-filters";

function formatDate(value: string | null, time: string | null): string {
  if (!value) return "Без даты";
  const label = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`)).replace(".", "");
  return time ? `${label}, ${time.slice(0, 5)}` : label;
}

function ProjectTaskCard({ task, column, index, disabled, onOpen }: { task: Task; column: ProjectColumn; index: number; disabled: boolean; onOpen: () => void }) {
  const update = useUpdateTaskMutation();
  const sortable = useSortable({ id: task.id, index, group: column.id, data: { taskId: task.id, columnId: column.id, task }, disabled });
  return <article ref={sortable.ref} data-task-id={task.id} className={`project-task-card${sortable.isDragging ? " project-task-card--dragging" : ""}${sortable.isDropping ? " project-task-card--dropping" : ""}`}>
    <Checkbox className="route-board-check" aria-label={`Выполнить: ${task.title}`} isSelected={task.status === "done"} isDisabled={disabled || update.isPending || task.recurrence_type_code !== "none"} onChange={(checked) => update.mutate({taskId:task.id,payload:{status:checked ? "done" : "todo"}})} />
    <button className="project-task-card__content" type="button" onClick={onOpen}><strong>{task.title}</strong>{task.description ? <p>{task.description}</p> : null}<span><CalendarDays size={15} />{formatDate(task.planned_date, task.planned_time)}</span>{task.deadline_date ? <small>Дедлайн: {formatDate(task.deadline_date, task.deadline_time)}</small> : null}</button>
    <button ref={sortable.handleRef} className="project-task-card__handle" type="button" aria-label={`Переместить задачу ${task.title}`}><GripVertical size={17} /></button>
    {update.isError ? <p className="route-board-error" role="alert">Не удалось изменить задачу.</p> : null}
  </article>;
}

function ProjectColumnView({ column, tasks, disabled, onOpenTask, onCreateTask }: { column: ProjectColumn; tasks: Task[]; disabled: boolean; onOpenTask: (taskId: string) => void; onCreateTask: (columnId: string) => void }) {
  const droppable = useDroppable({ id: `column:${column.id}`, data: { columnId: column.id } });
  return <section ref={droppable.ref} data-column-id={column.id} className={`project-column project-column--${column.position % 5}${droppable.isDropTarget ? " project-column--over" : ""}`}>
    <header><h2>{column.title} <span>{tasks.length}</span></h2><MoreHorizontal size={18} /></header>
    <div className="project-column__tasks">{tasks.map((task, index) => <ProjectTaskCard key={task.id} task={task} column={column} index={index} disabled={disabled} onOpen={() => onOpenTask(task.id)} />)}{tasks.length === 0 ? <div className="project-column__empty">Перетащите задачу сюда</div> : null}</div>
    <button className="project-column__add" type="button" onClick={() => onCreateTask(column.id)}><Plus size={17} />Добавить задачу</button>
  </section>;
}

function ProjectBoardColumns({ columns, tasks, boardRef, disabled, onOpenTask, onCreateTask }: { columns: ProjectColumn[]; tasks: Task[]; boardRef: RefObject<HTMLDivElement | null>; disabled: boolean; onOpenTask: (taskId: string) => void; onCreateTask: (columnId: string) => void }) {
  const { source } = useDragOperation();
  const [dragTasks, setDragTasks] = useState(tasks);
  useEffect(() => {
    if (!source) setDragTasks(tasks);
  }, [source, tasks]);
  // Сохраняем DOM карточек до завершения drop-анимации: их позициями управляет dnd-kit.
  const visibleTasks = source ? dragTasks : tasks;
  return <div ref={boardRef} className="project-board">{columns.map((column) => <ProjectColumnView key={column.id} column={column} tasks={visibleTasks.filter((task) => task.project_column_id === column.id).sort((a, b) => (a.project_position ?? 0) - (b.project_position ?? 0))} disabled={disabled} onOpenTask={onOpenTask} onCreateTask={onCreateTask} />)}</div>;
}

function ProjectBoard({ projectId, columns, tasks, onOpenTask, onCreateTask }: { projectId: string; columns: ProjectColumn[]; tasks: Task[]; onOpenTask: (taskId: string) => void; onCreateTask: (columnId: string) => void }) {
  const mutation = useMoveProjectTaskMutation(projectId);
  const [dndError, setDndError] = useState<string | null>(null);
  const boardRef = useRef<HTMLDivElement>(null);
  const dropTarget = useRef<{ columnId: string; position: number } | null>(null);

  async function handleDragEnd(event: DragEndEvent) {
    if (event.canceled || !event.operation.source || !event.operation.target) {
      return;
    }
    const taskId = String(event.operation.source.id);
    const task = tasks.find((item) => item.id === taskId);
    if (!task) {
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
      } else {
        const center = event.operation.shape?.current.center ?? event.operation.position.current;
        if (event.operation.target.shape && center.y > event.operation.target.shape.center.y) targetPosition += 1;
      }
    } else {
      const data = event.operation.target.data as { columnId?: string } | undefined;
      targetColumnId = data?.columnId;
      targetPosition = tasks.filter((item) => item.project_column_id === targetColumnId).length;
    }
    if (!targetColumnId) {
      return;
    }
    const targetColumn = columns.find((column) => column.id === targetColumnId);
    if (task.recurrence_type_code !== "none" && targetColumn?.is_completion_column) {
      setDndError("Повторяющуюся задачу нельзя переносить в завершающий этап.");
      event.suspend().abort();
      return;
    }
    if (task.project_column_id === targetColumnId && task.project_position === targetPosition) {
      return;
    }
    setDndError(null);
    const suspension = event.suspend();
    try {
      await mutation.mutateAsync({ taskId, targetColumnId, targetPosition });
      dropTarget.current = { columnId: targetColumnId, position: targetPosition };
      suspension.resume();
    } catch {
      suspension.abort();
    }
  }

  return <>
    {dndError || mutation.isError ? <div className="project-board__error" role="alert">{dndError ?? "Не удалось переместить задачу. Порядок восстановлен."}</div> : null}
    <DragDropProvider
      onDragStart={() => { dropTarget.current = null; }}
      onDragOver={(event) => {
        // React сам переносит карточку между контейнерами после drop, сохраняя владение DOM.
        if (event.operation.source && event.operation.target && isSortableOperation(event.operation) && event.operation.source.sortable.group !== event.operation.target.sortable.group) event.preventDefault();
      }}
      onDragEnd={handleDragEnd}
    >
      <ProjectBoardColumns columns={columns} tasks={tasks} boardRef={boardRef} disabled={mutation.isPending} onOpenTask={onOpenTask} onCreateTask={onCreateTask} />
      <DragOverlay dropAnimation={async ({ source, element, feedbackElement }) => {
        const destination = dropTarget.current;
        const container = destination ? boardRef.current?.querySelector<HTMLElement>(`[data-column-id="${destination.columnId}"] .project-column__tasks`) : null;
        const current = feedbackElement.getBoundingClientRect();
        let final = element.getBoundingClientRect();
        if (container && destination) {
          const allCards = Array.from(container.querySelectorAll<HTMLElement>(".project-task-card"));
          const sourceIndex = allCards.findIndex((card) => card.dataset.taskId === String(source.id));
          const cards = allCards.filter((card) => card.dataset.taskId !== String(source.id));
          const nextCard = cards[destination.position];
          const previousCard = cards[destination.position - 1];
          const bounds = container.getBoundingClientRect();
          const styles = getComputedStyle(container);
          const left = bounds.left + parseFloat(styles.paddingLeft);
          const top = nextCard ? nextCard.getBoundingClientRect().top : previousCard ? previousCard.getBoundingClientRect().bottom + parseFloat(styles.rowGap) : bounds.top + parseFloat(styles.paddingTop) - container.scrollTop;
          final = sourceIndex === destination.position ? allCards[sourceIndex].getBoundingClientRect() : new DOMRect(left, top, container.clientWidth - parseFloat(styles.paddingLeft) - parseFloat(styles.paddingRight), current.height);
        }
        // Двигаем содержимое overlay, чтобы не конфликтовать с позиционированием dnd-kit.
        const preview = feedbackElement.firstElementChild;
        if (!preview) return;
        const animation = preview.animate({
          translate: ["0px 0px", `${final.left - current.left}px ${final.top - current.top}px`]
        }, { duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 280, easing: "cubic-bezier(.2,.75,.2,1)", fill: "forwards" });
        try {
          await animation.finished;
        } finally {
          animation.cancel();
        }
      }}>
        {(source) => {
          const task = source.data.task as Task;
          return <div className={`project-task-card project-task-card--overlay${source.isDropping ? " project-task-card--dropping" : ""}`} style={{ width: "100%", height: "100%" }}>
            <span className="route-board-check ui-checkbox" aria-hidden="true"><span className="ui-checkbox__indicator">{task.status === "done" ? <CheckCircle2 size={18} /> : null}</span></span>
            <div className="project-task-card__content"><strong>{task.title}</strong>{task.description ? <p>{task.description}</p> : null}<span><CalendarDays size={15} />{formatDate(task.planned_date, task.planned_time)}</span>{task.deadline_date ? <small>Дедлайн: {formatDate(task.deadline_date, task.deadline_time)}</small> : null}</div>
            <div className="project-task-card__handle" style={{ display: "grid", placeItems: "center" }}><GripVertical size={17} /></div>
          </div>;
        }}
      </DragOverlay>
    </DragDropProvider>
  </>;
}

function ProjectList({ projectId, columns, tasks, onOpenTask }: { projectId: string; columns: ProjectColumn[]; tasks: Task[]; onOpenTask: (taskId: string) => void }) {
  const bulk = useProjectBulkMutations(projectId);
  const [selected, setSelected] = useState<string[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [targetColumn, setTargetColumn] = useState(columns[0]?.id ?? "");
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const page = tasks.slice(offset, offset + limit);
  const allPageSelected = page.length > 0 && page.every((task) => selected.includes(task.id));
  const pending = bulk.move.isPending || bulk.status.isPending;
  useEffect(() => {
    setSelected((current) => current.filter((id) => tasks.some((task) => task.id === id)));
    if (offset >= tasks.length && offset > 0) setOffset(Math.max(0,(Math.ceil(tasks.length / limit)-1)*limit));
  }, [tasks, offset, limit]);
  return <div className="project-list-panel">
    {selected.length ? <div className="project-list-bulk"><strong>Выбрано: {selected.length}</strong><SelectCombobox label="Переместить в этап" value={targetColumn} onChange={setTargetColumn} isDisabled={pending} options={columns.map((column) => ({ value: column.id, label: column.title }))} /><button type="button" disabled={pending || !targetColumn} onClick={() => bulk.move.mutate({ taskIds: selected, targetColumnId: targetColumn })}>Переместить в этап</button><button type="button" disabled={pending} onClick={() => bulk.status.mutate({ taskIds: selected, status: "done" })}><CheckCircle2 size={18} aria-hidden="true" />Отметить выполненными</button><button type="button" disabled={pending} onClick={() => setSelected([])}>Снять выделение</button></div> : null}
    {bulk.move.isError || bulk.status.isError ? <p className="project-board__error" role="alert">Не удалось применить действие. Повторяющиеся задачи нельзя переносить в завершающий этап или завершать целиком.</p> : null}
    <div className="project-list-scroll"><table className="project-list-table"><thead><tr><th><Checkbox aria-label="Выбрать страницу" isSelected={allPageSelected} isIndeterminate={!allPageSelected && page.some((task) => selected.includes(task.id))} onChange={(checked) => setSelected(checked ? [...new Set([...selected, ...page.map((task) => task.id)])] : selected.filter((id) => !page.some((task) => task.id === id)))} /></th><th>Задача</th><th>Этап</th><th>Когда делать</th><th>Дедлайн</th><th>Обновлено</th></tr></thead><tbody>{page.map((task) => <Fragment key={task.id}><tr className={expanded === task.id ? "route-project-row--expanded" : task.deadline_date && task.deadline_date < getTodayValue() && task.status === "todo" ? "overdue" : ""}><td><Checkbox aria-label={`Выбрать ${task.title}`} isSelected={selected.includes(task.id)} onChange={(checked) => setSelected(checked ? [...selected, task.id] : selected.filter((id) => id !== task.id))} /></td><td><button type="button" aria-expanded={expanded === task.id} aria-controls={expanded === task.id ? `project-inline-${task.id}` : undefined} onClick={() => setExpanded(expanded === task.id ? null : task.id)}>{task.title}</button></td><td><span>{columns.find((column) => column.id === task.project_column_id)?.title ?? "—"}</span></td><td>{formatDate(task.planned_date, task.planned_time)}</td><td>{formatDate(task.deadline_date, task.deadline_time)}</td><td>{new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(task.updated_at))}</td></tr>{expanded === task.id ? <tr className="route-project-inline"><td colSpan={6}><TaskInlineDetails task={task} id={`project-inline-${task.id}`} /><button type="button" className="route-inline-more" onClick={() => onOpenTask(task.id)}>Все действия и сведения</button></td></tr> : null}</Fragment>)}</tbody></table>{!tasks.length ? <div className="route-empty"><h2>Задачи не найдены</h2><p>Измените фильтры или добавьте задачу.</p></div> : null}</div>
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
    () => filterProjectTasks(tasksQuery.data?.items ?? [], query, dateFilter, selectedDate, stage, status),
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
    <header className="project-page__header"><div><p><Link to={appRoutePaths.projects.all}>Проекты</Link> / {project.title}</p><h1>{project.title}</h1><span>{project.description || "Без описания"}</span></div><div><button type="button" className="project-icon-button" aria-label="Настройки проекта" onClick={() => setSettingsOpen(true)}><Settings2 size={19} aria-hidden="true" />Настройки проекта</button><button type="button" className="projects-primary-button" onClick={() => setCreateColumnId(columns[0]?.id ?? "")}><Plus size={18} />Новая задача</button></div></header>
    <div className="project-toolbar">
      <div className="project-view-switch"><button aria-pressed={!isList} className={!isList ? "active" : ""} type="button" onClick={() => navigate(appRoutePaths.projects.board(project.id))}>Доска</button><button aria-pressed={isList} className={isList ? "active" : ""} type="button" onClick={() => navigate(appRoutePaths.projects.list(project.id))}>Список</button></div>
      <label className="projects-search"><Search size={16} /><input aria-label="Поиск по проекту" placeholder="Поиск по проекту" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
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
    {tasksQuery.isError ? <div className="project-board__error" role="alert">Не удалось загрузить задачи проекта. <button type="button" disabled={tasksQuery.isFetching} onClick={() => void tasksQuery.refetch()}>Повторить</button></div> : isList ? <ProjectList projectId={project.id} columns={columns} tasks={tasks} onOpenTask={setTaskDetailsId} /> : <ProjectBoard projectId={project.id} columns={columns} tasks={tasks} onOpenTask={setTaskDetailsId} onCreateTask={setCreateColumnId} />}
    {settingsOpen ? <ProjectSettingsDrawer project={project} onClose={() => setSettingsOpen(false)} /> : null}
    {createColumnId !== null ? <CreateTaskDrawer initialProjectId={project.id} initialProjectColumnId={createColumnId} onClose={() => setCreateColumnId(null)} /> : null}
    {taskDetailsId ? <TaskDetailsDrawer taskId={taskDetailsId} onClose={() => setTaskDetailsId(null)} /> : null}
  </div>;
}
