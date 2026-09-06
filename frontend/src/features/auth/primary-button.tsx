import type { ButtonHTMLAttributes, ReactNode } from "react";

type PrimaryButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export function PrimaryButton({ children, className, ...props }: PrimaryButtonProps) {
  const buttonClassName = className ? `primary-button ${className}` : "primary-button";

  return (
    <span className="primary-button-shell">
      <span className="primary-button-shell__glow" aria-hidden="true" />
      <button className={buttonClassName} {...props}>
        {children}
      </button>
    </span>
  );
}
