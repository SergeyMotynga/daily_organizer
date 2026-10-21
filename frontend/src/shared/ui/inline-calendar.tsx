import { DayPicker } from "@daypicker/react";
import { ru } from "@daypicker/react/locale/ru";
import "@daypicker/react/style.css";
import { formatDateValue, parseDateValue } from "../date-values";

export function InlineCalendar({ value, onChange }: { value?: string; onChange: (value: string) => void }) {
  return <div className="route-calendar"><DayPicker mode="single" locale={ru} weekStartsOn={1} showOutsideDays selected={parseDateValue(value)} defaultMonth={parseDateValue(value)} onSelect={(date) => { if (date) onChange(formatDateValue(date)); }} /></div>;
}
