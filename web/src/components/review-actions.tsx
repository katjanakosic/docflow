"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { components } from "@/lib/api-types";

type DocumentOut = components["schemas"]["DocumentOut"];

const REASONS = [
  "Not a supplier invoice or purchase order",
  "Unreadable or incomplete",
  "Duplicate of another document",
  "Other",
];

async function post(url: string, body?: unknown): Promise<DocumentOut> {
  const response = await fetch(url, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await response.json();
  if (!response.ok) {
    throw new Error(typeof json.detail === "string" ? json.detail : "The request failed");
  }
  return json;
}

type Decision = { kind: "approve" } | { kind: "reject"; reason: string };

export function ReviewActions({ documentId }: { documentId: string }) {
  const queryClient = useQueryClient();
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState(REASONS[0]);
  const [note, setNote] = useState("");

  const review = useMutation({
    mutationFn: (decision: Decision) =>
      decision.kind === "approve"
        ? post(`/api/v1/documents/${documentId}/approve`)
        : post(`/api/v1/documents/${documentId}/reject`, { reason: decision.reason }),
    onSuccess: (document) => {
      queryClient.setQueryData(["document", documentId], document);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const trimmedNote = note.trim();
  const fullReason =
    reason === "Other" ? trimmedNote : trimmedNote ? `${reason}: ${trimmedNote}` : reason;

  return (
    <section className="mb-6 rounded-md border border-rule bg-sheet px-5 py-4">
      <p className="mb-3 text-sm text-muted">
        Check the extracted data against the PDF, then approve or reject it.
      </p>

      {!rejecting ? (
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => review.mutate({ kind: "approve" })}
            disabled={review.isPending}
            className="rounded bg-stamp px-4 py-1.5 text-sm font-medium text-white hover:bg-stamp/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stamp disabled:opacity-50"
          >
            {review.isPending ? "Saving…" : "Approve"}
          </button>
          <button
            type="button"
            onClick={() => setRejecting(true)}
            disabled={review.isPending}
            className="rounded border border-red-700/40 px-4 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700"
          >
            Reject
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <label className="block text-sm">
            <span className="text-muted">Reason</span>
            <select
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              className="mt-1 block w-full max-w-md rounded border border-rule bg-white px-2 py-1.5"
            >
              {REASONS.map((option) => (
                <option key={option}>{option}</option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="text-muted">
              {reason === "Other" ? "Describe the reason" : "Note (optional)"}
            </span>
            <textarea
              value={note}
              onChange={(event) => setNote(event.target.value)}
              rows={2}
              className="mt-1 block w-full max-w-md rounded border border-rule bg-white px-2 py-1.5"
            />
          </label>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => review.mutate({ kind: "reject", reason: fullReason })}
              disabled={review.isPending || !fullReason}
              className="rounded bg-red-700 px-4 py-1.5 text-sm font-medium text-white hover:bg-red-700/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700 disabled:opacity-50"
            >
              {review.isPending ? "Saving…" : "Reject document"}
            </button>
            <button
              type="button"
              onClick={() => setRejecting(false)}
              className="px-2 py-1.5 text-sm text-muted hover:text-ink"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {review.isError && <p className="mt-3 text-sm text-red-700">{review.error.message}</p>}
    </section>
  );
}