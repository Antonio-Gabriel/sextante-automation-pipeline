import type { ReactNode } from "react";

interface PageProps {
  title: string;
  description?: string;
  breadcrumb?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}

/** A page of the panel: header with trail, title and actions, then the content. */
export function Page({ title, description, breadcrumb, actions, children }: PageProps) {
  return (
    <main className="flex flex-col">
      <header className="flex min-h-16 flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white px-8 py-3">
        <div className="flex flex-col gap-0.5">
          {breadcrumb}
          <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
          {description !== undefined && <p className="text-sm text-slate-500">{description}</p>}
        </div>
        {actions !== undefined && <div className="flex items-center gap-2">{actions}</div>}
      </header>
      <div className="flex flex-col gap-6 p-8">{children}</div>
    </main>
  );
}
