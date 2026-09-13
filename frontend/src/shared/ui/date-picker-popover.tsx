import { useEffect, useRef, useState } from "react";
import { DayPicker } from "@daypicker/react";
import type { DateRange } from "@daypicker/react";
import { ru } from "@daypicker/react/locale/ru";
import "@daypicker/react/style.css";
import { CalendarDays, ChevronDown } from "lucide-react";

import type { DateRangeValue } from "../date-values";
import { formatDateValue, parseDateValue } from "../date-values";

type DatePickerBaseProps = {
  label: string;
  buttonLabel: string;
  className?: string;
};

type SingleDatePickerProps = DatePickerBaseProps & {
  mode: "single";
  value?: string;
  onChange: (value: string) => void;
};

type RangeDatePickerProps = DatePickerBaseProps & {
  mode: "range";
  value: DateRangeValue;
  onChange: (value: DateRangeValue) => void;
};

type DatePickerPopoverProps = SingleDatePickerProps | RangeDatePickerProps;

export function DatePickerPopover(props: DatePickerPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handlePointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const selectedSingle = props.mode === "single" ? parseDateValue(props.value) : undefined;
  const selectedRange: DateRange | undefined =
    props.mode === "range"
      ? {
          from: parseDateValue(props.value.from),
          to: parseDateValue(props.value.to)
        }
      : undefined;
  const defaultMonth =
    selectedSingle ?? selectedRange?.from ?? selectedRange?.to ?? new Date();

  return (
    <div
      className={`date-picker${props.className ? ` ${props.className}` : ""}`}
      ref={rootRef}
    >
      <span className="date-picker__label">{props.label}</span>
      <button
        className="date-picker__trigger"
        type="button"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((current) => !current)}
      >
        <CalendarDays size={15} aria-hidden="true" />
        <span>{props.buttonLabel}</span>
        <ChevronDown size={14} aria-hidden="true" />
      </button>
      {isOpen ? (
        <div className="date-picker__popover" role="dialog" aria-label={props.label}>
          {props.mode === "single" ? (
            <DayPicker
              mode="single"
              locale={ru}
              weekStartsOn={1}
              captionLayout="dropdown"
              navLayout="after"
              startMonth={new Date(2000, 0)}
              endMonth={new Date(2100, 11)}
              defaultMonth={defaultMonth}
              selected={selectedSingle}
              onSelect={(date) => {
                if (date) {
                  props.onChange(formatDateValue(date));
                  setIsOpen(false);
                }
              }}
            />
          ) : (
            <DayPicker
              mode="range"
              locale={ru}
              weekStartsOn={1}
              captionLayout="dropdown"
              navLayout="after"
              startMonth={new Date(2000, 0)}
              endMonth={new Date(2100, 11)}
              resetOnSelect
              defaultMonth={defaultMonth}
              selected={selectedRange}
              onSelect={(range) => {
                const value = {
                  from: range?.from ? formatDateValue(range.from) : undefined,
                  to: range?.to ? formatDateValue(range.to) : undefined
                };
                props.onChange(value);
                if (value.from && value.to) {
                  setIsOpen(false);
                }
              }}
            />
          )}
        </div>
      ) : null}
    </div>
  );
}
