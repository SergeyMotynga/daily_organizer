import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Plus,
  Repeat2,
  RotateCcw
} from "lucide-react";
import { Link, useSearchParams } from "react-router";

import { appRoutePaths } from "../app/route-paths";
import type { CalendarTaskItem } from "../entities/task/types";
import { useCalendarViewQuery } from "../features/calendar/queries";
import { CreateTaskDrawer } from "../features/tasks/create-task-drawer";
import { TaskDetailsDrawer } from "../features/tasks/task-details-drawer";
import { useRecurrenceCompletionMutation, useUpdateTaskMutation } from "../features/tasks/queries";
import { Checkbox } from "../shared/ui/checkbox";
import { getRecurrenceLabel } from "../features/tasks/recurrence";
import {
  formatCompactDate,
  formatDateValue,
  getTodayValue,
  parseDateValue
} from "../shared/date-values";
import { DatePickerPopover } from "../shared/ui/date-picker-popover";

type CalendarView = "week" | "month";
type CalendarItemKind = "planned" | "deadline" | "recurrence";
type DatedCalendarItem = CalendarTaskItem & { kind: CalendarItemKind };

const weekdayLabels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function addDays(date: Date, days: number): Date {
  const nextDate = new Date(date);
  nextDate.setDate(nextDate.getDate() + days);
  return nextDate;
}

function addMonths(date: Date, months: number): Date {
  const day = date.getDate();
  const nextDate = new Date(date.getFullYear(), date.getMonth() + months, 1);
  const lastDay = new Date(nextDate.getFullYear(), nextDate.getMonth() + 1, 0).getDate();
  nextDate.setDate(Math.min(day, lastDay));
  return nextDate;
}

function startOfWeek(date: Date): Date {
  const weekday = date.getDay() || 7;
  return addDays(date, 1 - weekday);
}

function getVisibleDates(view: CalendarView, selectedDate: Date): Date[] {
  if (view === "week") {
    const firstDay = startOfWeek(selectedDate);
    return Array.from({ length: 7 }, (_, index) => addDays(firstDay, index));
  }

  const monthStart = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);
  const gridStart = startOfWeek(monthStart);
  const monthEnd = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0);
  const gridEnd = addDays(startOfWeek(monthEnd), 6);
  const daysCount = Math.round((gridEnd.getTime() - gridStart.getTime()) / 86_400_000) + 1;
  return Array.from({ length: daysCount }, (_, index) => addDays(gridStart, index));
}

function formatWeekRange(dates: Date[]): string {
  const first = dates[0];
  const last = dates[dates.length - 1];
  if (first.getMonth() === last.getMonth()) {
    const month = new Intl.DateTimeFormat("ru-RU", { month: "long" }).format(last);
    return `Неделя: ${first.getDate()}–${last.getDate()} ${month}`;
  }
  return `Неделя: ${formatCompactDate(formatDateValue(first))} – ${formatCompactDate(formatDateValue(last))}`;
}

function formatMonthLabel(date: Date): string {
  const value = new Intl.DateTimeFormat("ru-RU", { month: "long", year: "numeric" }).format(date);
  return `Месяц: ${value}`;
}

function formatDateJumpLabel(value: string): string {
  const date = parseDateValue(value);
  if (!date) {
    return value;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric"
  }).format(date);
}

