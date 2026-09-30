type PlaygroundResponseProps = {
  content: string;
};

export function PlaygroundResponse({ content }: PlaygroundResponseProps) {
  return (
    <section className="panel space-y-4 px-6 py-5">
      <div>
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-mark">Response</div>
        <h3 className="mt-2 text-xl font-semibold text-ink">
          Assistant output
        </h3>
      </div>

      <div className="rounded-2xl border border-line bg-canvas px-4 py-4 text-sm leading-7 text-ink-2">
        {content}
      </div>
    </section>
  );
}
