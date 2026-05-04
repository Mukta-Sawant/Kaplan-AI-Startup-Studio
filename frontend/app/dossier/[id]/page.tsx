"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getDossier, runPhase1, runPhase2, submitFeedback } from "@/lib/api";
import type { Dossier, FeedbackSource, RerunScope } from "@/lib/types";
import { DossierCard } from "@/components/dossier-card";
import { Spinner } from "@/components/ui/spinner";
import { Alert } from "@/components/ui/alert";

export default function DossierPage() {
  const params = useParams();
  const submissionId = params.id as string;

  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Feedback form
  const [feedbackText, setFeedbackText] = useState("");
  const [sourceType, setSourceType] = useState<FeedbackSource>("mentor");
  const [triggersRerun, setTriggersRerun] = useState(false);
  const [rerunScope, setRerunScope] = useState<RerunScope>("phase1");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);

  // Phase 1 rerun
  const [runningRerun, setRunningRerun] = useState(false);
  const [rerunError, setRerunError] = useState<string | null>(null);
  const [rerunDone, setRerunDone] = useState(false);

  // Phase 2
  const [runningPhase2, setRunningPhase2] = useState(false);
  const [phase2Error, setPhase2Error] = useState<string | null>(null);
  const [phase2Done, setPhase2Done] = useState(false);

  useEffect(() => {
    getDossier(submissionId)
      .then(setDossier)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [submissionId]);

  async function handleRerunPhase1() {
    setRunningRerun(true);
    setRerunError(null);
    setRerunDone(false);
    try {
      await runPhase1(submissionId);
      const updated = await getDossier(submissionId);
      setDossier(updated);
      setRerunDone(true);
    } catch (e) {
      setRerunError(e instanceof Error ? e.message : "Phase 1 rerun failed.");
    } finally {
      setRunningRerun(false);
    }
  }

  async function handleRunPhase2() {
    setRunningPhase2(true);
    setPhase2Error(null);
    try {
      await runPhase2(submissionId);
      setPhase2Done(true);
    } catch (e) {
      setPhase2Error(e instanceof Error ? e.message : "Phase 2 run failed.");
    } finally {
      setRunningPhase2(false);
    }
  }

  async function handleFeedback(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!feedbackText.trim()) return;

    setSubmittingFeedback(true);
    setFeedbackError(null);
    try {
      await submitFeedback({
        submission_id: submissionId,
        source_type: sourceType,
        feedback_text: feedbackText,
        triggers_rerun: triggersRerun,
        rerun_scope: triggersRerun ? rerunScope : undefined,
      });
      setFeedbackSuccess(true);
      setFeedbackText("");
    } catch (e) {
      setFeedbackError(e instanceof Error ? e.message : "Feedback submission failed.");
    } finally {
      setSubmittingFeedback(false);
    }
  }

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
        <div className="mt-4">
          <Link href="/dashboard" className="text-brand-600 text-sm underline">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  if (!dossier) return null;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/dashboard" className="text-sm text-gray-500 hover:text-gray-700">
            ← Dashboard
          </Link>
          <h1 className="text-2xl font-bold mt-1">Qualification Dossier</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Submission {submissionId}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {rerunError && <p className="text-xs text-red-600">{rerunError}</p>}
          {rerunDone && <p className="text-xs text-green-600">Rerun complete — dossier updated.</p>}
          <button
            onClick={handleRerunPhase1}
            disabled={runningRerun}
            className="flex items-center gap-2 text-sm border border-brand-400 text-brand-600 px-4 py-2 rounded-lg hover:bg-brand-50 disabled:opacity-60 transition-colors"
          >
            {runningRerun && <Spinner className="text-brand-500 h-4 w-4" />}
            {runningRerun ? "Rerunning Phase 1…" : "↺ Rerun Phase 1"}
          </button>
        </div>
      </div>

      <DossierCard dossier={dossier} />

      {/* Phase 2 launch */}
      <div className="mt-8 bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-1">Stage One Analysis — Phase 2</h2>
        <p className="text-sm text-gray-500 mb-4">
          Run 6 parallel agents: market discovery, competitive intelligence, risk register, go-to-market strategy, and financial model.
        </p>

        {phase2Error && <Alert variant="error" className="mb-3">{phase2Error}</Alert>}

        {phase2Done ? (
          <div className="flex items-center gap-4">
            <Alert variant="success">Phase 2 complete.</Alert>
            <Link
              href={`/phase2/${submissionId}`}
              className="text-sm bg-purple-600 text-white px-5 py-2 rounded-lg hover:bg-purple-700 transition-colors"
            >
              View Phase 2 Results →
            </Link>
          </div>
        ) : (
          <button
            onClick={handleRunPhase2}
            disabled={runningPhase2}
            className="flex items-center gap-2 bg-purple-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-60 transition-colors"
          >
            {runningPhase2 && <Spinner className="text-white h-4 w-4" />}
            {runningPhase2 ? "Running Phase 2 (5 agents in parallel)…" : "Run Phase 2"}
          </button>
        )}
      </div>

      {/* Feedback form */}
      <div className="mt-10 bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">Submit Feedback</h2>

        {feedbackSuccess && (
          <Alert variant="success">
            Feedback submitted successfully.{" "}
            {triggersRerun && "A rerun has been triggered."}
          </Alert>
        )}

        {feedbackError && <Alert variant="error">{feedbackError}</Alert>}

        <form onSubmit={handleFeedback} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Feedback Role
            </label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value as FeedbackSource)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
            >
              <option value="mentor">Mentor</option>
              <option value="founder">Founder</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Feedback
            </label>
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="Share your observations or concerns about this assessment..."
              rows={4}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm resize-y focus:ring-2 focus:ring-brand-500 focus:outline-none"
            />
          </div>

          <div className="flex items-start gap-3">
            <input
              type="checkbox"
              id="rerun"
              checked={triggersRerun}
              onChange={(e) => setTriggersRerun(e.target.checked)}
              className="mt-0.5"
            />
            <label htmlFor="rerun" className="text-sm text-gray-700">
              Trigger agent rerun
            </label>
          </div>

          {triggersRerun && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rerun Scope
              </label>
              <select
                value={rerunScope}
                onChange={(e) => setRerunScope(e.target.value as RerunScope)}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:outline-none"
              >
                <option value="phase1">Full Phase 1</option>
                <option value="eval">EVAL Agent only</option>
                <option value="team">TEAM Agent only</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={submittingFeedback || !feedbackText.trim()}
            className="flex items-center gap-2 bg-brand-500 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-brand-600 disabled:opacity-60 transition-colors"
          >
            {submittingFeedback && <Spinner className="text-white h-4 w-4" />}
            Submit Feedback
          </button>
        </form>
      </div>
    </div>
  );
}
