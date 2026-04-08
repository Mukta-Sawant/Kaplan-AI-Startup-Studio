"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getDossier, submitFeedback } from "@/lib/api";
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

  useEffect(() => {
    getDossier(submissionId)
      .then(setDossier)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [submissionId]);

  async function handleFeedback(e: React.FormEvent) {
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
      </div>

      <DossierCard dossier={dossier} />

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
