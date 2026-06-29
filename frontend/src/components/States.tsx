import { AlertCircle, Loader2, Search } from "lucide-react";
import type { ReactNode } from "react";

export function StatusBadge({
  tone,
  children
}: {
  tone: "passed" | "warning" | "failed" | "running" | "queued";
  children: ReactNode;
}) {
  return <span className={`status-pill status-${tone}`}>{children}</span>;
}

export function LoadingState({ label }: { label: string }) {
  return (
    <div className="state-panel">
      <Loader2 className="spin" size={20} aria-hidden="true" />
      <strong>{label}</strong>
      <span>Loading state primitive</span>
    </div>
  );
}

export function ErrorState({ title, message }: { title: string; message: string }) {
  return (
    <div className="state-panel">
      <AlertCircle size={20} aria-hidden="true" />
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="state-panel">
      <Search size={20} aria-hidden="true" />
      <strong>{title}</strong>
      <span>{message}</span>
    </div>
  );
}
