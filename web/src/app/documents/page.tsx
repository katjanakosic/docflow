import { Suspense } from "react";

import { StatusBadge } from "@/components/status-badge";
import type { components } from "@/lib/api-types";

type DocumentOut = components["schemas"]["DocumentOut"];

const API_URL = process.env.API_URL ?? "http://localhost:8000";

async function getDocuments(): Promise<DocumentOut[]> {
  const response = await fetch(`${API_URL}/api/v1/documents`);
  if (!response.ok) {
    throw new Error(`The API answered with status ${response.status}`);
  }
  return response.json();
}

export default function DocumentsPage() {
  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="mb-6 text-2xl font-semibold">Documents</h1>
      <Suspense fallback={<p className="text-gray-500">Loading documents…</p>}>
        <DocumentTable />
      </Suspense>
    </main>
  );
}

async function DocumentTable() {
  const documents = await getDocuments();

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
          <th className="pl-6">Uploaded</th>
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
            <td className="pl-6">{new Date(document.created_at).toLocaleString("de-CH")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}