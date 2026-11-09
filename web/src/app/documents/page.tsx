import { Suspense } from "react";

import { DocumentList } from "@/components/document-list";
import { UploadForm } from "@/components/upload-form";
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
      <main className="mx-auto max-w-6xl px-8 py-10">
        <h1 className="mb-6 text-3xl font-bold tracking-tight">Documents</h1>
        <UploadForm />
        <Suspense fallback={<p className="text-muted">Loading documents…</p>}>
          <InitialDocuments />
        </Suspense>
      </main>
    );
  }

async function InitialDocuments() {
  const documents = await getDocuments();
  return <DocumentList initialDocuments={documents} />;
}