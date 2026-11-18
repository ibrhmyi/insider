import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {Replay, type ReplayData} from '@/components/product/replay';
import {Source} from '@/components/product/research';
import {getLayer2, getValidation, getWallets, getMarket, getMarkets, getV0, getV2, MARKET_IDS} from '@/lib/data';
import {FLAGS, FLAG_PLAIN, FLAG_SHORT, NOT_PROOF} from '@/lib/copy';
import {CASES, SOURCES, SRC, WHERE} from '@/lib/research';

const REPO = 'https://github.com/ibrhmyi/insider';
// One centred reading column, the same width as the research articles on iyildiz.me/research.
const pad = 'mx-auto w-full max-w-[680px] px-6';

/** One part of the story: a small label and a few paragraphs, like the other research articles. */
function Part({id, title, children}: {id: string; title: string; children: React.ReactNode}) {
  return <section aria-labelledby={`${id}-title`} id={id} className={`flex flex-col gap-5 py-10 ${pad}`}>
    <h2 id={`${id}-title`} className="research-label text-text-3">{title}</h2>
    {children}
  </section>;
}

const P = ({children, muted = false}: {children: React.ReactNode; muted?: boolean}) =>
  <p className={`type-product max-w-measure ${muted ? 'text-text-2' : 'text-text-1'}`}>{children}</p>;

const lcFirst = (t: string) => t.charAt(0).toLowerCase() + t.slice(1);
const sg = (x: number, d = 2) => `${x >= 0 ? '+' : '-'}${Math.abs(x).toFixed(d)}`;
const pts = (x: number) => `${x >= 0 ? '+' : '-'}${Math.abs(x * 100).toFixed(0)}`;
const pct = (x: number) => `${Math.round(x * 100)}%`;
const n0 = (x: number) => x.toLocaleString('en-US');
const ordinal = (n: number) => n === 1 ? '1st' : n === 2 ? '2nd' : n === 3 ? '3rd' : `${n}th`;

