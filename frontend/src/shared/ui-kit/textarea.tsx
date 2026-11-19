// Copied from shadcn/ui (MIT), adapted to the AMT palette.
import { forwardRef, type TextareaHTMLAttributes } from "react";

import { cn } from "./cn";

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;

/**
 * A multi-line text field, styled like the other fields.
 *
 * Example:
 *   <Textarea id="note" rows={3} {...form.register("note")} />
 */
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-xs placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 aria-invalid:border-red-600",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
