import { Check, Minus } from "lucide-react";
import {
  Checkbox as CheckboxPrimitive,
  composeRenderProps,
  type CheckboxProps,
} from "react-aria-components";

// Checkbox shadcn/ui (React Aria), адаптированный к CSS-системе проекта.
export function Checkbox({ className, children, title, ...props }: CheckboxProps & { title?: string }) {
  return (
    <CheckboxPrimitive
      {...props}
      data-slot="checkbox"
      className={composeRenderProps(className, (name) =>
        ["ui-checkbox", name].filter(Boolean).join(" "),
      )}
    >
      {composeRenderProps(children, (content, { isSelected, isIndeterminate }) => (
        <>
          <span className="ui-checkbox__indicator" data-slot="checkbox-indicator" aria-hidden="true" title={title}>
            {isIndeterminate ? <Minus size={12} strokeWidth={3} /> :
              isSelected ? <Check size={12} strokeWidth={3} /> : null}
          </span>
          {content}
        </>
      ))}
    </CheckboxPrimitive>
  );
}
