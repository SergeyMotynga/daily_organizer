import { useCallback, useEffect, useRef, useState } from "react";

// Даём панели закончить анимацию перед размонтированием формы.
export function useTaskDrawerTransition(onDismiss: () => void) {
  const [isClosing, setIsClosing] = useState(false);
  const dismissRef = useRef(onDismiss);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const openerRef = useRef(document.activeElement);

  useEffect(() => {
    const getDialog = () => document.querySelector<HTMLElement>(".date-picker__popover")
      ?? Array.from(document.querySelectorAll<HTMLElement>(".task-drawer[role='dialog']:not([inert])")).at(-1);
    const getControls = (dialog: HTMLElement) => Array.from(dialog.querySelectorAll<HTMLElement>(
      "button:not(:disabled), a[href], input:not(:disabled):not([type='hidden']), textarea:not(:disabled), select:not(:disabled), [tabindex='0']"
    )).filter((control) => control.tabIndex >= 0 && control.getClientRects().length > 0);
    const focusDialog = () => {
      const dialog = getDialog();
      if (dialog && !dialog.contains(document.activeElement)) getControls(dialog)[0]?.focus({ preventScroll: true });
    };
    const frame = requestAnimationFrame(focusDialog);
    function trapTab(event: KeyboardEvent) {
      if (event.key !== "Tab" || document.querySelector(".ui-combobox[data-open]")) return;
      const dialog = getDialog();
      if (!dialog) return;
      const controls = getControls(dialog);
      const first = controls[0];
      const last = controls.at(-1);
      if (!first || !last) return;
      if (!dialog.contains(document.activeElement) || (event.shiftKey ? document.activeElement === first : document.activeElement === last)) {
        event.preventDefault();
        (event.shiftKey ? last : first).focus();
      }
    }
    document.addEventListener("keydown", trapTab, true);
    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener("keydown", trapTab, true);
      const opener = openerRef.current;
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus({ preventScroll: true });
    };
  }, []);

  useEffect(() => { dismissRef.current = onDismiss; }, [onDismiss]);
  useEffect(() => () => {
    if (timerRef.current !== null) clearTimeout(timerRef.current);
  }, []);

  const onClose = useCallback(() => {
    if (timerRef.current !== null) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      dismissRef.current();
      return;
    }
    setIsClosing(true);
    timerRef.current = setTimeout(() => dismissRef.current(), 220);
  }, []);

  return { onClose, isClosing };
}

export function isComboboxHandlingEscape(event: KeyboardEvent): boolean {
  // Вложенный список или календарь получает первый Escape, сохраняя черновик панели.
  return event.key === "Escape" && document.querySelector(".ui-combobox[data-open], .date-picker__popover") !== null;
}
