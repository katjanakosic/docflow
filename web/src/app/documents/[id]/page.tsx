import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { DocumentView } from "@/components/document-view";
import type { components } from "@/lib/api-types";

type DocumentOut = components["schemas"]["DocumentOut"];

const API_URL = process.env.API_URL ?? "http://localhost:8000";

async function getDocument(id: string): Promise<DocumentOut> {
  const response = await fetch(`${API_URL}/api/v1/documents/${id}`);
  if (response.status === 404 || response.status === 422) {
    notFound();
  }
  if (!response.ok) {
    throw new Error(`The API answered with status ${response.status}`);
  }
  return response.json();
}

export default function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <main className="mx-auto max-w-6xl px-8 py-10">
      <Link href="/documents" className="text-sm text-muted hover:text-stamp hover:underline">
        Back to documents
      </Link>
      <Suspense fallback={<p className="mt-6 text-muted">Loading document…</p>}>
        <DocumentDetail params={params} />
      </Suspense>
    </main>
  );
}

async function DocumentDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const document = await getDocument(id);
  return <DocumentView initialDocument={document} />;
}