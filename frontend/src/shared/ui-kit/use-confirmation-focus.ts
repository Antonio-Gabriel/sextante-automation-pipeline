import { useEffect, useRef, type KeyboardEvent } from "react";

/**
 * Focus for an inline confirmation (WAI-ARIA alertdialog): the safe choice gets focus
 * when it opens, Tab stays inside it, Escape cancels, and focus returns to the trigger
 * when it closes.
 *
 * Example:
 *   const focus = useConfirmationFocus(open, cancel);
 *   <div ref={focus.dialog} onKeyDown={focus.onKeyDown}>...</div>
 */
export function useConfirmationFocus(open: boolean, cancel: () => void) {
  const trigger = useRef<HTMLButtonElement>(null);
  const dialog = useRef<HTMLDivElement>(null);
  const safeChoice = useRef<HTMLButtonElement>(null);
  const wasOpen = useRef(false);

  useEffect(() => {
    if (open) safeChoice.current?.focus();
    else if (wasOpen.current) trigger.current?.focus();
    wasOpen.current = open;
  }, [open]);

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      cancel();
      return;
    }
    if (event.key !== "Tab" || dialog.current === null) return;
    const buttons = [...dialog.current.querySelectorAll<HTMLButtonElement>("button:not(:disabled)")];
    const first = buttons[0];
    const last = buttons.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
  };
  return { trigger, dialog, safeChoice, onKeyDown };
}
