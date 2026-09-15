import { Check, ChevronDown } from "lucide-react";
import {
  Button,
  ListBox,
  ListBoxItem,
  Popover,
  Select,
  SelectValue,
  composeRenderProps,
  type Key,
} from "react-aria-components";

export type SelectComboboxOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

type SelectComboboxProps = {
  value: string;
  options: SelectComboboxOption[];
  label: string;
  onChange: (value: string) => void;
  className?: string;
  isDisabled?: boolean;
};

// Единый select на React Aria для всех одиночных списков приложения.
export function SelectCombobox({ value, options, label, onChange, className, isDisabled }: SelectComboboxProps) {
  return (
    <Select<SelectComboboxOption>
      aria-label={label}
      selectedKey={value}
      onSelectionChange={(key: Key | null) => { if (key !== null) onChange(String(key)); }}
      isDisabled={isDisabled}
      className={composeRenderProps(className, (name) => ["ui-combobox", name].filter(Boolean).join(" "))}
    >
      <Button className="ui-combobox__control">
        <SelectValue<SelectComboboxOption> className="ui-combobox__value" />
        <ChevronDown className="ui-combobox__chevron" size={14} aria-hidden="true" />
      </Button>
      <Popover className="ui-combobox__popover">
        <ListBox<SelectComboboxOption>
          items={options}
          renderEmptyState={() => <div className="ui-combobox__empty">Ничего не найдено</div>}
          onWheel={(event) => {
            const list = event.currentTarget;
            const reachedTop = event.deltaY < 0 && list.scrollTop <= 0;
            const reachedBottom = event.deltaY > 0 && list.scrollTop + list.clientHeight >= list.scrollHeight - 1;
            if (reachedTop || reachedBottom) event.preventDefault();
            event.stopPropagation();
          }}
        >
          {(option) => (
            <ListBoxItem id={option.value} textValue={option.label} isDisabled={option.disabled} className="ui-combobox__item">
              {({ isSelected }) => <><span>{option.label}</span>{isSelected ? <Check size={14} aria-hidden="true" /> : null}</>}
            </ListBoxItem>
          )}
        </ListBox>
      </Popover>
    </Select>
  );
}
