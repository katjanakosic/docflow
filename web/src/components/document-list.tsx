"use client";

import { useQuery } from "@tanstack/react-query";

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

export function DocumentList({ initialDocuments }: { initialDocuments: DocumentOut[] }) {
  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: fetchDocuments,
    initialData: initialDocuments,
    // Ask again every 2 seconds while any document is still being processed.
    refetchInterval: (query) =>
      query.state.data?.some((d) => IN_PROGRESS.includes(d.status)) ? 2000 : false,
  });

  if (documents.length === 0) {
    return <p className="text-gray-500">No documents yet.</p>;
  }

  return (
    <table className="w-full text-left text-sm [&_td]:px-3 [&_th]:px-3">
      <thead>
        <tr className="border-b text-gray-500">
          <th className="py-2">File</th>
          <th>Status</th>
          <th>Supplier</th>
          <th className="text-right">Total</th>
          <th>Uploaded</th>
        </tr>
      </thead>
      <tbody>
        {documents.map((document) => (
          <tr key={document.id} className="border-b">
            <td className="py-2">{document.file_name}</td>
            <td>
              <StatusBadge status={document.status} />
            </td>
            <td>{document.extracted_data?.supplier_name ?? "–"}</td>
            <td className="text-right">
              {document.extracted_data
                ? `${document.extracted_data.currency} ${document.extracted_data.total}`
                : "–"}
            </td>
            <td>
              {new Date(document.created_at).toLocaleString("de-CH", {
                timeZone: "Europe/Zurich",
              })}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}