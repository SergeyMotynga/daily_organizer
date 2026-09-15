import type { ComponentProps } from "react";
import { Group, Input, composeRenderProps, type GroupProps } from "react-aria-components";

// InputGroup shadcn/ui (React Aria), адаптированный к CSS-системе проекта.
export function InputGroup({ className, ...props }: GroupProps) {
  return <Group {...props} data-slot="input-group" className={composeRenderProps(className,
    (name) => ["ui-input-group", name].filter(Boolean).join(" "))} />;
}

export function InputGroupInput({ className, ...props }: ComponentProps<typeof Input>) {
  return <Input {...props} data-slot="input-group-control" className={composeRenderProps(className,
    (name) => ["ui-input-group__input", name].filter(Boolean).join(" "))} />;
}

export function InputGroupAddon({ className, align = "inline-start", onClick, ...props }:
  ComponentProps<"div"> & { align?: "inline-start" | "inline-end" }) {
  return <div {...props} data-slot="input-group-addon" data-align={align}
    className={["ui-input-group__addon", className].filter(Boolean).join(" ")}
    onClick={(event) => {
      onClick?.(event);
      if (!event.defaultPrevented && !(event.target as HTMLElement).closest("button")) {
        event.currentTarget.parentElement?.querySelector("input")?.focus();
      }
    }} />;
}
