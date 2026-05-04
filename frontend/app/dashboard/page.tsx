"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { listSubmissions, runPhase1, runPhase2, runPhase3, runPhase4 } from "@/lib/api";
import type { SubmissionListItem } from "@/lib/types";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";

const STATUS_STYLES: Record<string, string> = {
  submitted: "bg-gray-100 text-gray-700",
  clarification_needed: "bg-blue-100 text-blue-700",
  phase1_complete: "bg-green-100 text-green-700",
  mentor_review_required: "bg-amber-100 text-amber-700",
  phase2_complete: "bg-purple-100 text-purple-700",
  phase3_complete: "bg-orange-100 text-orange-700",
  phase4_complete: "bg-indigo-100 text-indigo-700",
};

const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  clarification_needed: "Clarification Needed",
  phase1_complete: "Phase 1 Complete",
  mentor_review_required: "Mentor Review Required",
  phase2_complete: "Phase 2 Complete",
  phase3_complete: "Phase 3 Complete",
  phase4_complete: "Phase 4 Complete",
};

function DashboardContent() {
  const searchParams = useSearchParams();
  const highlight = searchParams.get("highlight");

  const [submissions, setSubmissions] = useState<SubmissionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState<string | null>(null);
  const [runningPhase, setRunningPhase] = useState<"phase1" | "phase2" | "phase3" | "phase4" | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    listSubmissions()
      .then(setSubmissions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleRunPhase1(submissionId: string) {
    setRunning(submissionId);
    setRunningPhase("phase1");
    setRunError(null);
    try {
      await runPhase1(submissionId);
      const updated = await listSubmissions();
      setSubmissions(updated);
    } catch (e) {
      setRunError(e instanceof Error ? e.message : "Phase 1 run failed.");
    } finally {
      setRunning(null);
      setRunningPhase(null);
    }
  }

  async function handleRunPhase2(submissionId: string) {
    setRunning(submissionId);
    setRunningPhase("phase2");
    setRunError(null);
    try {
      await runPhase2(submissionId);
      const updated = await listSubmissions();
      setSubmissions(updated);
    } catch (e) {
      setRunError(e instanceof Error ? e.message : "Phase 2 run failed.");
    } finally {
      setRunning(null);
      setRunningPhase(null);
    }
  }

  async function handleRunPhase3(submissionId: string) {
    setRunning(submissionId);
    setRunningPhase("phase3");
    setRunError(null);
    try {
      await runPhase3(submissionId);
      const updated = await listSubmissions();
      setSubmissions(updated);
    } catch (e) {
      setRunError(e instanceof Error ? e.message : "Phase 3 run failed.");
    } finally {
      setRunning(null);
      setRunningPhase(null);
    }
  }

  async function handleRunPhase4(submissionId: string) {
    setRunning(submissionId);
    setRunningPhase("phase4");
    setRunError(null);
    try {
      await runPhase4(submissionId);
      const updated = await listSubmissions();
      setSubmissions(updated);
    } catch (e) {
      setRunError(e instanceof Error ? e.message : "Phase 4 run failed.");
    } finally {
      setRunning(null);
      setRunningPhase(null);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner className="text-brand-500 h-8 w-8" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <Link
          href="/submit"
          className="bg-brand-500 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-brand-600 transition-colors"
        >
          + New Submission
        </Link>
      </div>

      {error && <Alert variant="error">{error}</Alert>}
      {runError && <Alert variant="error" className="mb-4">{runError}</Alert>}

      {submissions.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg mb-4">No submissions yet.</p>
          <Link href="/submit" className="text-brand-500 underline">
            Submit your first startup
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {submissions.map((sub) => (
            <div
              key={sub.id}
              className={`bg-white border rounded-2xl p-5 shadow-sm transition-all ${
                highlight === sub.id ? "ring-2 ring-brand-500" : "border-gray-200"
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-lg">{sub.startup_name}</h3>
                  <p className="text-gray-500 text-sm mt-0.5">{sub.one_line_pitch}</p>
                  <div className="flex items-center gap-3 mt-2">
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full capitalize">
                      {sub.stage}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        STATUS_STYLES[sub.status] ?? "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {STATUS_LABELS[sub.status] ?? sub.status}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(sub.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="flex gap-2 flex-shrink-0 flex-wrap justify-end">
                  {sub.status === "submitted" && (
                    <button
                      onClick={() => handleRunPhase1(sub.id)}
                      disabled={running === sub.id}
                      className="flex items-center gap-1.5 text-sm bg-brand-500 text-white px-4 py-2 rounded-lg hover:bg-brand-600 disabled:opacity-60 transition-colors"
                    >
                      {running === sub.id && runningPhase === "phase1" ? (
                        <><Spinner className="text-white h-4 w-4" />Running P1...</>
                      ) : "Run Phase 1"}
                    </button>
                  )}

                  {(sub.status === "phase1_complete" ||
                    sub.status === "mentor_review_required" ||
                    sub.status === "clarification_needed") && (
                    <>
                      <Link
                        href={`/dossier/${sub.id}`}
                        className="text-sm border border-brand-500 text-brand-600 px-4 py-2 rounded-lg hover:bg-brand-50 transition-colors"
                      >
                        View Dossier
                      </Link>
                      <button
                        onClick={() => handleRunPhase2(sub.id)}
                        disabled={running === sub.id}
                        className="flex items-center gap-1.5 text-sm bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-60 transition-colors"
                      >
                        {running === sub.id && runningPhase === "phase2" ? (
                          <><Spinner className="text-white h-4 w-4" />Running P2...</>
                        ) : "Run Phase 2"}
                      </button>
                    </>
                  )}

                  {sub.status === "phase2_complete" && (
                    <>
                      <Link
                        href={`/phase2/${sub.id}`}
                        className="text-sm border border-gray-300 text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        View Phase 2
                      </Link>
                      <button
                        onClick={() => handleRunPhase3(sub.id)}
                        disabled={running === sub.id}
                        className="flex items-center gap-1.5 text-sm bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 disabled:opacity-60 transition-colors"
                      >
                        {running === sub.id && runningPhase === "phase3" ? (
                          <><Spinner className="text-white h-4 w-4" />Running P3...</>
                        ) : "Run Phase 3"}
                      </button>
                    </>
                  )}

                  {sub.status === "phase3_complete" && (
                    <>
                      <Link
                        href={`/phase3/${sub.id}`}
                        className="text-sm border border-orange-400 text-orange-600 px-4 py-2 rounded-lg hover:bg-orange-50 transition-colors"
                      >
                        View Phase 3
                      </Link>
                      <button
                        onClick={() => handleRunPhase4(sub.id)}
                        disabled={running === sub.id}
                        className="flex items-center gap-1.5 text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-60 transition-colors"
                      >
                        {running === sub.id && runningPhase === "phase4" ? (
                          <><Spinner className="text-white h-4 w-4" />Running P4...</>
                        ) : "Run Phase 4"}
                      </button>
                    </>
                  )}

                  {sub.status === "phase4_complete" && (
                    <>
                      <Link
                        href={`/phase3/${sub.id}`}
                        className="text-sm border border-gray-300 text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        Phase 3
                      </Link>
                      <Link
                        href={`/phase4/${sub.id}`}
                        className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                      >
                        View Phase 4
                      </Link>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DashboardFallback() {
  return (
    <div className="flex justify-center py-20">
      <Spinner className="text-brand-500 h-8 w-8" />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardFallback />}>
      <DashboardContent />
    </Suspense>
  );
}
