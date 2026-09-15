import { useCallback, useEffect, useRef, useState } from "react";

// Даём панели закончить анимацию перед размонтированием формы.
export function useTaskDrawerTransition(onDismiss: () => void) {
  const [isClosing, setIsClosing] = useState(false);
  const dismissRef = useRef(onDismiss);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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
  return event.key === "Escape" && document.querySelector(".ui-combobox[data-open]") !== null;
}
