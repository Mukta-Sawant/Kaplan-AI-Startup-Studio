"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getPhase2Output } from "@/lib/api";
import type { Phase2Output } from "@/lib/types";
import { Phase2Card } from "@/components/phase2-card";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";

export default function Phase2Page() {
  const params = useParams();
  const submissionId = params.id as string;

  const [output, setOutput] = useState<Phase2Output | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPhase2Output(submissionId)
      .then(setOutput)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [submissionId]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="text-brand-500 h-8 w-8" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-12">
        <Alert variant="error">{error}</Alert>
        <div className="mt-4 flex gap-4">
          <Link href="/dashboard" className="text-brand-600 text-sm underline">
            Back to Dashboard
          </Link>
          <Link href={`/dossier/${submissionId}`} className="text-brand-600 text-sm underline">
            View Phase 1 Dossier
          </Link>
        </div>
      </div>
    );
  }

  if (!output) return null;

  const failedCount = Object.values(output.agent_statuses ?? {}).filter(s => s === "failed").length;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
            ← Dashboard
          </Link>
          <h1 className="text-2xl font-bold mt-1">Phase 2 — Stage One Analysis</h1>
          <p className="text-xs text-gray-400 mt-0.5">Submission {submissionId}</p>
        </div>
        <Link
          href={`/dossier/${submissionId}`}
          className="text-sm border border-gray-300 text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          View Phase 1 Dossier
        </Link>
      </div>

      {failedCount > 0 && (
        <Alert variant="error" className="mb-6">
          {failedCount} agent{failedCount > 1 ? "s" : ""} failed during this run.
          Fallback data is shown. You can re-run Phase 2 from the dashboard.
        </Alert>
      )}

      {/* Agent status bar */}
      <div className="bg-white border border-gray-200 rounded-2xl p-4 mb-8 shadow-sm">
        <p className="text-xs font-medium text-gray-500 mb-3 uppercase tracking-wide">Agent Status</p>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {(["interact", "discovery", "comp", "risk", "gtm", "fin"] as const).map((agent) => {
            const s = (output.agent_statuses ?? {})[agent];
            return (
              <div key={agent} className={`rounded-xl px-3 py-2 text-center text-xs font-medium ${
                s === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
              }`}>
                {agent.toUpperCase()}
                <br />
                <span className="font-normal">{s ?? "—"}</span>
              </div>
            );
          })}
        </div>
      </div>

      <Phase2Card output={output} />
    </div>
  );
}