export default function Home() {
  const replay: ReplayData = JSON.parse(readFileSync(join(process.cwd(), 'public', 'data', 'maduro_replay.json'), 'utf8'));
  const charged = getValidation().find(v => v.label_id === 'MAD-CFTC-1')!;
  const w = getWallets('maduro').find(x => x.id === charged.wallet_id)!;
  const head = getMarkets().headline;
  const v0 = getV0();
  // Every number below is read from the frozen result files at build time.
  const perm = Object.fromEntries(MARKET_IDS.map(m => [m, getMarket(m)!.permutation]));
  const l2 = (scope: string) => getLayer2().tests.find(t => t.outcome === 'wallets' && t.H === 30 && t.scope === scope)!;
  const pooledL2 = l2('pooled').mean_diff;
  const nobelL2 = l2('nobel').mean_diff;
  const chanceOnly = MARKET_IDS.filter(m => m !== 'nobel' && perm[m].p_value >= 0.05).map(m => ({maduro: 'Maduro', iran: 'Iran', nobel: 'Nobel'})[m]);
  const others = head.n_high_total - head.documented_flagged;
  const v2 = getV2();
  const [soldier, google, israel, youtube] = CASES;
  const [allMk, political, military] = WHERE;

  return <article id="top" className="pb-10 text-text-1" style={{'--title-ch': '30ch'} as React.CSSProperties}>
    <header aria-labelledby="question-title" className={`flex flex-col gap-5 pt-[12vh] pb-4 ${pad}`}>
      <a href="/research/" className="research-label w-fit text-text-3 transition-colors duration-(--dur-state) hover:text-text-1 focus-visible:focus-ring">← Research</a>
      <p className="research-label mt-12 text-text-3"><time dateTime="2026-11-14">11.2026</time> · Capstone</p>
      <h1 id="question-title" className="type-story-title max-w-(--title-ch)">Can public trades reveal an insider before the news breaks?</h1>
      <p className="type-product max-w-measure text-text-2">On Polymarket every trade is public, but nobody checks them while a market is still open. I wanted to see whether a few simple signs could point at suspicious bets before the news came out.</p>
    </header>

    <Part id="question" title="The question">
      <P>In 2026 US regulators brought their first insider trading cases on prediction markets. In one, a {soldier.who} is charged with making {soldier.made} by betting on the raid on Maduro before it happened. <Source href={soldier.source}>CFTC</Source></P>
      <P>Whoever takes the other side of a bet like that loses. And the evidence is sitting in the open: every trade settles on a public blockchain with its time, wallet, side, size and price. Who owns a wallet is not public. <Source href={SRC.polymarketDocs}>Polymarket docs</Source></P>
      <P>The screens published so far work after a market resolves, and they don&apos;t release the wallets they flag. <Source href={SRC.bock}>Bock and Guenthoer</Source> <Source href={SRC.nechepurenko}>Nechepurenko</Source> So my question was simple: can a check that runs while a market is open spot the pattern early?</P>
    </Part>

    <Part id="pattern" title="What the cases have in common">
      <P>The public cases share a shape. Besides the soldier, a {google.who} is charged over {google.secret} ({google.made}) <Source href={google.source}/>, an {israel.who} are indicted over {lcFirst(israel.secret)} ({israel.made}) <Source href={israel.source}/>, and a {youtube.who} was fined on Kalshi for betting on {lcFirst(youtube.secret)} <Source href={youtube.source}/>. Charged or indicted is not convicted.</P>
      <P>They all bet where a few people know the answer first, and those markets show it. Of long-shot bets of $2,500 or more at 35¢ or less, {allMk.pct}% win across all markets, {political.pct}% in political markets and {military.pct}% in military and defense. <Source href={SRC.acdcMarkets}>ACDC</Source></P>
      <P>The trading looks alike too. The account is new, it bets on one event and goes quiet, it buys the unlikely side big, and it buys close to the news. <Source href={SRC.acdcOrcas}>ACDC</Source> <Source href={SRC.gomezCram}>Gomez-Cram et al.</Source> Not every case fits: the Google engineer used an account opened two years earlier. <Source href={SRC.googleAccount}/></P>
    </Part>

    <Part id="check" title="The check">
      <P>I turned that pattern into six yes-or-no questions for every wallet that bought before the news. The thresholds were fixed before I looked at any results.</P>
      <ol aria-label="The six signs" className="type-product flex max-w-measure list-decimal flex-col gap-1 ps-5 text-text-2 marker:text-text-3">
        {FLAGS.map(f => <li key={f}><span className="text-text-1">{FLAG_SHORT[f]}.</span> {FLAG_PLAIN[f]}</li>)}
      </ol>
      <P>Four or more yeses means the wallet is worth a look, nothing more. The wallet later charged in the Maduro case answers yes to {w.score} of 6.</P>
    </Part>

    <Part id="result" title="What happened">
      <P>I ran it on three past markets: Maduro, the Nobel Peace Prize and the Iran strike. In the Maduro market the charged wallet ranked {ordinal(head.rank)} of {head.n_in_market.toLocaleString('en-US')}, flagged {head.hours_before} hours before the news. Across all three markets, {head.documented_flagged} of {head.documented_total} wallets named in public reporting were flagged.</P>
    </Part>

    <figure aria-label="Replay of the Maduro market" className={`py-6 ${pad}`}>
      <Replay d={replay}/>
    </figure>

    <Part id="caveats" title="Why that is less than it sounds">
      <P>Journalists found those named wallets by looking for similar signs, so {head.documented_flagged} of {head.documented_total} is partly circular. The check also flagged {others} other wallets that nobody has accused.</P>
      <P>When I shuffled the trade times {perm.nobel.n_perm.toLocaleString('en-US')} times, only the Nobel market had more flags than chance would give: {perm.nobel.observed} against {Math.round(perm.nobel.null_mean)} expected, p&nbsp;=&nbsp;{perm.nobel.p_value.toFixed(3)}. {chanceOnly.join(' and ')} did no better than chance.</P>
      <P>My first idea didn&apos;t hold either. I expected big bets to draw more copycats where insiders are possible, but the difference was {v0.pooled['insider-possible'].mean_excess} against {v0.pooled['insider-impossible'].mean_excess} extra wallets, p&nbsp;=&nbsp;{v0.p_value.toFixed(2)}. {pooledL2 < 0 && nobelL2 > 0
        ? 'And other traders followed flagged wallets less than ordinary bets of the same size, except in the Nobel market.'
        : `Followers after flagged bets, against ordinary bets of the same size: ${pooledL2.toFixed(1)} overall, ${nobelL2.toFixed(1)} in the Nobel market.`}</P>
    </Part>

    <Part id="v2" title="Next model: let the data choose the weights.">
      <P>I replaced my hand-picked signs with weights learned from {v2.learned.train_markets} resolved markets and {n0(v2.learned.train_wallets)} wallets, then tested them on {v2.learned.val_markets} later markets the model had not seen.</P>
      <div className="flex flex-col gap-2">
        <h3 className="type-product text-text-1">Do winners keep winning?</h3>
        <P muted>{v2.persistence.diff[1] > 0 ? 'Partly.' : 'Not clearly.'} The top 5% of wallets in 2025 (n&nbsp;=&nbsp;{v2.persistence.n_top}) beat the price they paid by {pts(v2.persistence.top_2025)} points; in 2026 the same group (n&nbsp;=&nbsp;{v2.persistence.n_top_2026}) beat it by {pts(v2.persistence.top_2026[0])} points ({pts(v2.persistence.top_2026[1])} to {pts(v2.persistence.top_2026[2])}), against {pts(v2.persistence.others_2026[0])} for everyone else. The gap of {pts(v2.persistence.diff[0])} points ranges from {pts(v2.persistence.diff[1])} to {pts(v2.persistence.diff[2])}, which includes zero.</P>
      </div>
      <div className="flex flex-col gap-3">
        <h3 className="type-product text-text-1">Does it beat the market price?</h3>
        <dl className="grid grid-cols-2 gap-x-6 border-y border-line py-4">
          <div className="flex flex-col gap-1">
            <dt className="type-product text-text-2">Model Brier score</dt>
            <dd className="type-product-title text-text-1">{v2.validation.brier_model.toFixed(3)}</dd>
            <dd className="type-product text-text-3">{v2.validation.brier_model_ci[0].toFixed(3)} to {v2.validation.brier_model_ci[1].toFixed(3)}</dd>
          </div>
          <div className="flex flex-col gap-1">
            <dt className="type-product text-text-2">Market price Brier score</dt>
            <dd className="type-product-title text-text-1">{v2.validation.brier_market.toFixed(3)}</dd>
            <dd className="type-product text-text-3">{v2.validation.brier_market_ci[0].toFixed(3)} to {v2.validation.brier_market_ci[1].toFixed(3)}</dd>
          </div>
        </dl>
        <P><strong className="font-medium">{v2.validation.verdict}.</strong> Lower is better. The difference is {sg(v2.validation.diff, 3)}, with an interval from {sg(v2.validation.diff_ci[0], 3)} to {sg(v2.validation.diff_ci[1], 3)}, so it cannot be told apart from zero (n&nbsp;=&nbsp;{v2.validation.n_points} points in {v2.validation.n_markets} markets). On {n0(v2.validation.unit.n_units)} individual positions the scores are {v2.validation.unit.brier_model.toFixed(3)} for the model and {v2.validation.unit.brier_market.toFixed(3)} for the market.</P>
      </div>
      <div className="flex flex-col gap-3">
        <h3 className="type-product text-text-1">What it learned</h3>
        <ul aria-label="Largest weights" className="flex flex-col border-t border-line">
          {v2.coefficients.map(c => <li key={c.feature} className="flex flex-col gap-1 border-b border-line py-4">
            <span className="type-product text-text-1">{c.plain.charAt(0).toUpperCase() + c.plain.slice(1)}</span>
            <span className="type-product text-text-2">A higher value went with {c.direction} winning than the price already says ({sg(c.coef, 2)} per standard deviation, interval {sg(c.lo, 2)} to {sg(c.hi, 2)}). {c.excludes_zero ? 'The interval excludes zero, but the effect is small.' : 'The interval includes zero, so it may be nothing.'}</span>
          </li>)}
        </ul>
      </div>
    </Part>

    <Part id="forward" title="Ten predictions, locked before the outcome.">
      <ul aria-label="Ten locked predictions" className="flex flex-col border-t border-line">
        {v2.forward.predictions.map(p => <li key={p.slug} className="flex flex-col gap-1 border-b border-line py-4">
          <span className="type-product text-text-1">{p.question}</span>
          <span className="type-product flex flex-wrap gap-x-5 gap-y-1 text-text-2">
            <span>Market price {pct(p.market)}</span>
            <span>Model {pct(p.model)}</span>
            <span className="text-text-3">{p.status}</span>
          </span>
        </li>)}
      </ul>
      <P muted>Locked {v2.forward.snapshot_utc.replace('T', ' ').replace(/:\d\dZ$/, ' UTC')} in <a href={v2.forward.commit_url} target="_blank" rel="noreferrer" className="underline underline-offset-4 hover:text-text-1 focus-visible:focus-ring">commit {v2.forward.commit.slice(0, 7)}</a>. The model passes if its Brier score beats the market price on the markets that resolve.</P>
    </Part>

    <Part id="takeaway" title="What I take away">
      <P>A flag is a reason to look, not proof. The check finds the obvious pattern, held up in one market of three, and misses anyone who uses an old account, as in the Google case.</P>
    </Part>

    <footer className={`flex flex-col gap-5 py-10 ${pad}`}>
      <h2 className="research-label text-text-3">Sources</h2>
      <ul aria-label="Sources" className="flex flex-col gap-1">
        {SOURCES.map(s => <li key={s.href} className="flex flex-wrap items-baseline gap-x-3">
          <Source href={s.href}>{s.name}</Source>
          <span className="type-product text-text-3">{s.what}</span>
        </li>)}
      </ul>
      <p className="type-product text-text-3">{NOT_PROOF} <a href={REPO} target="_blank" rel="noreferrer" className="text-text-2 underline underline-offset-4 hover:text-text-1 focus-visible:focus-ring">Code and data on GitHub</a></p>
    </footer>
  </article>;
}
