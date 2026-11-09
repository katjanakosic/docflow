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
    <form onSubmit={handleSubmit} className="mb-8 flex items-center gap-3">
      <input type="file" name="file" accept="application/pdf" required className="text-sm" />
      <button
        type="submit"
        disabled={upload.isPending}
        className="rounded bg-blue-600 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {upload.isPending ? "Uploading…" : "Upload"}
      </button>
      {upload.isError && <p className="text-sm text-red-500">{upload.error.message}</p>}
      {upload.isSuccess && upload.data.duplicate && (
        <p className="text-sm text-gray-500">Already uploaded: showing the existing document.</p>
      )}
    </form>
  );
}