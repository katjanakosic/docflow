import type { components } from "@/lib/api-types";

type Status = components["schemas"]["Status"];

const LABELS: Record<Status, string> = {
  uploaded: "Queued",
  extracting: "Reading",
  needs_review: "Needs review",
  approved: "Approved",
  exported: "Exported",
  rejected: "Rejected",
  extraction_failed: "Extraction failed",
  export_failed: "Export failed",
};

const STYLES: Record<Status, string> = {
  uploaded: "border-muted/40 text-muted",
  extracting: "border-stamp/40 text-stamp",
  needs_review: "border-amber-600/50 bg-amber-50 text-amber-800",
  approved: "border-green-700/40 bg-green-50 text-green-800",
  exported: "border-green-700/40 bg-green-50 text-green-800",
  rejected: "border-red-700/40 bg-red-50 text-red-700",
  extraction_failed: "border-red-700/40 bg-red-50 text-red-700",
  export_failed: "border-red-700/40 bg-red-50 text-red-700",
};

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-xs font-medium whitespace-nowrap ${STYLES[status]}`}
    >
      {status === "extracting" && (
        <span className="size-1.5 rounded-full bg-current motion-safe:animate-pulse" />
      )}
      {LABELS[status]}
    </span>
  );
}