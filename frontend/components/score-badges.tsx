"use client";

interface ScoreBadgeProps {
  label: string;
  score: number;
  max?: number;
}

function getScoreColor(score: number, max: number): string {
  const pct = score / max;
  if (pct >= 0.75) return "bg-green-100 text-green-800 border-green-300";
  if (pct >= 0.5) return "bg-yellow-100 text-yellow-800 border-yellow-300";
  return "bg-red-100 text-red-800 border-red-300";
}

export function ScoreBadge({ label, score, max = 10 }: ScoreBadgeProps) {
  return (
    <div
      className={`flex flex-col items-center px-4 py-3 rounded-xl border ${getScoreColor(
        score,
        max
      )}`}
    >
      <span className="text-2xl font-bold">
        {score}
        <span className="text-sm font-normal">/{max}</span>
      </span>
      <span className="text-xs mt-1 font-medium">{label}</span>
    </div>
  );
}

interface EvalScoreBadgesProps {
  market: number;
  feasibility: number;
  scalability: number;
}

export function EvalScoreBadges({
  market,
  feasibility,
  scalability,
}: EvalScoreBadgesProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <ScoreBadge label="Market Viability" score={market} />
      <ScoreBadge label="Feasibility" score={feasibility} />
      <ScoreBadge label="Scalability" score={scalability} />
    </div>
  );
}

export function TeamScoreBadge({ score }: { score: number }) {
  return <ScoreBadge label="Founder-Market Fit" score={score} />;
}
