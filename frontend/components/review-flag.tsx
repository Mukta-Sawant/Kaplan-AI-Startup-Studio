"use client";

interface ReviewFlagProps {
  mentorReviewRequired: boolean;
  clarificationRequest?: string | null;
}

export function ReviewFlag({
  mentorReviewRequired,
  clarificationRequest,
}: ReviewFlagProps) {
  if (!mentorReviewRequired && !clarificationRequest) return null;

  return (
    <div className="space-y-3">
      {mentorReviewRequired && (
        <div className="bg-amber-50 border border-amber-300 rounded-xl px-5 py-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-amber-600 text-lg">⚠</span>
            <span className="font-semibold text-amber-800">
              Mentor Review Required
            </span>
          </div>
          <p className="text-sm text-amber-700">
            A significant divergence was detected between the EVAL and TEAM
            assessments. A human mentor must review this dossier before it is
            shared with the founder.
          </p>
        </div>
      )}

      {clarificationRequest && (
        <div className="bg-blue-50 border border-blue-300 rounded-xl px-5 py-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-blue-600 text-lg">?</span>
            <span className="font-semibold text-blue-800">
              Clarification Requested
            </span>
          </div>
          <p className="text-sm text-blue-700">{clarificationRequest}</p>
        </div>
      )}
    </div>
  );
}
