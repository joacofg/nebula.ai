type PlaygroundResponseProps = {
  content: string;
};

export function PlaygroundResponse({ content }: PlaygroundResponseProps) {
  return (
    <section aria-labelledby="playground-response-heading" className="flex flex-col gap-2">
      <h2 id="playground-response-heading" className="m-0 text-lg font-semibold text-ink">
        Respuesta
      </h2>
      <div className="max-h-[420px] overflow-y-auto bg-canvas px-4 py-3 text-[15px] leading-relaxed whitespace-pre-wrap text-ink [overflow-wrap:anywhere]">
        {content}
      </div>
    </section>
  );
}
