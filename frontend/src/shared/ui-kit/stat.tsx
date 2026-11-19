import type { ReactNode } from "react";

import { cn } from "./cn";

interface StatProps {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  className?: string;
}

/** One figure with its label, as in a row of tiles. */
export function Stat({ label, value, icon, className }: StatProps) {
  return (
    <div className={cn("flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-4", className)}>
      <div className="flex items-center gap-2 text-sm text-slate-500 [&_svg]:size-4">
        {icon}
        <span>{label}</span>
      </div>
      <p className="text-2xl font-semibold tabular-nums text-slate-900">{value}</p>
    </div>
  );
}
