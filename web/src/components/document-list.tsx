"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { StatusBadge } from "@/components/status-badge";
import type { components } from "@/lib/api-types";

type DocumentOut = components["schemas"]["DocumentOut"];

const IN_PROGRESS: DocumentOut["status"][] = ["uploaded", "extracting"];

async function fetchDocuments(): Promise<DocumentOut[]> {
  const response = await fetch("/api/v1/documents");
  if (!response.ok) {
    throw new Error(`The API answered with status ${response.status}`);
  }
  return response.json();
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString("de-CH", {
    timeZone: "Europe/Zurich",
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function DocumentList({ initialDocuments }: { initialDocuments: DocumentOut[] }) {
  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: fetchDocuments,
    initialData: initialDocuments,
    refetchInterval: (query) =>
      query.state.data?.some((d) => IN_PROGRESS.includes(d.status)) ? 2000 : false,
  });

  if (documents.length === 0) {
    return (
      <p className="rounded-md border border-dashed border-rule px-5 py-10 text-center text-muted">
        No documents yet. Upload a PDF above to get started.
      </p>
    );
  }

  const waiting = documents.filter((d) => d.status === "needs_review").length;
  const failed = documents.filter((d) => d.status === "extraction_failed").length;

  return (
    <section>
      <p className="mb-3 text-sm text-muted">
        {waiting} waiting for review{failed > 0 && `, ${failed} failed`}
      </p>
      <div className="overflow-x-auto rounded-md border border-rule bg-sheet">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-xs text-muted">
              <th className="px-4 py-2.5 font-medium">File</th>
              <th className="px-4 py-2.5 font-medium">Status</th>
              <th className="px-4 py-2.5 font-medium">Supplier</th>
              <th className="px-4 py-2.5 text-right font-medium">Total</th>
              <th className="px-4 py-2.5 font-medium">Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id} className="border-t border-rule hover:bg-paper">
                <td className="px-4 py-3">
                  <Link
                    href={`/documents/${document.id}`}
                    className="font-medium hover:text-stamp hover:underline"
                  >
                    {document.file_name}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={document.status} />
                </td>
                <td className="px-4 py-3">{document.extracted_data?.supplier_name ?? "–"}</td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {document.extracted_data
                    ? `${document.extracted_data.currency} ${document.extracted_data.total}`
                    : "–"}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-muted">
                  {formatDate(document.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}