import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { DayPicker } from "@daypicker/react";
import type { DateRange, DropdownProps } from "@daypicker/react";
import { ru } from "@daypicker/react/locale/ru";
import "@daypicker/react/style.css";
import { CalendarDays, ChevronDown } from "lucide-react";

import type { DateRangeValue } from "../date-values";
import { formatDateValue, parseDateValue } from "../date-values";
import { SelectCombobox } from "./select-combobox";

function CalendarDropdown({ options = [], value, onChange, disabled, "aria-label": ariaLabel }: DropdownProps) {
  return (
    <SelectCombobox
      className="date-picker__combobox"
      label={ariaLabel ?? "Выбор месяца или года"}
      value={String(value)}
      isDisabled={disabled}
      options={options.map((option) => ({ value: String(option.value), label: option.label, disabled: option.disabled }))}
      onChange={(nextValue) => onChange?.({ target: { value: nextValue } } as never)}
    />
  );
}

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
  const [month, setMonth] = useState(new Date());
  const [draftRange, setDraftRange] = useState<DateRange>();
  const rootRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ top: 0, left: 0 });

  useLayoutEffect(() => {
    if (!isOpen) return;
    function positionPopover() {
      const anchor = rootRef.current?.getBoundingClientRect();
      const popup = popoverRef.current?.getBoundingClientRect();
      if (!anchor || !popup) return;
      const left = Math.max(12, Math.min(anchor.left, window.innerWidth - popup.width - 12));
      const below = anchor.bottom + 8;
      const top = below + popup.height <= window.innerHeight - 12
        ? below : Math.max(12, anchor.top - popup.height - 8);
      setPosition({ top, left });
    }
    positionPopover();
    const observer = new ResizeObserver(positionPopover);
    if (popoverRef.current) observer.observe(popoverRef.current);
    window.addEventListener("resize", positionPopover);
    function handleScroll(event: Event) {
      const target = event.target;
      if (target instanceof Element && target.closest(".ui-combobox__popover")) return;
      positionPopover();
    }
    window.addEventListener("scroll", handleScroll, true);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", positionPopover);
      window.removeEventListener("scroll", handleScroll, true);
    };
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      const popup = popoverRef.current;
      const target = popup?.querySelector<HTMLButtonElement>(".rdp-selected .rdp-day_button")
        ?? popup?.querySelector<HTMLButtonElement>(".rdp-today .rdp-day_button")
        ?? popup?.querySelector<HTMLButtonElement>(".rdp-day_button");
      target?.focus({ preventScroll: true });
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handlePointerDown(event: PointerEvent) {
      const target = event.target;
      if (target instanceof Element && target.closest(".ui-combobox__popover")) return;
      if (!rootRef.current?.contains(target as Node) && !popoverRef.current?.contains(target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        if (document.querySelector(".ui-combobox[data-open]")) return;
        event.stopImmediatePropagation();
        setIsOpen(false);
        rootRef.current?.querySelector("button")?.focus({ preventScroll: true });
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown, true);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown, true);
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
        onClick={() => {
          if (!isOpen) {
            setMonth(defaultMonth);
            setDraftRange(selectedRange);
          }
          setIsOpen((current) => !current);
        }}
      >
        <CalendarDays size={15} aria-hidden="true" />
        <span>{props.buttonLabel}</span>
        <ChevronDown size={14} aria-hidden="true" />
      </button>
      {isOpen ? createPortal(
        <div ref={popoverRef} style={{ position: "fixed", ...position }} className="date-picker__popover" role="dialog" aria-label={props.label}>
          {props.mode === "single" ? (
            <DayPicker
              mode="single"
              locale={ru}
              weekStartsOn={1}
              captionLayout="dropdown"
              components={{ Dropdown: CalendarDropdown }}
              navLayout="around"
              showOutsideDays
              startMonth={new Date(2000, 0)}
              endMonth={new Date(2100, 11)}
              month={month}
              onMonthChange={setMonth}
              selected={selectedSingle}
              onSelect={(date) => {
                if (date) {
                  props.onChange(formatDateValue(date));
                  setIsOpen(false);
                  rootRef.current?.querySelector("button")?.focus({ preventScroll: true });
                }
              }}
            />
          ) : (
            <DayPicker
              mode="range"
              locale={ru}
              weekStartsOn={1}
              captionLayout="dropdown"
              components={{ Dropdown: CalendarDropdown }}
              navLayout="around"
              showOutsideDays
              startMonth={new Date(2000, 0)}
              endMonth={new Date(2100, 11)}
              resetOnSelect
              month={month}
              onMonthChange={setMonth}
              selected={draftRange}
              onSelect={(range) => {
                setDraftRange(range);
                const value = {
                  from: range?.from ? formatDateValue(range.from) : undefined,
                  to: range?.to ? formatDateValue(range.to) : undefined
                };
                if (value.from && value.to) {
                  props.onChange(value);
                  setIsOpen(false);
                  rootRef.current?.querySelector("button")?.focus({ preventScroll: true });
                }
              }}
            />
          )}
          <footer className="date-picker__footer"><button type="button" onClick={() => { if (props.mode === "single") props.onChange(formatDateValue(new Date())); else { const today = formatDateValue(new Date()); props.onChange({ from: today, to: today }); } setIsOpen(false); }}>Сегодня</button><button type="button" onClick={() => { setIsOpen(false); rootRef.current?.querySelector("button")?.focus(); }}>Закрыть</button></footer>
        </div>, document.body
      ) : null}
    </div>
  );
}
