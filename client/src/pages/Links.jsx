import { useEffect, useState } from "react";
import { AlertCircle, ExternalLink, Link2 } from "lucide-react";
import { api, ApiError } from "../services/api";

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Date unavailable"
    : new Intl.DateTimeFormat(undefined, {
        day: "numeric",
        month: "short",
        year: "numeric",
      }).format(date);
}

export default function Links() {
  const [links, setLinks] = useState([]);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .listSavedLinks()
      .then((saved) => {
        if (!cancelled) setLinks(saved);
      })
      .catch((error) => {
        if (cancelled) return;
        setLoadError(error instanceof ApiError ? error.message : "Unable to load saved links.");
        setLinks([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="w-full pb-10">
      <header className="mb-8">
        <h1 className="font-display text-4xl sm:text-5xl tracking-wide text-[#261B33] uppercase mb-3">
          LINKS
        </h1>
        <p className="text-[#776A83] font-medium text-lg">
          Saved links with their title, date, and hyperlink.
        </p>
      </header>

      {loadError && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 p-3 rounded-xl text-sm font-medium mb-4">
          <AlertCircle size={16} /> {loadError}
        </div>
      )}

      {links.length === 0 && !loadError ? (
        <div className="rounded-3xl border-2 border-dashed border-[#E3D4F8] bg-white p-12 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#F0E8FF] border border-[#E3D4F8] shadow-xs">
            <Link2 size={28} className="text-[#8B5CF6]" />
          </div>
          <p className="text-[#776A83] font-medium">No saved links yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {links.map((link) => (
            <article
              key={link.id}
              className="rounded-2xl border border-[#E3D4F8] bg-white p-5 shadow-[0_2px_12px_-4px_rgba(139,92,246,0.04)] hover:shadow-md hover:border-[#8B5CF6]/40 hover:-translate-y-0.5 transition-all"
            >
              <h2 className="text-base font-bold text-[#261B33]">{link.label}</h2>
              <p className="mt-1 text-sm text-[#776A83]">{formatDate(link.created_at)}</p>
              <a
                href={link.url}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-flex items-center gap-1.5 break-all text-sm font-semibold text-[#8B5CF6] underline underline-offset-2 hover:text-[#6D28D9] transition-colors"
              >
                {link.url}
                <ExternalLink size={13} />
              </a>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