function formatSelectedDate(date: Date): string {
  const value = new Intl.DateTimeFormat("ru-RU", {
    weekday: "short",
    day: "numeric",
    month: "long"
  })
    .format(date)
    .replace(".", "");
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function getItemDate(item: DatedCalendarItem): string | null {
  if (item.kind === "planned") {
    return item.task.planned_date;
  }
  if (item.kind === "deadline") {
    return item.task.deadline_date;
  }
  return item.occurrence_date;
}

function getItemTime(item: DatedCalendarItem): string | null {
  return item.kind === "deadline" ? item.task.deadline_time : item.task.planned_time;
}

function CalendarItemChip({ item, onOpen }: { item: DatedCalendarItem; onOpen: () => void }) {
  const time = getItemTime(item);
  return (
    <button
      className={`calendar-item calendar-item--${item.kind}${item.status === "done" ? " calendar-item--done" : ""}`}
      type="button"
      title={item.task.title}
      onClick={(event) => {
        event.stopPropagation();
        onOpen();
      }}
    >
      {item.kind === "deadline" ? (
        <AlertTriangle size={12} aria-hidden="true" />
      ) : item.kind === "recurrence" ? (
        <Repeat2 size={12} aria-hidden="true" />
      ) : time ? (
        <Clock3 size={12} aria-hidden="true" />
      ) : null}
      <span className="calendar-item__content">
        {item.kind === "deadline" ? (
          <span className="calendar-item__eyebrow">Дедлайн:</span>
        ) : null}
        <span className="calendar-item__main">
          {time ? <span className="calendar-item__time">{time}</span> : null}
          <span className="calendar-item__title">{item.task.title}</span>
        </span>
        {item.kind === "recurrence" ? (
          <span className="calendar-item__recurrence-label">
            {getRecurrenceLabel(
              item.task.recurrence_type_code,
              item.task.recurrence_interval
            )}
          </span>
        ) : null}
      </span>
    </button>
  );
}

function CalendarSideItem({ item, onOpen, showTime = false }: { item: DatedCalendarItem; onOpen: () => void; showTime?: boolean }) {
  const update = useUpdateTaskMutation();
  const completion = useRecurrenceCompletionMutation();
  const recurring = item.task.recurrence_type_code !== "none";
  const time = getItemTime(item);
  const recurrenceLabel =
    item.kind === "recurrence"
      ? getRecurrenceLabel(item.task.recurrence_type_code, item.task.recurrence_interval)
      : null;

  return (
    <div className="route-calendar-side-row">
      <Checkbox className="route-task__check" aria-label={`${item.status === "done" ? "Снять выполнение" : "Выполнить"}: ${item.task.title}`} isSelected={item.status === "done"} isDisabled={update.isPending || completion.isPending || (recurring && !item.occurrence_date)} onChange={(checked) => {
        if (recurring && item.occurrence_date) completion.mutate({ taskId: item.task.id, occurrenceDate: item.occurrence_date, completed: checked });
        else update.mutate({ taskId: item.task.id, payload: {status: checked ? "done" : "todo"} });
      }} />
    <button
      className={`calendar-side-item calendar-side-item--${item.kind}`}
      type="button"
      onClick={onOpen}
    >
      {(item.kind === "planned" || showTime) && time ? (
        <span className="calendar-side-item__time">{time}</span>
      ) : item.kind === "deadline" ? (
        <Clock3 size={17} aria-hidden="true" />
      ) : item.kind === "recurrence" ? (
        <Repeat2 size={17} aria-hidden="true" />
      ) : null}
      <span className="calendar-side-item__copy">
        <span>{item.task.title}</span>
        {item.kind === "deadline" && time ? ` — ${time}` : null}
        {recurrenceLabel ? <small> · {recurrenceLabel}</small> : null}
      </span>
    </button>
    {update.isError || completion.isError ? <span className="route-board-error" role="alert">Не удалось изменить задачу.</span> : null}
    </div>
  );
}

function CalendarMoreLink({ date, count }: { date: string; count: number }) {
  return (
    <Link
      className="calendar-more"
      to={`${appRoutePaths.tasks.planning}?planned_date=${date}&statuses=todo,done`}
      onClick={(event) => event.stopPropagation()}
    >
      +{count} ещё
    </Link>
  );
}

export function CalendarPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const rawView = searchParams.get("view");
  const view: CalendarView = rawView === "month" ? "month" : "week";
  const dateValue = parseDateValue(searchParams.get("date"))
    ? (searchParams.get("date") as string)
    : getTodayValue();
  const selectedDate = parseDateValue(dateValue) ?? new Date();
  const visibleDates = useMemo(
    () => getVisibleDates(view, selectedDate),
    [view, selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate()]
  );
  const dateFrom = formatDateValue(visibleDates[0]);
  const dateTo = formatDateValue(visibleDates[visibleDates.length - 1]);
  const calendarQuery = useCalendarViewQuery(dateFrom, dateTo);
  const [isCreateTaskOpen, setIsCreateTaskOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  useEffect(() => {
    if (searchParams.get("view") === view && searchParams.get("date") === dateValue) {
      return;
    }
    const nextSearchParams = new URLSearchParams(searchParams);
    nextSearchParams.set("view", view);
    nextSearchParams.set("date", dateValue);
    setSearchParams(nextSearchParams, { replace: true });
  }, [dateValue, searchParams, setSearchParams, view]);

  function updateCalendar(nextView: CalendarView, nextDate: string) {
    const nextSearchParams = new URLSearchParams(searchParams);
    nextSearchParams.set("view", nextView);
    nextSearchParams.set("date", nextDate);
    setSearchParams(nextSearchParams);
  }

  const itemsByDate = useMemo(() => {
    const grouped = new Map<string, DatedCalendarItem[]>();
    const addItems = (items: CalendarTaskItem[], kind: CalendarItemKind) => {
      items.forEach((item) => {
        const datedItem = { ...item, kind };
        const date = getItemDate(datedItem);
        if (!date) {
          return;
        }
        grouped.set(date, [...(grouped.get(date) ?? []), datedItem]);
      });
    };
    addItems(calendarQuery.data?.planned ?? [], "planned");
    addItems(calendarQuery.data?.deadlines ?? [], "deadline");
    addItems(calendarQuery.data?.recurrences ?? [], "recurrence");
    return grouped;
  }, [calendarQuery.data]);

  const selectedItems = itemsByDate.get(dateValue) ?? [];
  const selectedPlanned = selectedItems.filter((item) => item.kind !== "deadline");
  const selectedTimed = selectedPlanned.filter((item) => item.task.planned_time).sort((a, b) => (a.task.planned_time ?? "").localeCompare(b.task.planned_time ?? ""));
  const selectedUntimed = selectedPlanned.filter((item) => !item.task.planned_time);
  const selectedDeadlines = selectedItems.filter((item) => item.kind === "deadline");
  const selectedRecurrences = selectedItems.filter((item) => item.kind === "recurrence");

  return (
    <>
      <section className="calendar-page">
        <header className="calendar-page__header">
          <div>
            <h1>Календарь</h1>
            <p>Задачи и повторения по дням</p>
          </div>
          <button type="button" onClick={() => setIsCreateTaskOpen(true)}>
            <Plus size={18} aria-hidden="true" />
            Новая задача
          </button>
        </header>

        <div className="calendar-toolbar">
          <div className="calendar-view-switch" aria-label="Режим календаря">
            <button
              type="button"
              className={view === "week" ? "calendar-view-switch__active" : undefined}
              aria-pressed={view === "week"}
              onClick={() => updateCalendar("week", dateValue)}
            >
              Неделя
            </button>
            <button
              type="button"
              className={view === "month" ? "calendar-view-switch__active" : undefined}
              aria-pressed={view === "month"}
              onClick={() => updateCalendar("month", dateValue)}
            >
              Месяц
            </button>
          </div>
          <button
            className="calendar-toolbar__today"
            type="button"
            onClick={() => updateCalendar(view, getTodayValue())}
          >
            Сегодня
          </button>
          <div className="calendar-toolbar__navigation">
            <button
              type="button"
              aria-label={view === "week" ? "Предыдущая неделя" : "Предыдущий месяц"}
              onClick={() =>
                updateCalendar(
                  view,
                  formatDateValue(
                    view === "week" ? addDays(selectedDate, -7) : addMonths(selectedDate, -1)
                  )
                )
              }
            >
              <ChevronLeft size={17} aria-hidden="true" />
            </button>
            <button
              type="button"
              aria-label={view === "week" ? "Следующая неделя" : "Следующий месяц"}
              onClick={() =>
                updateCalendar(
                  view,
                  formatDateValue(
                    view === "week" ? addDays(selectedDate, 7) : addMonths(selectedDate, 1)
                  )
                )
              }
            >
              <ChevronRight size={17} aria-hidden="true" />
            </button>
          </div>
          <DatePickerPopover
            mode="single"
            className="calendar-toolbar__picker"
            label="Перейти к дате"
            buttonLabel={formatDateJumpLabel(dateValue)}
            value={dateValue}
            onChange={(value) => updateCalendar(view, value)}
          />
          <strong className="calendar-toolbar__range">
            {view === "week" ? formatWeekRange(visibleDates) : formatMonthLabel(selectedDate)}
          </strong>
        </div>

        {calendarQuery.isError ? (
          <section className="calendar-error" role="alert">
            <AlertCircle size={25} aria-hidden="true" />
            <div>
              <h2>Не удалось загрузить календарь</h2>
              <p>Проверьте подключение и попробуйте ещё раз.</p>
            </div>
            <button type="button" onClick={() => void calendarQuery.refetch()}>
              <RotateCcw size={15} aria-hidden="true" />
              Повторить
            </button>
          </section>
        ) : (
          <div className="calendar-layout" aria-busy={calendarQuery.isFetching}>
            <section className="calendar-board">
              {calendarQuery.isPending ? (
                <div className="calendar-loading">Загружаем календарь…</div>
              ) : view === "week" ? (
                <div className="calendar-week">
                  {visibleDates.map((date, index) => {
                    const dayValue = formatDateValue(date);
                    const items = itemsByDate.get(dayValue) ?? [];
                    const allDay = items.filter(
                      (item) => item.kind !== "deadline" && !getItemTime(item)
                    );
                    const timed = items.filter(
                      (item) => item.kind !== "deadline" && Boolean(getItemTime(item))
                    );
                    const deadlines = items.filter((item) => item.kind === "deadline");
                    const scheduled = [...timed.sort((a, b) => (getItemTime(a) ?? "").localeCompare(getItemTime(b) ?? "")), ...deadlines];
                    return (
                      <article
                        key={dayValue}
                        className={`calendar-week-day${dayValue === dateValue ? " calendar-day--selected" : ""}`}
                        onClick={() => updateCalendar(view, dayValue)}
                      >
                        <button className="calendar-day-heading" type="button">
                          <span>{weekdayLabels[index]}</span>
                          <strong>{date.getDate()}</strong>
                        </button>
                        <div className="calendar-all-day">
                          <span className="calendar-lane-label">Без времени</span>
                          {allDay.slice(0, 2).map((item) => (
                            <CalendarItemChip
                              key={`${item.kind}-${item.task.id}-${dayValue}`}
                              item={item}
                              onOpen={() => setSelectedTaskId(item.task.id)}
                            />
                          ))}
                          {allDay.length > 2 ? (
                            <CalendarMoreLink date={dayValue} count={allDay.length - 2} />
                          ) : null}
                        </div>
                        <div className="calendar-timed-items">
                          {scheduled.slice(0, 4).map((item) => (
                            <CalendarItemChip
                              key={`${item.kind}-${item.task.id}-${dayValue}`}
                              item={item}
                              onOpen={() => setSelectedTaskId(item.task.id)}
                            />
                          ))}
                          {scheduled.length > 4 ? (
                            <CalendarMoreLink date={dayValue} count={scheduled.length - 4} />
                          ) : null}
                        </div>
                      </article>
                    );
                  })}
                </div>
              ) : (
                <div className="calendar-month">
                  {weekdayLabels.map((label) => (
                    <div className="calendar-month__weekday" key={label}>
                      {label}
                    </div>
                  ))}
                  {visibleDates.map((date) => {
                    const dayValue = formatDateValue(date);
                    const items = itemsByDate.get(dayValue) ?? [];
                    const isOutside = date.getMonth() !== selectedDate.getMonth();
                    return (
                      <article
                        key={dayValue}
                        className={`calendar-month-day${dayValue === dateValue ? " calendar-day--selected" : ""}${isOutside ? " calendar-month-day--outside" : ""}`}
                        onClick={() => updateCalendar(view, dayValue)}
                      >
                        <button className="calendar-month-day__number" type="button">
                          {date.getDate()}
                        </button>
                        <div className="calendar-month-day__items">
                          {items.slice(0, 2).map((item) => (
                            <CalendarItemChip
                              key={`${item.kind}-${item.task.id}-${dayValue}`}
                              item={item}
                              onOpen={() => setSelectedTaskId(item.task.id)}
                            />
                          ))}
                          {items.length > 2 ? (
                            <CalendarMoreLink date={dayValue} count={items.length - 2} />
                          ) : null}
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>

            <aside className="calendar-selected-day">
              <header>
                <span>Выбранный день</span>
                <h2>{formatSelectedDate(selectedDate)}</h2>
              </header>
              <div className="calendar-selected-day__groups">
                {selectedTimed.length ? (
                  <section className="calendar-day-group">
                    <h3>По времени</h3>
                    {selectedTimed.map((item) => (
                      <CalendarSideItem
                        key={`${item.kind}-${item.task.id}-${dateValue}`}
                        item={item}
                        showTime
                        onOpen={() => setSelectedTaskId(item.task.id)}
                      />
                    ))}
                  </section>
                ) : null}

                {selectedUntimed.length ? (
                  <section className="calendar-day-group">
                    <h3>Без времени</h3>
                    {selectedUntimed.slice(0, 2).map((item) => (
                      <CalendarSideItem
                        key={`${item.kind}-${item.task.id}-${dateValue}`}
                        item={item}
                        onOpen={() => setSelectedTaskId(item.task.id)}
                      />
                    ))}
                    {selectedUntimed.length > 2 ? (
                      <Link
                        className="calendar-side-more"
                        to={`${appRoutePaths.tasks.planning}?planned_date=${dateValue}&statuses=todo,done`}
                      >
                        +{selectedUntimed.length - 2} ещё
                      </Link>
                    ) : null}
                  </section>
                ) : null}

                {selectedDeadlines.length ? (
                  <section className="calendar-day-group calendar-day-group--deadlines">
                    <h3>
                      Дедлайны
                      <AlertCircle size={18} aria-hidden="true" />
                    </h3>
                    {selectedDeadlines.slice(0, 3).map((item) => (
                      <CalendarSideItem
                        key={`${item.kind}-${item.task.id}-${dateValue}`}
                        item={item}
                        onOpen={() => setSelectedTaskId(item.task.id)}
                      />
                    ))}
                    {selectedDeadlines.length > 3 ? (
                      <Link
                        className="calendar-side-more"
                        to={`${appRoutePaths.tasks.planning}?deadline_date=${dateValue}&statuses=todo,done`}
                      >
                        +{selectedDeadlines.length - 3} ещё
                      </Link>
                    ) : null}
                  </section>
                ) : null}

                {selectedRecurrences.length ? (
                  <section className="calendar-day-group calendar-day-group--recurrences">
                    <h3>Повторения</h3>
                    {selectedRecurrences.map((item) => (
                      <CalendarSideItem
                        key={`${item.kind}-${item.task.id}-${dateValue}`}
                        item={item}
                        onOpen={() => setSelectedTaskId(item.task.id)}
                      />
                    ))}
                  </section>
                ) : null}
                {selectedItems.length === 0 ? (
                  <p className="calendar-selected-day__empty">На этот день задач нет.</p>
                ) : null}
              </div>
              <Link to={`${appRoutePaths.tasks.planning}?planned_date=${dateValue}&statuses=todo,done`}>Показать в планировании</Link>
            </aside>
          </div>
        )}
      </section>

      {isCreateTaskOpen ? (
        <CreateTaskDrawer onClose={() => setIsCreateTaskOpen(false)} />
      ) : null}
      {selectedTaskId ? (
        <TaskDetailsDrawer taskId={selectedTaskId} onClose={() => setSelectedTaskId(null)} />
      ) : null}
    </>
  );
}
