import { Clock3 } from "lucide-react";
import type { TaskRecurrenceType, TaskRecurrenceTypeCode, TaskStatus, TaskStatusCode } from "../../entities/task/types";
import { formatCompactDate, getTodayValue, formatDateValue } from "../../shared/date-values";
import { DatePickerPopover } from "../../shared/ui/date-picker-popover";
import { RadioGroup, RadioGroupItem } from "../../shared/ui/radio-group";
import { SelectCombobox } from "../../shared/ui/select-combobox";
import { getRecurrenceLabel } from "./recurrence";

type TaskFormFieldsProps = {
  title: string; description: string; status: TaskStatusCode;
  plannedDate: string; plannedTime: string; deadlineDate: string; deadlineTime: string;
  recurrenceType: TaskRecurrenceTypeCode; recurrenceInterval: number;
  recurrenceStartDate: string; recurrenceEndDate: string;
  titleError: string | null;
  statuses: TaskStatus[] | undefined; statusLoading: boolean; statusError: boolean;
  onRetryStatuses: () => void; recurrenceTypes: TaskRecurrenceType[];
  onTitleChange: (value: string) => void; onDescriptionChange: (value: string) => void;
  onStatusChange: (value: TaskStatusCode) => void;
  onPlannedDateChange: (value: string) => void; onPlannedTimeChange: (value: string) => void;
  onDeadlineDateChange: (value: string) => void; onDeadlineTimeChange: (value: string) => void;
  onRecurrenceTypeChange: (value: TaskRecurrenceTypeCode) => void;
  onRecurrenceIntervalChange: (value: number) => void;
  onRecurrenceStartDateChange: (value: string) => void; onRecurrenceEndDateChange: (value: string) => void;
};

function DateField({ label, value, onChange, placeholder = "Выберите дату" }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string }) {
  return <div className="task-calendar-input">
    <DatePickerPopover mode="single" label={label} buttonLabel={value ? formatCompactDate(value) : placeholder} value={value} onChange={onChange} />
    {value ? <button type="button" className="task-calendar-input__clear" aria-label={`Очистить: ${label}`} onClick={() => onChange("")}>×</button> : null}
  </div>;
}

function TimeField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="task-date-input"><Clock3 size={17} aria-hidden="true" /><input type="time" aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} /></label>;
}

export function TaskFormFields(props: TaskFormFieldsProps) {
  const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1);
  const shortcuts = [{ label: "Сегодня", value: getTodayValue() }, { label: "Завтра", value: formatDateValue(tomorrow) }, { label: "Без даты", value: "" }];
  return <>
    <label className="task-create-field">
      <span>Название <b aria-hidden="true">*</b></span>
      <input autoFocus value={props.title} onChange={(event) => props.onTitleChange(event.target.value)} aria-invalid={Boolean(props.titleError)} aria-describedby={props.titleError ? "task-form-title-error" : undefined} placeholder="Введите название задачи" maxLength={255} />
      {props.titleError ? <small id="task-form-title-error" className="task-create-field__error">{props.titleError}</small> : null}
    </label>
    <label className="task-create-field"><span>Описание</span><textarea value={props.description} onChange={(event) => props.onDescriptionChange(event.target.value)} placeholder="Краткое описание задачи (необязательно)" rows={3} /></label>
    {props.recurrenceType === "none" ? <fieldset className="task-create-fieldset">
      <legend>Статус</legend>
      {props.statusLoading ? <p className="task-create-fieldset__state">Загружаем статусы…</p> : null}
      {props.statusError ? <div className="task-create-fieldset__error" role="alert">Не удалось загрузить статусы. <button type="button" onClick={props.onRetryStatuses}>Повторить</button></div> : null}
      <RadioGroup className="task-status-options" aria-label="Статус задачи" name="task-status" orientation="horizontal" value={props.status} onChange={(value) => {
        const option = props.statuses?.find((item) => item.code === value);
        if (option) props.onStatusChange(option.code);
      }}>
        {[...(props.statuses ?? [])].sort((a, b) => a.sort_order - b.sort_order).map((option) => (
          <RadioGroupItem key={option.code} value={option.code} className="task-status-option"><span>{option.title}</span></RadioGroupItem>
        ))}
      </RadioGroup>
    </fieldset> : null}
    <fieldset className="task-create-fieldset">
      <legend>Когда делать (план)</legend>
      <div className="task-date-shortcuts">{shortcuts.map(({ value, label }) => <button type="button" key={label} aria-pressed={props.plannedDate === value} className={props.plannedDate === value ? "task-date-shortcut--active" : undefined} onClick={() => props.onPlannedDateChange(value)}>{label}</button>)}</div>
      <div className="task-plan-inputs"><DateField label="Плановая дата" value={props.plannedDate} onChange={props.onPlannedDateChange} /><TimeField label="Плановое время" value={props.plannedTime} onChange={props.onPlannedTimeChange} /></div>
    </fieldset>
    <fieldset className="task-create-fieldset"><legend>Дедлайн</legend><div className="task-plan-inputs"><DateField label="Дата дедлайна" placeholder="Выберите дату (необязательно)" value={props.deadlineDate} onChange={props.onDeadlineDateChange} /><TimeField label="Время дедлайна" value={props.deadlineTime} onChange={props.onDeadlineTimeChange} /></div></fieldset>
    <fieldset className="task-create-fieldset">
      <legend>Повторение</legend>
      <SelectCombobox className="task-recurrence-select" label="Повторение" value={props.recurrenceType} onChange={(value) => props.onRecurrenceTypeChange(value as TaskRecurrenceTypeCode)} options={[...props.recurrenceTypes].sort((a, b) => a.sort_order - b.sort_order).map((option) => ({ value: option.code, label: getRecurrenceLabel(option.code, 1) }))} />
      {props.recurrenceType !== "none" ? <div className="task-recurrence-inputs">
        {props.recurrenceType === "daily" || props.recurrenceType === "weekly" ? <label className="task-create-field"><span>{props.recurrenceType === "daily" ? "Интервал в днях" : "Интервал в неделях"}</span><input type="number" min={1} value={props.recurrenceInterval} onChange={(event) => props.onRecurrenceIntervalChange(Math.max(1, Number(event.target.value) || 1))} /></label> : null}
        <div className="task-recurrence-dates"><div className="task-create-field"><span>Начало</span><DateField label="Начало повторения" value={props.recurrenceStartDate} onChange={props.onRecurrenceStartDateChange} /></div><div className="task-create-field"><span>Окончание</span><DateField label="Окончание повторения" value={props.recurrenceEndDate} onChange={props.onRecurrenceEndDateChange} /></div></div>
      </div> : null}
    </fieldset>
  </>;
}
