"use client";

import { useRef, useState } from "react";
import { uploadResume } from "@/lib/api";
import type { TeamMemberFormValues } from "@/lib/validators";
import { Spinner } from "@/components/ui/spinner";

interface TeamMembersFormProps {
  members: TeamMemberFormValues[];
  onChange: (members: TeamMemberFormValues[]) => void;
  errors?: Record<number, Partial<Record<keyof TeamMemberFormValues, string>>>;
}

const emptyMember = (): TeamMemberFormValues => ({
  name: "",
  role: "",
  resume_text: "",
  linkedin_url: "",
  domain_expertise: "",
  startup_experience: "",
  commitment_level: "",
});

export function TeamMembersForm({
  members,
  onChange,
  errors = {},
}: TeamMembersFormProps) {
  // Track upload state per member index
  const [uploading, setUploading] = useState<Record<number, boolean>>({});
  const [uploadErrors, setUploadErrors] = useState<Record<number, string>>({});
  const [fileNames, setFileNames] = useState<Record<number, string>>({});

  function updateMember(
    index: number,
    field: keyof TeamMemberFormValues,
    value: string
  ) {
    const updated = members.map((m, i) =>
      i === index ? { ...m, [field]: value } : m
    );
    onChange(updated);
  }

  async function handleFileUpload(index: number, file: File) {
    setUploading((p) => ({ ...p, [index]: true }));
    setUploadErrors((p) => ({ ...p, [index]: "" }));
    try {
      const { text, filename } = await uploadResume(file);
      setFileNames((p) => ({ ...p, [index]: filename }));
      updateMember(index, "resume_text", text);
    } catch (e) {
      setUploadErrors((p) => ({
        ...p,
        [index]: e instanceof Error ? e.message : "Upload failed.",
      }));
    } finally {
      setUploading((p) => ({ ...p, [index]: false }));
    }
  }

  function addMember() {
    onChange([...members, emptyMember()]);
  }

  function removeMember(index: number) {
    if (members.length <= 1) return;
    onChange(members.filter((_, i) => i !== index));
    setFileNames((p) => {
      const next = { ...p };
      delete next[index];
      return next;
    });
  }

  return (
    <div className="space-y-6">
      {members.map((member, index) => (
        <div
          key={index}
          className="bg-gray-50 border border-gray-200 rounded-xl p-5"
        >
          <div className="flex justify-between items-center mb-4">
            <h4 className="font-medium text-sm">Team Member {index + 1}</h4>
            {members.length > 1 && (
              <button
                type="button"
                onClick={() => removeMember(index)}
                className="text-xs text-red-500 hover:text-red-700"
              >
                Remove
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field
              label="Full Name *"
              value={member.name}
              onChange={(v) => updateMember(index, "name", v)}
              error={errors[index]?.name}
            />
            <Field
              label="Role *"
              value={member.role}
              onChange={(v) => updateMember(index, "role", v)}
              error={errors[index]?.role}
            />
          </div>

          {/* LinkedIn URL */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              LinkedIn Profile URL *
            </label>
            <input
              type="url"
              value={member.linkedin_url}
              onChange={(e) => updateMember(index, "linkedin_url", e.target.value)}
              placeholder="https://linkedin.com/in/yourname"
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                errors[index]?.linkedin_url ? "border-red-400" : "border-gray-300"
              }`}
            />
            {errors[index]?.linkedin_url && (
              <p className="text-xs text-red-500 mt-1">{errors[index]?.linkedin_url}</p>
            )}
          </div>

          {/* Resume upload */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resume *
            </label>
            <ResumeUpload
              index={index}
              fileName={fileNames[index]}
              uploading={!!uploading[index]}
              uploadError={uploadErrors[index]}
              hasText={member.resume_text.length >= 10}
              onFileChange={handleFileUpload}
            />
            {/* Show extracted text (read-only preview) */}
            {member.resume_text && (
              <details className="mt-2">
                <summary className="text-xs text-gray-500 cursor-pointer select-none">
                  Preview extracted text ({member.resume_text.length} chars)
                </summary>
                <pre className="mt-1 text-xs text-gray-600 bg-white border border-gray-200 rounded p-2 whitespace-pre-wrap max-h-40 overflow-y-auto">
                  {member.resume_text}
                </pre>
              </details>
            )}
            {/* Fallback manual paste */}
            {!fileNames[index] && (
              <div className="mt-2">
                <p className="text-xs text-gray-500 mb-1">
                  Or paste resume text manually:
                </p>
                <textarea
                  value={member.resume_text}
                  onChange={(e) => updateMember(index, "resume_text", e.target.value)}
                  placeholder="Paste education, work history, and key achievements..."
                  rows={4}
                  className={`w-full rounded-lg border px-3 py-2 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                    errors[index]?.resume_text ? "border-red-400" : "border-gray-300"
                  }`}
                />
              </div>
            )}
            {errors[index]?.resume_text && (
              <p className="text-xs text-red-500 mt-1">{errors[index]?.resume_text}</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <Field
              label="Domain Expertise"
              value={member.domain_expertise ?? ""}
              onChange={(v) => updateMember(index, "domain_expertise", v)}
            />
            <Field
              label="Startup Experience"
              value={member.startup_experience ?? ""}
              onChange={(v) => updateMember(index, "startup_experience", v)}
            />
            <Field
              label="Commitment Level"
              value={member.commitment_level ?? ""}
              onChange={(v) => updateMember(index, "commitment_level", v)}
              placeholder="e.g. Full-time, Part-time"
            />
          </div>
        </div>
      ))}

      <button
        type="button"
        onClick={addMember}
        className="text-sm text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1"
      >
        + Add Team Member
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Resume upload widget
// ---------------------------------------------------------------------------

function ResumeUpload({
  index,
  fileName,
  uploading,
  uploadError,
  hasText,
  onFileChange,
}: {
  index: number;
  fileName?: string;
  uploading: boolean;
  uploadError?: string;
  hasText: boolean;
  onFileChange: (index: number, file: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div>
      <div
        className={`flex items-center gap-3 border-2 border-dashed rounded-lg px-4 py-3 cursor-pointer transition-colors ${
          fileName
            ? "border-green-400 bg-green-50"
            : "border-gray-300 bg-white hover:border-brand-400"
        }`}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onFileChange(index, file);
          }}
        />
        {uploading ? (
          <>
            <Spinner className="h-4 w-4 text-brand-500" />
            <span className="text-sm text-gray-600">Extracting text...</span>
          </>
        ) : fileName ? (
          <>
            <span className="text-green-600 text-lg">✓</span>
            <div>
              <p className="text-sm font-medium text-gray-700">{fileName}</p>
              <p className="text-xs text-gray-500">Click to replace</p>
            </div>
          </>
        ) : (
          <>
            <span className="text-2xl text-gray-400">📄</span>
            <div>
              <p className="text-sm font-medium text-gray-700">
                Upload resume (PDF or TXT)
              </p>
              <p className="text-xs text-gray-500">Max 5 MB</p>
            </div>
          </>
        )}
      </div>
      {uploadError && (
        <p className="text-xs text-red-500 mt-1">{uploadError}</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Reusable field
// ---------------------------------------------------------------------------

function Field({
  label,
  value,
  onChange,
  placeholder,
  error,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  error?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 ${
          error ? "border-red-400" : "border-gray-300"
        }`}
      />
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}
