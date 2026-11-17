import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {Replay, type ReplayData} from '@/components/product/replay';
import {Source} from '@/components/product/research';
import {getLayer2, getValidation, getWallets, getMarket, getMarkets, getV0, MARKET_IDS} from '@/lib/data';
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

    <Part id="takeaway" title="What I take away">
      <P>A flag is a reason to look, not proof. The check finds the obvious pattern, held up in one market of three, and misses anyone who uses an old account, as in the Google case.</P>
      <P muted>Next I want to learn how much each sign should count from resolved markets, then lock predictions on 10 open markets and score them when they resolve.</P>
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
