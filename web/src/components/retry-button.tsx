"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { components } from "@/lib/api-types";

type DocumentOut = components["schemas"]["DocumentOut"];

async function retry(documentId: string): Promise<DocumentOut> {
  const response = await fetch(`/api/v1/documents/${documentId}/retry`, { method: "POST" });
  const json = await response.json();
  if (!response.ok) {
    throw new Error(typeof json.detail === "string" ? json.detail : "The retry failed");
  }
  return json;
}

export function RetryButton({ documentId }: { documentId: string }) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => retry(documentId),
    onSuccess: (document) => {
      queryClient.setQueryData(["document", documentId], document);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  return (
    <div className="mt-3 flex items-center gap-3">
      <button
        type="button"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="rounded border border-red-700/40 bg-white px-3 py-1.5 text-sm font-medium text-red-800 hover:bg-red-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700 disabled:opacity-50"
      >
        {mutation.isPending ? "Retrying…" : "Retry extraction"}
      </button>
      {mutation.isError && <p className="text-sm">{mutation.error.message}</p>}
    </div>
  );
}