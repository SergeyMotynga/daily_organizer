import { useState } from "react";
import { Archive, CalendarDays, Clock3, Folder, MoreHorizontal, Pencil, Repeat2 } from "lucide-react";
import type { Task, TaskStatusCode } from "../../entities/task/types";
import { formatCompactDate } from "../../shared/date-values";
import { Checkbox } from "../../shared/ui/checkbox";
import { useProjectsQuery } from "../projects/queries";
import { EditTaskDrawer } from "./edit-task-drawer";
import { TaskDetailsDrawer } from "./task-details-drawer";
import { useUpdateTaskMutation } from "./queries";
import { getRecurrenceLabel, isTaskRecurring } from "./recurrence";

type TaskListItemProps = {
  task: Task;
  expanded: boolean;
  onExpand: () => void;
  onStatusChange: (status: TaskStatusCode) => void;
  isPending: boolean;
  showTime?: boolean;
  showPlan?: boolean;
};

export function TaskInlineDetails({ task, id, isPending = false }: { task: Task; id?: string; isPending?: boolean }) {
  const [editing, setEditing] = useState(false);
  const archiveMutation = useUpdateTaskMutation();
  const plannedDate = task.occurrence_date ?? task.planned_date;
  return <div className="route-task__details" id={id}>
      <p>{task.description || "Описание не добавлено."}</p>
      <div className="route-task__metadata">
        <span><CalendarDays size={21} aria-hidden="true" />План: {plannedDate ? formatCompactDate(plannedDate) : "Без даты"}{task.planned_time ? `, ${task.planned_time.slice(0, 5)}` : ""}</span>
        <span><Clock3 size={21} aria-hidden="true" />Дедлайн: {task.deadline_date ? formatCompactDate(task.deadline_date) : "Без даты"}{task.deadline_time ? `, ${task.deadline_time.slice(0, 5)}` : ""}</span>
        <span><Repeat2 size={21} aria-hidden="true" />{getRecurrenceLabel(task.recurrence_type_code, task.recurrence_interval)}</span>
      </div>
      <div className="route-task__footer">
        <button type="button" onClick={() => setEditing(true)}><Pencil size={20} aria-hidden="true" />Редактировать</button>
        <button type="button" disabled={isPending || archiveMutation.isPending} onClick={() => archiveMutation.mutate({ taskId: task.id, payload: { archived: true } })}><Archive size={20} aria-hidden="true" />В архив</button>
      </div>
      {archiveMutation.isError ? <p className="task-create-error" role="alert">Не удалось архивировать задачу. Попробуйте ещё раз.</p> : null}
    {editing ? <EditTaskDrawer taskId={task.id} onClose={() => setEditing(false)} /> : null}
    </div>;

}

export function TaskListItem({ task, expanded, onExpand, onStatusChange, isPending, showTime = true, showPlan = false }: TaskListItemProps) {
  const [dialog, setDialog] = useState(false);
  const projects = useProjectsQuery(false).data;
  const isRecurring = isTaskRecurring(task);
  const isDone = task.status === "done";
  const projectName = projects?.items.find((project) => project.id === task.project_id)?.title ?? (task.project_id ? "Проект" : "Личное");
  const plannedDate = task.occurrence_date ?? task.planned_date;
  const now = new Date();
  const overdue = task.deadline_date && new Date(`${task.deadline_date}T${task.deadline_time ?? "23:59:59"}`) < now;
  const detailsId = `task-inline-${task.id}-${task.occurrence_date ?? "rule"}`;
  const busy = isPending;

  return <article className={`route-task${expanded ? " route-task--expanded" : ""}${isDone ? " route-task--done" : ""}${!showTime ? " route-task--no-time" : ""}`}>
    <div className="route-task__row">
      {showTime ? <span className="route-task__time">{task.planned_time?.slice(0, 5) ?? "—"}</span> : null}
      <Checkbox className="route-task__check" isSelected={isDone} isDisabled={busy || (isRecurring && !task.occurrence_date)} onChange={(selected) => onStatusChange(selected ? "done" : "todo")} aria-label={`${isDone ? "Вернуть в активные" : "Выполнить"}: ${task.title}`} />
      <div className="route-task__copy">
        <button className="route-task__title" type="button" onClick={onExpand} aria-expanded={expanded} aria-controls={expanded ? detailsId : undefined}>{task.title}</button>
        <div className="route-task__meta"><Folder size={17} aria-hidden="true" />{projectName}
          {isRecurring ? <span>· {getRecurrenceLabel(task.recurrence_type_code, task.recurrence_interval)}</span> : null}
          {showPlan && plannedDate ? <span>· План: {formatCompactDate(plannedDate)}</span> : null}
        </div>
      </div>
      {task.deadline_date && !isDone ? <span className={`route-task__deadline${overdue ? " route-task__deadline--overdue" : ""}`}><Clock3 size={20} aria-hidden="true" />{overdue ? "Дедлайн истёк · " : "до "}{formatCompactDate(task.deadline_date)}{task.deadline_time ? `, ${task.deadline_time.slice(0, 5)}` : ""}</span> : null}
      <button className="route-task__more" type="button" aria-label={`Действия: ${task.title}`} onClick={() => setDialog(true)}><MoreHorizontal size={23} aria-hidden="true" /></button>
    </div>
    {expanded ? <TaskInlineDetails task={task} id={detailsId} isPending={isPending} /> : null}
    {dialog ? <TaskDetailsDrawer taskId={task.id} onClose={() => setDialog(false)} /> : null}
  </article>;
}
