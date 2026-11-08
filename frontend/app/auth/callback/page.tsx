"use client";

import { useEffect, useState } from "react";
import { completeLoginFromCallback } from "../../../lib/oidc";
import { Button } from "../../../components/ui";

export default function AuthCallbackPage() {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await completeLoginFromCallback(window.location.href);
        if (!cancelled) {
          window.location.replace("/dashboard/");
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Sign-in failed");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6">
        <h1 className="text-xl font-bold text-[var(--ink)]">Sign-in failed</h1>
        <p className="text-sm text-[var(--ink-muted)]" role="alert">
          {error}
        </p>
        <Button href="/dashboard/">Back to dashboard</Button>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <p className="text-sm text-[var(--ink-muted)]">Completing sign-in…</p>
    </main>
  );
}
