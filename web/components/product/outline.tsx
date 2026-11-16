/** The page's outline: one ruled bar that stays at the top, so the presenter and the audience always know where they are. */
export const OUTLINE: {id: string; label: string}[] = [
  {id: 'who', label: 'Who'},
  {id: 'where', label: 'Where'},
  {id: 'how', label: 'How'},
  {id: 'model', label: 'Model'},
  {id: 'findings', label: 'Findings'},
  {id: 'demo', label: 'Demo'},
  {id: 'next', label: 'Limits'},
];

export function Outline() {
  return <nav aria-label="Outline" className="sticky top-0 z-(--z-raised) flex flex-wrap items-center gap-x-8 gap-y-2 border-b border-line bg-page px-6 py-3 sm:px-12 lg:px-24">
    <a href="#top" className="type-label-lg text-text-1 focus-visible:focus-ring">Insider signal</a>
    <ol className="flex flex-wrap items-center gap-x-6 gap-y-2">
      {OUTLINE.map((o, i) => <li key={o.id}>
        <a href={`#${o.id}`} className="type-label-lg text-text-2 transition-colors duration-(--dur-state) hover:text-text-1 focus-visible:focus-ring">{i + 1} {o.label}</a>
      </li>)}
    </ol>
  </nav>;
}
