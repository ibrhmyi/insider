import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import 'katex/dist/katex.min.css';
import './paper.css';
import {Replay, type ReplayData} from '@/components/product/replay';
import {Source} from '@/components/product/research';
import {CodeCell, Fig, H3, M, MathBlock, Section, Table} from '@/components/product/paper';
import {getLayer2, getValidation, getMarkets, getV0, getV2} from '@/lib/data';
import {FLAGS, FLAG_SHORT, NOT_PROOF} from '@/lib/copy';
import {CASES, FEATURE_DEFS, FREEZES, SOURCES, SRC, WHERE} from '@/lib/research';
import type {FlagId, MarketId} from '@/lib/types';

const REPO = 'https://github.com/ibrhmyi/insider';
const NAME: Record<MarketId, string> = {maduro: 'Maduro', nobel: 'Nobel', iran: 'Iran'};
const ORDER: MarketId[] = ['iran', 'maduro', 'nobel'];

// Number formatting. Every value comes from the frozen result files at build time.
const n0 = (x: number) => x.toLocaleString('en-US');
const f = (x: number, d = 2) => (x < 0 ? '−' : '') + Math.abs(x).toFixed(d);
const sg = (x: number, d = 2) => (x >= 0 ? '+' : '−') + Math.abs(x).toFixed(d);
const pc = (x: number, d = 0) => `${(x * 100).toFixed(d)}%`;
const pv = (p: number) => p < 0.001 ? '< 0.001' : p.toFixed(3);
const ci = (a: number, b: number, d = 2) => `[${f(a, d)}, ${f(b, d)}]`;
const lcFirst = (t: string) => t.charAt(0).toLowerCase() + t.slice(1);

