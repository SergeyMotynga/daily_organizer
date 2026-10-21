import { useState } from "react";
import { DayPicker, type DateRange } from "@daypicker/react";
import { ru } from "@daypicker/react/locale/ru";
import type { DateRangeValue } from "../../shared/date-values";
import { formatCompactDate, formatDateValue, parseDateValue } from "../../shared/date-values";

type TaskDateFiltersProps = {
  date?: string;
  range: DateRangeValue;
  onApply: (value: { date?: string; range?: DateRangeValue }) => void;
};

// Один постоянно видимый календарь для выбора дня и периода.
export function TaskDateFilters({ date, range, onApply }: TaskDateFiltersProps) {
  const [mode, setMode] = useState<"single" | "range">(range.from || range.to ? "range" : "single");
  const [day, setDay] = useState(parseDateValue(date));
  const [period, setPeriod] = useState<DateRange | undefined>(range.from || range.to ? { from: parseDateValue(range.from), to: parseDateValue(range.to) } : undefined);
  const singleLabel = day ? formatCompactDate(formatDateValue(day)) : "Все даты";
  const rangeLabel = period?.from ? `${formatCompactDate(formatDateValue(period.from))}–${period.to ? formatCompactDate(formatDateValue(period.to)) : "…"}` : "Все даты";
  return <section className="route-date-filter">
    <header><h3>Плановая дата</h3><div className="route-segment route-segment--small" aria-label="Режим выбора даты">
      <button type="button" aria-pressed={mode === "single"} onClick={() => setMode("single")}>День</button><button type="button" aria-pressed={mode === "range"} onClick={() => setMode("range")}>Период</button>
    </div></header>
    <div className="route-calendar route-calendar--filter">
      {mode === "single" ? <DayPicker mode="single" locale={ru} showOutsideDays weekStartsOn={1} defaultMonth={day ?? period?.from} selected={day} onSelect={setDay} /> : <DayPicker mode="range" locale={ru} showOutsideDays weekStartsOn={1} resetOnSelect defaultMonth={period?.from ?? day} selected={period} onSelect={setPeriod} />}
    </div>
    <div className="route-date-selection"><span>{mode === "range" ? "Выбран период" : "Выбрано"}</span><strong>{mode === "single" ? singleLabel : rangeLabel}</strong></div>
    <div className="route-date-filter__actions"><button type="button" onClick={() => { setDay(undefined); setPeriod(undefined); onApply({}); }}>Сбросить</button><button type="button" disabled={mode === "single" ? !day : !period?.from || !period.to} onClick={() => onApply(mode === "single" ? { date: day ? formatDateValue(day) : undefined } : { range: { from: period?.from ? formatDateValue(period.from) : undefined, to: period?.to ? formatDateValue(period.to) : undefined } })}>Применить</button></div>
    <p>{mode === "single" ? "Выберите день в календаре и примените фильтр." : "Выберите начало и конец периода в календаре."}</p>
  </section>;
}
