// Copied from shadcn/ui (MIT), adapted to this project's styles.
import type { HTMLAttributes } from "react";

import { cn } from "./cn";

type DivProps = HTMLAttributes<HTMLDivElement>;

export function Card({ className, ...props }: DivProps) {
  return <div className={cn("rounded-lg border border-slate-200 bg-white shadow-sm", className)} {...props} />;
}

export function CardHeader({ className, ...props }: DivProps) {
  return <div className={cn("flex flex-col gap-1.5 p-6", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h1 className={cn("text-lg font-semibold leading-none", className)} {...props} />;
}

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm text-slate-500", className)} {...props} />;
}

export function CardContent({ className, ...props }: DivProps) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}
