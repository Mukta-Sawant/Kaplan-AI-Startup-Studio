import Link from "next/link";

export default function HomePage() {
  return (
    <div className="py-16 text-center">
      <h1 className="text-4xl font-bold text-slate-900 mb-4">
        Startup Qualification Platform
      </h1>
      <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-10">
        Submit your startup for an AI-assisted Phase 1 qualification review. Two
        specialist agents — a VC analyst and an organizational psychologist —
        assess your submission in parallel and produce a Final Qualification
        Dossier for human mentor review.
      </p>

      <div className="flex justify-center gap-4 flex-wrap">
        <Link
          href="/submit"
          className="bg-brand-500 text-white px-8 py-3 rounded-xl text-lg font-semibold hover:bg-brand-600 transition-colors"
        >
          Submit Your Startup
        </Link>
        <Link
          href="/dashboard"
          className="border border-gray-300 text-gray-700 px-8 py-3 rounded-xl text-lg font-semibold hover:bg-gray-100 transition-colors"
        >
          View Dashboard
        </Link>
      </div>
    </div>
  );
}
