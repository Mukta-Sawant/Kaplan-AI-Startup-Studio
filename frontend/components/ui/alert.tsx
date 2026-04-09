import { ReactNode } from "react";

interface AlertProps {
  variant?: "error" | "warning" | "info" | "success";
  children: ReactNode;
  className?: string;
}

const styles = {
  error: "bg-red-50 border-red-300 text-red-800",
  warning: "bg-yellow-50 border-yellow-300 text-yellow-800",
  info: "bg-blue-50 border-blue-300 text-blue-800",
  success: "bg-green-50 border-green-300 text-green-800",
};

export function Alert({ variant = "info", children, className = "" }: AlertProps) {
  return (
    <div className={`border rounded-lg px-4 py-3 text-sm ${styles[variant]} ${className}`}>
      {children}
    </div>
  );
}
