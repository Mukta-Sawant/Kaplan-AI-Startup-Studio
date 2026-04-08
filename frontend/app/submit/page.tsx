import { StartupForm } from "@/components/startup-form";

export const metadata = {
  title: "Submit Your Startup — KI Agentic",
};

export default function SubmitPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Submit Your Startup</h1>
        <p className="text-gray-600 mt-2 text-sm">
          Complete all required sections. Your submission will be assessed by two
          AI agents in parallel and reviewed by a human mentor. No startup is
          autonomously approved or rejected.
        </p>
      </div>
      <StartupForm />
    </div>
  );
}
