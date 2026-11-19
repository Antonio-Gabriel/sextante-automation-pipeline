import { useId, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { Button } from "./button";
import type { useConfirmationFocus } from "./use-confirmation-focus";

interface ConfirmDialogProps {
  focus: ReturnType<typeof useConfirmationFocus>;
  icon: ReactNode;
  title: string;
  body: ReactNode;
  confirmLabel: string;
  pendingLabel: string;
  cancelLabel: string;
  pending: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * A modal confirmation of a destructive action (WAI-ARIA alertdialog), over a dimmed page.
 * Focus starts on Cancel and stays inside; Escape or a click outside cancels.
 *
 * Example:
 *   const focus = useConfirmationFocus(open, cancel);
 *   {open && <ConfirmDialog focus={focus} icon={<Trash2 />} title="Apagar?" ... />}
 */
export function ConfirmDialog(props: ConfirmDialogProps) {
  const { focus, pending, onCancel } = props;
  const titleId = useId();
  const bodyId = useId();
  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-[2px]"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !pending) onCancel();
      }}
    >
      <div
        ref={focus.dialog}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={bodyId}
        onKeyDown={focus.onKeyDown}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl ring-1 ring-slate-200"
      >
        <div className="flex gap-4">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-600 [&_svg]:size-5" aria-hidden>
            {props.icon}
          </span>
          <div className="flex flex-col gap-2">
            <h2 id={titleId} className="text-base font-semibold text-slate-900">{props.title}</h2>
            <div id={bodyId} className="text-sm leading-relaxed text-slate-600">{props.body}</div>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <Button ref={focus.safeChoice} variant="outline" disabled={pending} onClick={onCancel}>
            {props.cancelLabel}
          </Button>
          <Button variant="danger" disabled={pending} onClick={props.onConfirm}>
            {pending ? props.pendingLabel : props.confirmLabel}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
