"use client";

import { useQuery } from "@tanstack/react-query";

import { ReviewActions } from "@/components/review-actions";
import { StatusBadge } from "@/components/status-badge";
import type { components } from "@/lib/api-types";
import { formatDate, formatDateTime, formatMoney } from "@/lib/format";

type DocumentOut = components["schemas"]["DocumentOut"];
type ExtractedData = NonNullable<DocumentOut["extracted_data"]>;

const LOW_CONFIDENCE = 0.8;

async function fetchDocument(id: string): Promise<DocumentOut> {
  const response = await fetch(`/api/v1/documents/${id}`);
  if (!response.ok) {
    throw new Error(`The API answered with status ${response.status}`);
  }
  return response.json();
}

function isInProgress(document: DocumentOut | undefined): boolean {
  return document?.status === "uploaded" || document?.status === "extracting";
}

export function DocumentView({ initialDocument }: { initialDocument: DocumentOut }) {
  const { data: document } = useQuery({
    queryKey: ["document", initialDocument.id],
    queryFn: () => fetchDocument(initialDocument.id),
    initialData: initialDocument,
    refetchInterval: (query) => (isInProgress(query.state.data) ? 2000 : false),
  });

  return (
    <article className="mt-4">
      <header className="mb-8">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-3xl font-bold tracking-tight break-all">{document.file_name}</h1>
          <StatusBadge status={document.status} />
        </div>
        <p className="mt-1 text-sm text-muted">Uploaded {formatDateTime(document.created_at)}</p>
      </header>

      {isInProgress(document) && (
        <p className="rounded-md border border-rule bg-sheet px-5 py-4 text-sm text-muted">
          Reading the document. This page updates by itself when the data is ready.
        </p>
      )}

      {document.status === "extraction_failed" && (
        <div className="rounded-md border border-red-700/30 bg-red-50 px-5 py-4 text-sm text-red-800">
          <p className="font-medium">The data couldn’t be read from this PDF.</p>
          <p className="mt-1">{document.last_error}</p>
        </div>
      )}

      {document.status === "needs_review" && <ReviewActions documentId={document.id} />}

      {document.status === "approved" && document.reviewed_at && (
        <p className="mb-6 rounded-md border border-green-700/30 bg-green-50 px-5 py-4 text-sm text-green-900">
          Approved by {document.reviewed_by} on {formatDateTime(document.reviewed_at)}.
        </p>
      )}

      {document.status === "rejected" && document.reviewed_at && (
        <div className="mb-6 rounded-md border border-red-700/30 bg-red-50 px-5 py-4 text-sm text-red-800">
          <p className="font-medium">
            Rejected by {document.reviewed_by} on {formatDateTime(document.reviewed_at)}.
          </p>
          <p className="mt-1">{document.rejection_reason}</p>
        </div>
      )}

      {document.extracted_data && <ExtractedView data={document.extracted_data} />}
    </article>
  );
}

function ExtractedView({ data }: { data: ExtractedData }) {
  const confidence = data.confidence ?? {};
  const hasLowConfidence = Object.values(confidence).some((value) => value < LOW_CONFIDENCE);

  const facts: [string, string, string | null | undefined][] = [
    ["Type", "doc_type", data.doc_type === "invoice" ? "Invoice" : "Purchase order"],
    ["Supplier", "supplier_name", data.supplier_name],
    ["VAT number", "supplier_vat_id", data.supplier_vat_id],
    ["Document number", "document_number", data.document_number],
    ["Issue date", "issue_date", formatDate(data.issue_date)],
    ["Due date", "due_date", data.due_date ? formatDate(data.due_date) : null],
    ["PO reference", "po_reference", data.po_reference],
    ["Currency", "currency", data.currency],
  ];

  return (
    <>
      {hasLowConfidence && (
        <p className="mb-4 text-sm text-muted">
          <span className="rounded-sm bg-amber-100 px-1 text-amber-900">Highlighted</span> values
          are ones the AI was less sure about. Check them against the PDF.
        </p>
      )}
      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <section className="rounded-md border border-rule bg-sheet p-5">
          <h2 className="mb-4 font-semibold">Document</h2>
          <dl className="space-y-3 text-sm">
            {facts
              .filter(([, , value]) => value)
              .map(([label, field, value]) => (
                <div key={field}>
                  <dt className="text-muted">{label}</dt>
                  <dd className="font-medium">
                    <Checked confidence={confidence[field]}>{value}</Checked>
                  </dd>
                </div>
              ))}
          </dl>
        </section>

        <section className="rounded-md border border-rule bg-sheet p-5">
          <h2 className="mb-4 font-semibold">Line items</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-muted">
                  <th className="pb-2 text-left font-medium">Description</th>
                  <th className="pb-2 text-right font-medium">Qty</th>
                  <th className="pb-2 text-right font-medium">Unit price</th>
                  <th className="pb-2 text-right font-medium">Amount</th>
                </tr>
              </thead>
              <tbody>
                {data.line_items.map((item, index) => (
                  <tr key={index} className="border-t border-rule">
                    <td className="py-2 pr-4">{item.description}</td>
                    <td className="py-2 text-right tabular-nums">{item.quantity}</td>
                    <td className="py-2 text-right tabular-nums">{formatMoney(item.unit_price)}</td>
                    <td className="py-2 text-right tabular-nums">{formatMoney(item.line_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <dl className="mt-6 ml-auto w-full max-w-xs text-sm tabular-nums">
            <div className="flex justify-between py-1">
              <dt className="text-muted">Subtotal</dt>
              <dd>
                <Checked confidence={confidence.subtotal}>{formatMoney(data.subtotal)}</Checked>
              </dd>
            </div>
            <div className="flex justify-between py-1">
              <dt className="text-muted">VAT</dt>
              <dd>
                <Checked confidence={confidence.vat_amount}>{formatMoney(data.vat_amount)}</Checked>
              </dd>
            </div>
            <div className="mt-1 flex justify-between border-t border-b-[3px] border-ink border-b-double pt-2 pb-1.5 text-base font-bold">
              <dt>Total</dt>
              <dd>
                <Checked confidence={confidence.total}>
                  {data.currency} {formatMoney(data.total)}
                </Checked>
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </>
  );
}

function Checked({ confidence, children }: { confidence?: number; children: React.ReactNode }) {
  if (confidence === undefined || confidence >= LOW_CONFIDENCE) {
    return <>{children}</>;
  }
  return (
    <span
      className="rounded-sm bg-amber-100 px-1 text-amber-900"
      title={`The AI is ${Math.round(confidence * 100)}% sure about this value.`}
    >
      {children}
    </span>
  );
}