type PlaygroundResponseProps = {
  content: string;
  requestId: string;
};

export function PlaygroundResponse({ content, requestId }: PlaygroundResponseProps) {
  return (
    <section className="panel space-y-4 px-6 py-5">
      <div>
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-700">Response</div>
        <h3 className="mt-2 font-[var(--font-fira-code)] text-xl font-semibold text-slate-950">
          Assistant output
        </h3>
      </div>

      <div className="rounded-2xl border border-border bg-slate-50 px-4 py-4 text-sm leading-7 text-slate-800">
        {content}
      </div>

      <dl className="rounded-2xl border border-border bg-white px-4 py-4">
        <dt className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Request ID</dt>
        <dd className="mt-2 font-[var(--font-fira-code)] text-sm text-slate-900">{requestId}</dd>
      </dl>
    </section>
  );
}
