"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { components } from "@/lib/api-types";

type UploadOut = components["schemas"]["UploadOut"];

async function uploadFile(file: File): Promise<UploadOut> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch("/api/v1/documents", { method: "POST", body });
  const json = await response.json();
  if (!response.ok) {
    throw new Error(typeof json.detail === "string" ? json.detail : "Upload failed");
  }
  return json;
}

export function UploadForm() {
  const queryClient = useQueryClient();
  const upload = useMutation({
    mutationFn: uploadFile,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const file = new FormData(event.currentTarget).get("file");
    if (file instanceof File && file.size > 0) {
      upload.mutate(file);
    }
    event.currentTarget.reset();
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-8 rounded-md border border-rule bg-sheet px-5 py-4"
    >
      <p className="mb-3 text-sm text-muted">
        Add a supplier invoice or purchase order as a PDF, up to 20 MB.
      </p>
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="file"
          name="file"
          accept="application/pdf"
          required
          className="text-sm text-muted file:mr-3 file:rounded file:border file:border-rule file:bg-paper file:px-3 file:py-1.5 file:text-sm file:text-ink hover:file:bg-white"
        />
        <button
          type="submit"
          disabled={upload.isPending}
          className="rounded bg-stamp px-4 py-1.5 text-sm font-medium text-white hover:bg-stamp/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stamp disabled:opacity-50"
        >
          {upload.isPending ? "Uploading…" : "Upload PDF"}
        </button>
        {upload.isError && <p className="text-sm text-red-700">{upload.error.message}</p>}
        {upload.isSuccess && upload.data.duplicate && (
          <p className="text-sm text-muted">This file is already in DocFlow.</p>
        )}
      </div>
    </form>
  );
}