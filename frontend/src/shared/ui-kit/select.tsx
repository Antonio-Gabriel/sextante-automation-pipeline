import { forwardRef, type SelectHTMLAttributes } from "react";

import { cn } from "./cn";

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement>;

/**
 * The native select, styled like the other fields: accessible by keyboard and reader.
 *
 * Example:
 *   <Select value={value} onChange={...}><option value="">...</option></Select>
 */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(({ className, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      "h-9 rounded-lg border border-slate-200 bg-white px-3 pr-8 text-sm text-slate-700 shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400",
      className,
    )}
    {...props}
  />
));
Select.displayName = "Select";
