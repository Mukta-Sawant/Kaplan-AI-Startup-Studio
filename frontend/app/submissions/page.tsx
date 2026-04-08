import { redirect } from "next/navigation";

/**
 * /submissions redirects to /dashboard which already lists all submissions.
 */
export default function SubmissionsPage() {
  redirect("/dashboard");
}
