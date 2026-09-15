import {
  Radio as RadioPrimitive,
  RadioGroup as RadioGroupPrimitive,
  composeRenderProps,
  type RadioGroupProps,
  type RadioProps,
} from "react-aria-components";

export function RadioGroup({ className, ...props }: RadioGroupProps) {
  return (
    <RadioGroupPrimitive
      {...props}
      data-slot="radio-group"
      className={composeRenderProps(className, (name) => ["ui-radio-group", name].filter(Boolean).join(" "))}
    />
  );
}

export function RadioGroupItem({ className, children, ...props }: RadioProps) {
  return (
    <RadioPrimitive
      {...props}
      data-slot="radio-group-item"
      className={composeRenderProps(className, (name) => ["ui-radio", name].filter(Boolean).join(" "))}
    >
      {composeRenderProps(children, (content) => (
        <>
          <span className="ui-radio__indicator" aria-hidden="true"><span /></span>
          {content}
        </>
      ))}
    </RadioPrimitive>
  );
}
