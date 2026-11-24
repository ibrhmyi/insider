import 'server-only';
import katex from 'katex';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';

/** Pieces for the methods write-up: numbered sections, typeset maths, code cells with their output, tables and figures.
 *  Everything renders on the server, so the page ships no maths or highlighting code. */

export function Section({n, id, title, children}: {n: string; id: string; title: string; children: React.ReactNode}) {
  return <section aria-labelledby={`${id}-title`} id={id} className="paper-section">
    <h2 id={`${id}-title`}><span className="num">{n}</span>{title}</h2>
    {children}
  </section>;
}

export const H3 = ({children}: {children: React.ReactNode}) => <h3 className="paper-h3">{children}</h3>;

/** Display maths. */
export function MathBlock({tex}: {tex: string}) {
  return <div className="math-block" dangerouslySetInnerHTML={{__html: katex.renderToString(tex, {displayMode: true, throwOnError: true})}}/>;
}

/** Inline maths. */
export function M({tex}: {tex: string}) {
  return <span dangerouslySetInnerHTML={{__html: katex.renderToString(tex, {throwOnError: true})}}/>;
}

/** A foldable code cell, highlighted on the server, with its printed output if there is one. */
export function CodeCell({title, code, out}: {title: string; code: string; out?: string}) {
  const html = Prism.highlight(code.trim(), Prism.languages.python, 'python');
  return <details className="code-cell">
    <summary>{title}</summary>
    <pre><code className="language-python" dangerouslySetInnerHTML={{__html: html}}/></pre>
    {out && <pre className="out">{out.trim()}</pre>}
  </details>;
}

export function Fig({src, w, h, alt, n, children, narrow = false}: {src: string; w: number; h: number; alt: string; n: number; children: React.ReactNode; narrow?: boolean}) {
  return <figure className={`nb-figure${narrow ? ' is-narrow' : ''}`}>
    {/* eslint-disable-next-line @next/next/no-img-element */}
    <img src={src} width={w} height={h} alt={alt} loading="lazy"/>
    <figcaption><b>Fig. {n}</b>{children}</figcaption>
  </figure>;
}

export function Table({caption, head, rows, note, main = [], rule = [], narrow = false, wide = false}: {
  caption: string; head: React.ReactNode[]; rows: React.ReactNode[][]; note?: React.ReactNode; main?: number[]; rule?: number[]; narrow?: boolean; wide?: boolean;
}) {
  return <>
    <div className="paper-table-wrap">
      <table className={`paper-table${narrow ? ' is-narrow' : ''}${wide ? ' is-wide' : ''}`}>
        <caption>{caption}</caption>
        <thead><tr>{head.map((h, i) => <th key={i}>{h}</th>)}</tr></thead>
        <tbody>{rows.map((r, i) => <tr key={i} className={[main.includes(i) ? 'is-main' : '', rule.includes(i) ? 'is-rule' : ''].join(' ').trim() || undefined}>
          {r.map((c, j) => <td key={j}>{c}</td>)}
        </tr>)}</tbody>
      </table>
    </div>
    {note && <p className="table-note">{note}</p>}
  </>;
}