export default function Home() {
  const replay: ReplayData = JSON.parse(readFileSync(join(process.cwd(), 'public', 'data', 'maduro_replay.json'), 'utf8'));
  const mk = getMarkets();
  const head = mk.headline;
  const th = mk.flags;
  const byId = Object.fromEntries(mk.markets.map(m => [m.id, m])) as Record<MarketId, (typeof mk.markets)[number]>;
  const v0 = getV0();
  const l2 = getLayer2();
  const val = getValidation();
  const v2 = getV2();
  const distinctNamed = new Set(val.map(v => v.wallet_id)).size;
  const others = head.n_high_total - head.documented_flagged;
  const [soldier, google, israel, youtube] = CASES;
  const [allMk, political, military] = WHERE;
  const thr: Record<FlagId, string> = {
    F1: `≤ ${th.F1_days} days`, F2: `≥ ${th.F2_share} or ≤ ${th.F2_markets} markets`, F3: `≤ ${th.F3_price}`,
    F4: `≥ $${n0(th.F4_usd)}`, F5: `≥ ${th.F5_conv}`, F6: `≤ ${th.F6_hours} h`,
  };
  const wl = (H: number, scope: string) => l2.tests.find(t => t.outcome === 'wallets' && t.H === H && t.scope === scope)!;
  const imp60 = mk.impact.impact_60m_per_1k;
  const bands = ['<1k', '1k-2.5k', '2.5k-10k', '>=10k'];
  const prec = (band: string, high: boolean) => mk.precision.find(p => p.size_band === band && p.is_high === high)!;
  const vv = v2.validation;
  const ps = v2.persistence;
  const md = v2.model;
  const nobel = byId.nobel.permutation;

  return <article id="top" className="paper">
    <a href="/research/" className="paper-back">← Research</a>

    <header className="paper-head">
      <p className="paper-meta"><time dateTime="2026-11-14">11.2026</time> · Capstone · Python</p>
      <h1 className="paper-title">Detecting Potential Insider Trading on Polymarket</h1>
      <p className="paper-lede">Every Polymarket trade is public, but published screens for informed trading run after a market resolves. This project asks whether an ex-ante screen, using only data available before the news, can surface unusual activity for review while a market is still open. It tests three pre-registered approaches against a permutation null, publicly documented cases, a matched follow-on design and an out-of-sample market benchmark, with every rule frozen before the data it was judged on.</p>
    </header>

    <div className="paper-stats" role="list" aria-label="Key results">
      <div role="listitem"><span className="stat-value">{head.rank === 1 ? '1st' : `#${head.rank}`}<small>/ {n0(head.n_in_market)}</small></span><span className="stat-label">Rank of the charged wallet, Maduro</span></div>
      <div role="listitem"><span className="stat-value">{distinctNamed} / {distinctNamed}</span><span className="stat-label">Publicly named wallets scored 4 or more</span></div>
      <div role="listitem"><span className="stat-value">{pv(nobel.p_value)}</span><span className="stat-label">Permutation p, Nobel (other markets n.s.)</span></div>
      <div role="listitem"><span className="stat-value">{sg(vv.diff, 3)}</span><span className="stat-label">v2 Brier vs market, 95% CI {ci(vv.diff_ci[0], vv.diff_ci[1], 3)}</span></div>
    </div>

    <Section n="01" id="background" title="Background and question">
      <p>In 2026 US regulators brought their first insider trading cases on prediction markets. A {soldier.who} is charged with making {soldier.made} by buying Yes on the raid on Maduro before it happened <Source href={soldier.source}>CFTC</Source>. A {google.who} is charged over {google.secret} ({google.made}) <Source href={google.source}/>; an {israel.who} are indicted over {lcFirst(israel.secret)} ({israel.made}) <Source href={israel.source}/>; and a {youtube.who} was fined on Kalshi <Source href={youtube.source}/>. Charged or indicted is not convicted.</p>
      <p>These are markets decided by a small group. Of long-shot bets of $2,500 or more at 35¢ or less, {allMk.pct}% win across all Polymarket markets, {political.pct}% in political markets and {military.pct}% in military and defense <Source href={SRC.acdcMarkets}>ACDC</Source>. Reported cases share a trading pattern: new accounts, one event then silence, large long-shot buys close to the news, and outsized price impact per dollar <Source href={SRC.acdcOrcas}>ACDC</Source> <Source href={SRC.gomezCram}>Gomez-Cram et al.</Source></p>
      <p>Every trade settles on a public blockchain with its time, wallet, side, size and price; wallet ownership and unfilled orders are not public <Source href={SRC.polymarketDocs}>Polymarket docs</Source>. Existing screens work after resolution and do not release their flagged lists <Source href={SRC.bock}>Bock and Guenthoer</Source> <Source href={SRC.nechepurenko}>Nechepurenko</Source>. The question here is whether a screen built only from pre-news data can rank the wallets later named in public reporting near the top, and whether that ranking beats chance.</p>
      <p>Throughout, a high score means <strong>unusual activity for review</strong>, consistent with informed trading. It never identifies an owner or shows that a wallet traded on inside information.</p>
    </Section>

    <Section n="02" id="design" title="Data and design">
      <p>The pilot studies three resolved markets whose outcome a small group could know early, labelled insider-possible from their resolution rules alone. T_news is the first public news, from the event timeline; only fills strictly before it are used to score a wallet.</p>
      <Table caption="Table 1 · Study markets"
        head={['Market', 'T_news (UTC)', 'Pre-news buyers', 'Pre-news buy fills', 'Volume']}
        rows={ORDER.map(id => {
          const m = byId[id];
          return [<span key="q">{m.question}</span>, m.t_news_utc.replace('T', ' ').replace(':00Z', ''), n0(m.n_wallets), n0(m.pre_news_buy_fills), `$${(m.volume_usd / 1e6).toFixed(1)}M`];
        })}
        note="Trades and wallet statistics from the Polymarket Data API (maker and taker fills). Two BTC threshold markets serve as insider-impossible controls for v0."/>
      <p><strong>Freeze before validate.</strong> Each rule was written and committed before the data it would be judged on was computed. The order is part of the evidence:</p>
      <Table caption="Table 2 · Pre-registration timeline"
        head={['Rule', 'Frozen', 'Before']}
        rows={FREEZES.map(r => [<span key="r">{r.rule}<br/><code className="text-[11px] text-[#6f6f6a]">{r.file}</code></span>, r.frozen, <span key="b" className="whitespace-normal">{r.before}</span>])}/>
    </Section>

    <Section n="03" id="v0" title="First hypothesis: the ripple (v0, not supported)">
      <p>The first idea was market-level. After a large seed trade (above the rolling 99th percentile of the previous 24 hours), does same-direction follow-on trading, the ripple, exceed what matched ordinary moments predict, and more so in insider-possible markets than in controls? For seed <M tex="s"/>, the expected ripple averages the <M tex="k = 10"/> nearest no-seed anchors in the same market within ±2 h, matched on price and recent activity:</p>
      <MathBlock tex={String.raw`E_s = R_s - \frac{1}{k}\sum_{j \in \mathcal{N}_k(s)} R_j, \qquad R = \#\{\text{distinct same-direction wallets in } (t, t + 30\,\text{min}]\}`}/>
      <p>Seeds whose window touches the news ±30 min are excluded. The detector was tuned on controls only, where a placebo of 300 random ordinary trades showed a residual bias of +{v0.placebo_bias} wallets.</p>
      <Table caption="Table 3 · Excess ripple per pre-news seed (distinct wallets)"
        head={['Market', 'Label', 'Seeds compared', 'Mean excess', 'Alerts']}
        rows={v0.per_market.filter(r => r.n_compared > 0).map(r => [r.market.replace('ctrl_', 'control: '), r.label, String(r.n_compared), r.mean_excess === null ? 'n/a' : sg(r.mean_excess), String(r.n_alerts)])}
        note={`Pooled: insider-possible ${v0.pooled['insider-possible'].mean_excess} (n = ${v0.pooled['insider-possible'].n_seeds} seeds, ${v0.pooled['insider-possible'].n_markets} markets) against controls ${v0.pooled['insider-impossible'].mean_excess} (n = ${v0.pooled['insider-impossible'].n_seeds}, ${v0.pooled['insider-impossible'].n_markets} markets). Label-permutation p = ${v0.p_value.toFixed(2)}. One control had no usable seeds.`}/>
      <Fig src="/figures/ripple.png" w={1600} h={651} n={1} alt="Box plots of excess ripple after seed trades for controls and insider-possible markets at the 95th, 99th and 99.5th percentile seed thresholds; the distributions overlap heavily.">Excess ripple per seed, controls against insider-possible markets, at three seed thresholds. Dashed line: placebo bias.</Fig>
      <p>The difference is small and not distinguishable from zero (p = {v0.p_value.toFixed(2)}), and seeds within a market are not independent. In a blind run on Maduro, the one pre-news alert came {v0.maduro_blind.hours_before_news} h early and {v0.maduro_blind.direction}. Market-level herding did not separate the groups, so v1 moved to the wallet as the unit.</p>
    </Section>

    <Section n="04" id="screen" title="Layer 1: an ex-ante wallet screen (v1)">
      <p>The unit is a wallet in a market: every wallet with at least one buy fill before T_news. Six features are computed only from pre-news data, each with a threshold taken from the literature before any study market was scored:</p>
      <Table caption="Table 4 · Ex-ante features and frozen thresholds"
        head={['Flag', 'Definition', 'Fires when']}
        rows={FLAGS.map(k => [<span key="k">{k} · {FLAG_SHORT[k]}</span>, <span key="d" className="whitespace-normal">{FEATURE_DEFS[k]}</span>, thr[k]])}/>
      <MathBlock tex={String.raw`S_w = \sum_{k=1}^{6} \mathbb{1}\!\left[F_k(w)\ \text{fires}\right], \qquad \text{high score} \iff S_w \ge ${th.HIGH}`}/>
      <p>Correctness (F7) and dormancy after resolution (F8) are post-hoc and <strong>never enter the score</strong>; they are used only to evaluate it. One feature input, lifetime markets traded, is measured after the fact, but it can only understate F2 at T_news, so it cannot leak toward flagging.</p>
      <Table caption="Table 5 · How often each flag fires among pre-news buyers"
        head={['Flag', ...ORDER.map(id => NAME[id])]}
        rows={FLAGS.map(k => [`${k} · ${FLAG_SHORT[k]}`, ...ORDER.map(id => pc(byId[id].firing_rates[k]))])}
        note={`Wallets scoring ${th.HIGH} or more: ${ORDER.map(id => `${NAME[id]} ${byId[id].n_high} of ${n0(byId[id].n_wallets)}`).join(', ')}.`}/>
      <CodeCell title="Per-wallet features from pre-news fills (src/v1_03_layer1.py)" code={`
def features(m, f, upto=None):
    """Per-wallet features from pre-news fills (optionally only fills <= upto[wallet])."""
    T = T_NEWS[m]
    pre = f[(f.timestamp < T) & (~f.after_resolution)]
    buyers = set(pre[pre.side == "BUY"].proxy_wallet)
    pre = pre[pre.proxy_wallet.isin(buyers)]
    for w, g in pre.groupby("proxy_wallet", sort=False):
        b = g[g.side == "BUY"]
        main = int(b.groupby("outcome_index").usd.sum().idxmax())   # main side = largest pre-news buy USD
        bm = b[b.outcome_index == main]
        f1 = max(first_m - acct, 0) / 86400                         # days from account start to first fill here
        share = min(g.usd.sum() / denom, 1.0)                       # share of the wallet's volume to T_news
        vwap = bm.usd.sum() / bm["size"].sum()                      # price paid on the main side
        buy_usd = b.usd.sum()
        conv = abs((g.dir * g.usd).sum()) / g.usd.sum()             # net YES-direction USD / gross USD
        hrs = (T - wmedian_time(bm.timestamp.values, bm.usd.values)) / 3600
        fl = dict(F1=f1 <= FLAGS["F1_days"],
                  F2=share >= FLAGS["F2_share"] or nmk <= FLAGS["F2_markets"],
                  F3=vwap <= FLAGS["F3_price"], F4=buy_usd >= FLAGS["F4_usd"],
                  F5=conv >= FLAGS["F5_conv"], F6=hrs <= FLAGS["F6_hours"])
        score = int(sum(fl.values()))`}/>
    </Section>

    <Section n="05" id="validation" title="Validation against publicly documented wallets">
      <p>Labels come only from public reporting (a CFTC complaint, Lookonchain, Bloomberg, WSJ and ACDC), each with its source, and a wallet is never added because the screen flagged it. A reported handle matches only if it equals the name Polymarket serves on that wallet&apos;s fills; an address prefix matches only if exactly one wallet in the market starts with it.</p>
      <Table caption="Table 6 · Documented wallets in the screen"
        head={['Label', 'Status', 'Score', 'Rank', 'First scored 4+', 'Source']}
        rows={val.map(v => [`${v.label_id}`, v.confidence, `${v.score} / 6`, `${v.rank} of ${n0(v.n)}`, `${v.first_high_h} h before news`, <Source key="s" href={v.source}/>])}
        main={val.map((v, i) => v.confidence === 'charged' ? i : -1).filter(i => i >= 0)}
        note={`${val.length} labels cover ${distinctNamed} distinct wallets (two reports name the same Maduro wallet). Rank: descending score, ties broken by pre-news buy USD. "First scored 4+" recomputes the features using only the wallet's own fills up to each of its buys.`}/>
      <p>All {distinctNamed} named wallets score {th.HIGH} or more. The wallet behind the CFTC complaint scores 6 of 6, ranks <strong>{head.rank === 1 ? '1st' : `#${head.rank}`} of {n0(head.n_in_market)}</strong> buyers in the Maduro market, and first reaches the high band <strong>{head.hours_before} h</strong> before the news.</p>
      <Fig src="/figures/scores.png" w={1600} h={566} n={2} alt="Distribution of ex-ante scores in the three markets on a log scale, with high scores in orange and the documented wallets marked at scores 4 to 6.">Score distributions per market (log scale), documented wallets marked. Panel titles give the permutation result.</Fig>
      <Fig src="/figures/timelines.png" w={1600} h={970} n={3} alt="YES price over the last 48 hours before the news in Maduro and 24 hours in Nobel, with buys by high-score wallets and documented wallets overlaid.">Pre-news buys by high-score wallets against the YES price, Maduro (48 h) and Nobel (24 h). Marker area proportional to USD.</Fig>
      <p>The replay below steps through the Maduro market with the frozen screen, showing when each wallet crossed the threshold.</p>
      <figure aria-label="Replay of the Maduro market" className="paper-figure">
        <Replay d={replay}/>
      </figure>
      <p><strong>Two caveats.</strong> Journalists found these wallets by looking at similar patterns, so recall of {distinctNamed} of {distinctNamed} is partly circular. And the screen flagged {others} other wallets that nobody has accused; recall says nothing about precision.</p>
    </Section>

    <Section n="06" id="permutation" title="Does the screen beat chance? Timestamp permutation">
      <p>A high recall could come from the features alone: many buyers are new, small or one-sided whatever their timing. Following Bock and Guenthoer <Source href={SRC.bock}>Bock and Guenthoer</Source>, the null keeps each wallet&apos;s sizes, sides, account age and F2, F4, F5 fixed and redraws every pre-news buy time i.i.d. from the market&apos;s own pre-news activity profile, recomputing F1, F3 (price at the new time) and F6. The statistic is the number of high-score wallets:</p>
      <MathBlock tex={String.raw`p = \frac{1 + \#\{b \le B : N^{(b)}_{\text{high}} \ge N^{\text{obs}}_{\text{high}}\}}{1 + B}, \qquad B = ${n0(nobel.n_perm)}`}/>
      <Table caption="Table 7 · High-score wallets, observed against the timing null"
        head={['Market', 'Observed', 'Null mean', 'Null 95th pct', 'Null range', 'p']}
        rows={ORDER.map(id => {
          const p = byId[id].permutation;
          return [NAME[id], String(p.observed), p.null_mean.toFixed(1), String(p.null_p95), `${p.null_min} to ${p.null_max}`, pv(p.p_value)];
        })}
        main={[ORDER.indexOf('nobel')]}/>
      <p>Only the Nobel market has more high-score wallets than random timing gives ({nobel.observed} against {nobel.null_mean.toFixed(1)} expected, p = {pv(nobel.p_value)}). In Maduro and Iran the count is what the features produce on their own. The screen ranks the named wallets highly, but in two of three markets the overall flag count is not evidence of timed, informed buying.</p>
      <CodeCell title="One permutation draw (src/v1_03_layer1.py)" code={`
fixed = S.flag_F2 + S.flag_F4 + S.flag_F5          # held fixed: sizes, sides, account age
for k in range(N_PERM):                                # 1,000 draws per market
    # F1: first fill = earliest redrawn buy time (sells keep their real times)
    ia = rng.integers(0, len(pool_t), len(allb))
    first = sell_first.copy()
    np.minimum.at(first, aw, pool_t[ia].astype(float))
    f1 = (np.maximum(first - acct, 0) / 86400) <= FLAGS["F1_days"]
    # F3: price paid = the market's YES price path at the redrawn time
    ib = rng.integers(0, len(pool_t), len(b))
    pr = np.where(yes_tok, pool_yes[ib], 1 - pool_yes[ib])
    f3 = np.bincount(bw, shares * pr, nW) / np.bincount(bw, shares, nW) <= FLAGS["F3_price"]
    # F6: USD-weighted median of the redrawn main-side buy times
    f6 = ((T - weighted_median_time(pool_t[ib], usd, bw)) / 3600) <= FLAGS["F6_hours"]
    null[k] = int((fixed + f1 + f3 + f6 >= FLAGS["HIGH"]).sum())`}/>
    </Section>

    <Section n="07" id="precision" title="Precision proxies, sensitivity and price impact">
      <p>True precision needs ground truth the public record does not have. Two post-hoc proxies, never used in the score, compare high-score wallets with other wallets of the same size: whether the main side won (F7) and whether the wallet went dormant in the 30 days after resolution (F8).</p>
      <Table caption="Table 8 · Win rate and dormancy by size band"
        head={['Pre-news buy USD', 'High: n', 'Win', 'Dormant', 'Other: n', 'Win', 'Dormant']}
        rows={bands.map(b => {
          const h = prec(b, true); const o = prec(b, false);
          return [b.replace('>=', '≥ ').replace('<', '< '), n0(h.n), pc(h.win_rate), pc(h.dormant_rate), n0(o.n), pc(o.win_rate), pc(o.dormant_rate)];
        })}
        note="Win: main side was the winning outcome. Dormant: no trades from one to thirty days after resolution."/>
      <p>In every size band high-score wallets win more often, and above $2,500 they also go dormant far more often, both consistent with one-off informed bets. With three markets these are descriptive, not tests.</p>
      <Table caption="Table 9 · Sensitivity of the high-score count to the size threshold (F4)" narrow
        head={['F4 threshold', ...ORDER.map(id => NAME[id])]}
        rows={mk.sensitivity.map(r => [`$${n0(r.F4_threshold)}`, ...ORDER.map(id => String(r[id]))])}
        main={[mk.sensitivity.findIndex(r => r.F4_threshold === th.F4_usd)]}/>
      <p><strong>Price impact.</strong> For taker buys, the direction-signed YES price change per $1,000 over 60 minutes has a median of {imp60.high_median.toFixed(4)} for high-score wallets (n = {imp60.high_n}) against {imp60.other_median.toFixed(4)} for all others (n = {n0(imp60.other_n)}; Mann-Whitney p = {imp60.p_mwu.toFixed(3)}). Against other wallets of at least $2,500 the difference is not significant (p = {imp60.p_mwu_vs_ge2500.toFixed(2)}), so size explains much of it.</p>
    </Section>

    <Section n="08" id="layer2" title="Layer 2: do other traders follow flagged wallets?">
      <p>If flagged wallets carry information, other traders might follow them. Each pre-news buy by a high-score wallet (seed A, buys within 30 min merged) is paired with buys by established wallets (score ≤ 1, at least 10 markets traded) in the same market, within ±30% of its size and ±6 h of its time (seeds B). The outcome is the number of distinct taker wallets trading in the seed&apos;s direction in the next <M tex="H"/> minutes, excluding windows that touch the news ±15 min. For each A seed:</p>
      <MathBlock tex={String.raw`d_a = Y_a - \frac{1}{|\mathcal{B}_a|}\sum_{b \in \mathcal{B}_a} Y_b, \qquad p = \frac{1 + \#\{r : |\bar d^{\,(r)}| \ge |\bar d|\}}{1 + 10{,}000}, \quad \bar d^{\,(r)} = \tfrac{1}{n}\textstyle\sum_a \varepsilon_a^{(r)} d_a`}/>
      <p>with sign flips <M tex={String.raw`\varepsilon_a \in \{-1, +1\}`}/>, a 95% bootstrap interval over A seeds (5,000 resamples) and, because one wallet can contribute many seeds, a wallet-clustered version of the test.</p>
      <Table caption="Table 10 · Follow-on wallets after A seeds minus matched B seeds"
        head={['Scope', 'H', 'A seeds (wallets)', 'Mean A', 'Mean B', 'Difference [95% CI]', 'p', 'Clustered p']}
        rows={[30, 120].flatMap(H => ['pooled', ...ORDER].map(sc => {
          const t = wl(H, sc);
          return [sc === 'pooled' ? 'Pooled' : NAME[sc as MarketId], `${H} min`, `${t.n_A_seeds} (${t.n_A_wallets})`, t.mean_A.toFixed(1), t.mean_B.toFixed(1), `${sg(t.mean_diff, 1)} ${ci(t.ci95[0], t.ci95[1], 1)}`, pv(t.p_signflip), pv(t.wallet_clustered_p)];
        }))}
        main={[0]} rule={[4]} wide
        note={`Excluded for overlapping the news: ${l2.excluded_counts.filter(e => e.kind === 'A').map(e => `${e.n} A seeds at ${e.H} min`).join(', ')}. A seeds with no B match are dropped (${l2.A_seeds_without_B_H30} at 30 min, ${l2.A_seeds_without_B_H120} at 120 min).`}/>
      <Fig src="/figures/layer2.png" w={1600} h={621} n={4} alt="Left: mean difference in follow-on wallets with 95% intervals per market and pooled, at 30 and 120 minutes; Iran and Maduro negative, Nobel positive. Right: followers split into whales, bots and others.">Follow-on after flagged buys against matched ordinary buys, and who follows (whales, bots, others).</Fig>
      <p>Pooled at 30 minutes, flagged buys draw {f(Math.abs(wl(30, 'pooled').mean_diff), 2)} <em>fewer</em> followers than comparable ordinary buys (p = {pv(wl(30, 'pooled').p_signflip)}), and the wallet-clustered test is not significant (p = {pv(wl(30, 'pooled').wallet_clustered_p)}). The direction splits by market: fewer followers in Iran and Maduro, more in Nobel. The crowd does not systematically detect or follow these wallets.</p>
      <CodeCell title="Sign-flip test and bootstrap interval (src/v1_04_layer2.py)" code={`
def signflip(d, n=10000):
    d = np.asarray(d, float)
    obs = abs(d.mean())
    flips = rng.choice([-1, 1], size=(n, len(d)))
    return float((1 + (np.abs((flips * d).mean(1)) >= obs).sum()) / (n + 1))

def boot_ci(d, n=5000):
    d = np.asarray(d, float)
    m = rng.choice(d, size=(n, len(d))).mean(1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]`}/>
    </Section>

    <Section n="09" id="v2" title="Model v2: learning the weights from resolved markets">
      <p>The v1 thresholds are hand-picked. v2 learns weights from outcomes instead, on a pre-registered universe of resolved small-group markets (military and government actions, awards, appointments, central-bank decisions, company announcements; sports, crypto prices and elections excluded by text screen). The unit is a wallet × market × side with a net-long position, trained on {v2.learned.train_markets} markets resolved before the split ({n0(md.n_train_units)} units, {n0(v2.learned.train_wallets)} wallets) and validated on {v2.learned.val_markets} later markets ({n0(md.n_val_units)} units).</p>
      <p>The market price is an offset with coefficient fixed at 1, so the features can only explain what the price paid does not already say:</p>
      <MathBlock tex={String.raw`\operatorname{logit}\Pr(\text{won}_u) = \beta_0 + \sum_{j=1}^{8} \beta_j z_{uj} + \operatorname{logit}(\text{price paid}_u), \qquad \hat\beta = \arg\min_\beta\; -\ell(\beta) + \frac{\lambda}{2}\sum_{j \ge 1}\beta_j^2`}/>
      <p>with standardized features <M tex="z"/> and an unpenalized intercept. The ridge penalty <M tex={`\\lambda = ${md.lam}`}/> was chosen on an inner time split of the training set (log loss {Object.entries(md.lambda_grid).map(([k, v]) => `${k}: ${v.toFixed(4)}`).join(', ')}). Intervals are a bootstrap over training markets (200 resamples).</p>
      <Table caption="Table 11 · Frozen v2 coefficients (per standard deviation)"
        head={['Feature', 'Coefficient', '95% CI']}
        rows={md.all_coefs.map(c => [<code key="c">{c.feature}</code>, sg(c.coef, 4), ci(c.lo, c.hi, 3)])}
        main={md.all_coefs.map((c, i) => c.excludes_zero ? i : -1).filter(i => i >= 0)}
        note="Only conviction has an interval that excludes zero, and its effect is small: wallets that kept their whole position won slightly less often than the price implied."/>
      <p>At the market level, recent buying is aggregated into a signed, score-weighted flow over the last <M tex={`N = ${md.n_hours}`}/> hours and used to shift the market price:</p>
      <MathBlock tex={String.raw`Z_t = \frac{\sum_{i} \operatorname{sign}_i \cdot \text{USD}_i \cdot s_i}{\sum_i \text{USD}_i}, \qquad p^{\text{model}}_t = \sigma\!\left(\operatorname{logit} p^{\text{mkt}}_t + \gamma Z_t\right), \quad \hat\gamma = ${md.gamma.toFixed(2)}`}/>
      <p>The fitted <M tex="\gamma"/> is negative: in training, buying by high-score wallets preceded the opposite outcome. Given the null at unit level it is most likely noise, and it is reported as fitted.</p>
      <Table caption="Table 12 · Out-of-sample validation (Brier score, lower is better)"
        head={['Level', 'n', 'Market price', 'Model', 'Model − market [95% CI]']}
        rows={[
          [`Market snapshots, ${vv.n_markets} markets`, String(vv.n_points), `${vv.brier_market.toFixed(3)} ${ci(vv.brier_market_ci[0], vv.brier_market_ci[1], 3)}`, `${vv.brier_model.toFixed(3)} ${ci(vv.brier_model_ci[0], vv.brier_model_ci[1], 3)}`, `${sg(vv.diff, 3)} ${ci(vv.diff_ci[0], vv.diff_ci[1], 3)}`],
          ['Positions (units)', n0(vv.unit.n_units), vv.unit.brier_market.toFixed(4), vv.unit.brier_model.toFixed(4), ci(vv.unit.diff_ci[0], vv.unit.diff_ci[1], 4)],
        ]}
        main={[0]}
        note="Intervals: bootstrap over validation markets (market level) and clustered by market (unit level)."/>
      <p><strong>The model does not beat the market price.</strong> The Brier difference of {sg(vv.diff, 3)} has an interval that includes zero, and at the position level the two are indistinguishable. Skill also barely persists: the top 5% of wallets in 2025 (n = {ps.n_top}) beat their price by {sg(ps.top_2025 * 100, 1)} points; in 2026 the same group (n = {ps.n_top_2026}) beat it by {sg(ps.top_2026[0] * 100, 1)} points against {sg(ps.others_2026[0] * 100, 1)} for everyone else, a gap of {sg(ps.diff[0] * 100, 1)} points with an interval from {sg(ps.diff[1] * 100, 1)} to {sg(ps.diff[2] * 100, 1)}.</p>
      <CodeCell title="Penalized logistic regression with a price offset, by Newton's method (src/v2_06_analysis.py)" code={`
logit = lambda p: np.log(p / (1 - p)); sig = lambda z: 1 / (1 + np.exp(-z))

def fit(X, y, off, lam, iters=50):
    Xa = np.c_[np.ones(len(X)), X]; w = np.zeros(Xa.shape[1])
    R = lam * np.eye(Xa.shape[1]); R[0, 0] = 0                  # intercept unpenalised
    for _ in range(iters):
        p = sig(Xa @ w + off); g = Xa.T @ (p - y) + R @ w        # gradient of penalised log loss
        H = (Xa * (p * (1 - p))[:, None]).T @ Xa + R + 1e-9 * np.eye(len(w))
        step = np.linalg.solve(H, g); w -= step
        if np.abs(step).max() < 1e-7: break
    return w

Z = lambda df: ((df[FEATS] - mu) / sd).values                     # standardised on training
off = lambda df: logit(df.price.values)                           # market price, coefficient fixed at 1
brier = lambda p, y: float(np.mean((p - y) ** 2))`}/>
    </Section>

    <Section n="10" id="forward" title="Forward test: ten locked predictions">
      <p>The only clean test of v2 is one it cannot have seen. Before selection, the rule was committed: ten open small-group markets ending by 9 December 2026, at least $50,000 volume, price between 0.03 and 0.97, at most one per event, top ten by volume. The model was then run at a single timestamp and the predictions written, hashed and pushed. <strong>Success criterion:</strong> model Brier below market Brier on the markets that resolve; secondary, the hit rate where the two differ by at least 5 points. With n = 10 the test can show an obvious failure or give weak support, not validate the model.</p>
      <Table caption="Table 13 · Locked predictions (probability of Yes)"
        head={['Market', 'Market price', 'Model', 'Status']}
        rows={v2.forward.predictions.map(p => [<span key="q" className="whitespace-normal">{p.question}</span>, pc(p.market, 1), pc(p.model, 1), p.status])}
        note={<>Snapshot {v2.forward.snapshot_utc.replace('T', ' ').replace('Z', ' UTC')}, committed in <a href={v2.forward.commit_url} target="_blank" rel="noreferrer" className="underline underline-offset-2">{v2.forward.commit.slice(0, 7)}</a>. SHA-256 of the locked file: <code className="break-all">{v2.forward.sha256}</code></>}/>
    </Section>

    <Section n="11" id="conclusion" title="Conclusion and limitations">
      <p>A six-flag ex-ante screen, frozen before validation, ranks every publicly named wallet in the high band, including the wallet in the CFTC complaint at 1st of {n0(head.n_in_market)}, {head.hours_before} hours before the news. But the evidence that the screen detects informed timing rather than a common trading style is limited to one market of three under the permutation null, the crowd does not follow flagged wallets, and a model with learned weights does not beat the market price out of sample.</p>
      <ul className="paper-list">
        <li>Three study markets; per-market results do not generalize, and seeds and wallets within a market are not independent.</li>
        <li>Recall is partly circular, since reporters found the named wallets with similar signals; precision cannot be measured without ground truth.</li>
        <li>The screen misses informed traders using established accounts, as in the Google case <Source href={SRC.googleAccount}/>.</li>
        <li>T_news is approximate for Maduro, and the last-trade price stands in for a mid price that is not available historically.</li>
      </ul>
      <p className="paper-callout">{NOT_PROOF} The forward test is scored after the markets resolve, with the result reported whatever it is.</p>
      <p className="paper-links"><a href={REPO} target="_blank" rel="noreferrer">Code, data and rules on GitHub ↗</a></p>
    </Section>

    <section className="paper-section paper-refs" aria-labelledby="sources-title">
      <h2 id="sources-title">Sources</h2>
      <ul>
        {SOURCES.map(s => <li key={s.href}><a href={s.href} target="_blank" rel="noreferrer">{s.name}</a>. {s.what}.</li>)}
      </ul>
    </section>
  </article>;
}
