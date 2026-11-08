import type { components } from "@/lib/api-types";

type Status = components["schemas"]["Status"];

const STYLES: Record<Status, string> = {
  uploaded: "bg-gray-100 text-gray-700",
  extracting: "bg-blue-100 text-blue-700",
  needs_review: "bg-amber-100 text-amber-800",
  approved: "bg-green-100 text-green-800",
  exported: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-700",
  extraction_failed: "bg-red-100 text-red-700",
  export_failed: "bg-red-100 text-red-700",
};

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}>
      {status.replace("_", " ")}
    </span>
  );
}