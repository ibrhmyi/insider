import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import 'katex/dist/katex.min.css';
import './paper.css';
import {Replay, type ReplayData} from '@/components/product/replay';
import {Source} from '@/components/product/research';
import {CodeCell, M, MathBlock, Section, Table} from '@/components/product/paper';
import {FollowChart, PermutationChart} from '@/components/product/paper-charts';
import {getLayer2, getValidation, getMarkets, getV0, getV2} from '@/lib/data';
import {FLAGS, FLAG_SHORT, NOT_PROOF} from '@/lib/copy';
import {CASES, FEATURE_DEFS, SOURCES, SRC, WHERE} from '@/lib/research';
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
const ci = (a: number, b: number, d = 2) => `${f(a, d)} to ${f(b, d)}`;

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
  const [soldier] = CASES;
  const [allMk, , military] = WHERE;
  const thr: Record<FlagId, string> = {
    F1: `≤ ${th.F1_days} days`, F2: `≥ ${pc(th.F2_share)} or ≤ ${th.F2_markets} markets`, F3: `≤ ${th.F3_price * 100}¢`,
    F4: `≥ $${n0(th.F4_usd)}`, F5: `≥ ${th.F5_conv}`, F6: `≤ ${th.F6_hours} h`,
  };
  const wl = (H: number, scope: string) => l2.tests.find(t => t.outcome === 'wallets' && t.H === H && t.scope === scope)!;
  const pooled = wl(30, 'pooled');
  const vv = v2.validation;
  const md = v2.model;
  const conv = md.all_coefs.find(c => c.feature === 'conviction')!;
  const nobel = byId.nobel.permutation;
  const beat = ORDER.filter(id => byId[id].permutation.p_value < 0.05).length;
  const big = mk.precision.find(p => p.size_band === '>=10k' && p.is_high)!;
  const bigOther = mk.precision.find(p => p.size_band === '>=10k' && !p.is_high)!;

  return <article id="top" className="paper">
    <a href="/research/" className="paper-back">← Research</a>

    <header className="paper-head">
      <p className="paper-meta"><time dateTime="2026-11-14">11.2026</time> · Capstone · Python</p>
      <h1 className="paper-title">Detecting Potential Insider Trading on Polymarket</h1>
      <p className="paper-lede">Every trade on Polymarket is public, but the screens that look for informed trading only run after a market has resolved. I wanted to know whether a simple screen, using only what is visible before the news, could point at the right wallets while a market is still open, and whether that holds up once chance is taken into account.</p>
    </header>

    <div className="paper-stats" role="list" aria-label="Key results">
      <div role="listitem"><span className="stat-value">1st<small>/ {n0(head.n_in_market)}</small></span><span className="stat-label">Rank of the charged wallet</span></div>
      <div role="listitem"><span className="stat-value">{distinctNamed} / {distinctNamed}</span><span className="stat-label">Named wallets flagged</span></div>
      <div role="listitem"><span className="stat-value">{beat} / {ORDER.length}</span><span className="stat-label">Markets that beat chance</span></div>
      <div role="listitem"><span className="stat-value">{vv.verdict}</span><span className="stat-label">Learned model beats the price</span></div>
    </div>

    <Section n="01" id="question" title="The question">
      <p>In 2026 US regulators brought their first insider trading cases on prediction markets. In one, a {soldier.who} is charged with making {soldier.made} by betting on the raid on Maduro before it happened <Source href={soldier.source}>CFTC</Source>. Charged is not convicted, but the case shows the problem: whoever takes the other side of a bet like that loses.</p>
      <p>The evidence is in the open. Every trade settles on a public blockchain with its time, wallet, side, size and price <Source href={SRC.polymarketDocs}>Polymarket docs</Source>. Who owns a wallet is not public. The published screens work after a market resolves and don&apos;t release the wallets they flag <Source href={SRC.bock}>Bock and Guenthoer</Source> <Source href={SRC.nechepurenko}>Nechepurenko</Source>.</p>
      <p>So the question is whether a screen built only from pre-news data can rank the wallets later named in public reporting near the top, and whether that ranking is better than chance. A high score here means unusual activity worth a look. It never identifies an owner.</p>
    </Section>

    <Section n="02" id="data" title="Data and design">
      <p>I studied three resolved markets where a small group could know the answer early, labelled from their resolution rules alone: the Iran strike, Maduro leaving office and the Nobel Peace Prize. For each I pulled every fill from the Polymarket Data API and fixed T_news, the time of the first public report. Only trades before T_news are used to score a wallet.</p>
      <Table caption="Table 1 · Markets"
        head={['Market', 'T_news (UTC)', 'Pre-news buyers', 'Volume']}
        rows={ORDER.map(id => {
          const m = byId[id];
          return [m.question, m.t_news_utc.replace('T', ' ').replace(':00Z', ''), n0(m.n_wallets), `$${(m.volume_usd / 1e6).toFixed(1)}M`];
        })}/>
      <p>Each step was frozen in a committed rule file before I looked at the data it would be judged on: the market labels, the first detector, the wallet screen and its tests, and later the learned model and its forward test. Those files and their commit times are in the repository, and they are the main reason to trust the results below.</p>
    </Section>

    <Section n="03" id="v0" title="A first idea that didn't work">
      <p>My first guess was that big bets would draw copycats in markets where insiders are possible. After each large trade I counted the wallets that traded the same way in the next 30 minutes and compared that with matched ordinary moments in the same market, then compared insider-possible markets with two Bitcoin price markets where nobody can know the answer early.</p>
      <p>There was no real difference: {v0.pooled['insider-possible'].mean_excess} extra wallets against {v0.pooled['insider-impossible'].mean_excess} in the controls, p = {v0.p_value.toFixed(2)}. Market-wide herding was the wrong signal, so I moved from markets to wallets.</p>
    </Section>

    <Section n="04" id="screen" title="The wallet screen">
      <p>Public cases share a trading pattern: a new account, money on one event, a long shot bought big, close to the news <Source href={SRC.acdcOrcas}>ACDC</Source> <Source href={SRC.gomezCram}>Gomez-Cram et al.</Source>. Markets like these are where it pays: big long shots win {military.pct}% of the time in military markets against {allMk.pct}% overall <Source href={SRC.acdcMarkets}>ACDC</Source>. I turned the pattern into six yes-or-no flags for every wallet that bought before the news, with thresholds taken from that research before I scored anything:</p>
      <Table caption="Table 2 · The six flags"
        head={['Flag', 'Measured as', 'Yes when']}
        rows={FLAGS.map(k => [FLAG_SHORT[k], <span key="d" className="whitespace-normal">{FEATURE_DEFS[k]}</span>, thr[k]])}/>
      <MathBlock tex={String.raw`S_w = \sum_{k=1}^{6} \mathbb{1}\left[\text{flag } k \text{ fires for wallet } w\right], \qquad \text{worth a look if } S_w \ge ${th.HIGH}`}/>
      <p>Whether the wallet&apos;s side won, and whether it went quiet afterwards, are never part of the score. I only use them to check it.</p>
      <CodeCell title="Computing the flags for one market (src/v1_03_layer1.py)" code={`
pre = f[(f.timestamp < T) & (~f.after_resolution)]           # only trades before the news
for w, g in pre.groupby("proxy_wallet", sort=False):
    b = g[g.side == "BUY"]
    main = int(b.groupby("outcome_index").usd.sum().idxmax())  # the side it bought most
    bm = b[b.outcome_index == main]
    f1 = max(first_m - acct, 0) / 86400                        # account age at first fill, days
    vwap = bm.usd.sum() / bm["size"].sum()                     # price paid
    conv = abs((g.dir * g.usd).sum()) / g.usd.sum()            # how one-sided its trading was
    hrs = (T - wmedian_time(bm.timestamp.values, bm.usd.values)) / 3600
    fl = dict(F1=f1 <= FLAGS["F1_days"],
              F2=share >= FLAGS["F2_share"] or nmk <= FLAGS["F2_markets"],
              F3=vwap <= FLAGS["F3_price"], F4=b.usd.sum() >= FLAGS["F4_usd"],
              F5=conv >= FLAGS["F5_conv"], F6=hrs <= FLAGS["F6_hours"])
    score = int(sum(fl.values()))`}/>
    </Section>

    <Section n="05" id="validation" title="Does it find the named wallets?">
      <p>I collected every wallet named in public reporting for these markets, from a CFTC complaint, Lookonchain, Bloomberg, the WSJ and ACDC. A wallet only counts if the reported handle or address matches it exactly, and none was added because the screen liked it.</p>
      <Table caption="Table 3 · Named wallets"
        head={['Report', 'Status', 'Score', 'Rank', 'Flagged before news', 'Source']}
        rows={val.map(v => [v.label_id, v.confidence, `${v.score} / 6`, `${v.rank} of ${n0(v.n)}`, `${v.first_high_h} h`, <Source key="s" href={v.source}/>])}
        main={val.map((v, i) => v.confidence === 'charged' ? i : -1).filter(i => i >= 0)}
        note={`${val.length} reports cover ${distinctNamed} wallets; two reports name the same Maduro wallet.`}/>
      <p>All {distinctNamed} score {th.HIGH} or more. The wallet in the CFTC complaint scores 6 of 6 and ranks <strong>1st of {n0(head.n_in_market)}</strong> buyers, and it would have been flagged <strong>{head.hours_before} hours</strong> before the news. The replay steps through that market as the screen would have seen it.</p>
      <figure aria-label="Replay of the Maduro market" className="paper-figure">
        <Replay d={replay}/>
      </figure>
      <p>This is less than it sounds. Reporters found these wallets by looking for similar patterns, so finding all of them is partly circular, and the screen also flagged {others} wallets nobody has accused. Among bets over $10,000, flagged wallets won {pc(big.win_rate)} of the time against {pc(bigOther.win_rate)} for the rest, which is suggestive but not proof of anything.</p>
    </Section>

    <Section n="06" id="chance" title="Is it better than chance?">
      <p>Many buyers are new, small or one-sided regardless of when they trade, so a high count could come from the flags alone. To test that, I kept each wallet&apos;s sizes and sides fixed and redrew its buy times at random from the market&apos;s own trading activity, recomputing the timing-dependent flags, {n0(nobel.n_perm)} times per market <Source href={SRC.bock}>Bock and Guenthoer</Source>:</p>
      <MathBlock tex={String.raw`p = \frac{1 + \#\{\text{shuffles with at least as many flagged wallets as observed}\}}{1 + ${nobel.n_perm}}`}/>
      <figure className="paper-figure">
        <PermutationChart markets={ORDER.map(id => byId[id])}/>
        <figcaption><b>Fig. 1</b>Flagged wallets under {n0(nobel.n_perm)} random timings (grey) against the real count (white line).</figcaption>
      </figure>
      <p>Only the Nobel market beats chance: {nobel.observed} flagged wallets against about {Math.round(nobel.null_mean)} expected, p = {pv(nobel.p_value)}. In Maduro and Iran the flags produce roughly the real count on their own. So the screen ranks the right wallets near the top, but in two of the three markets the overall pattern is not evidence of well-timed buying.</p>
      <CodeCell title="One random timing (src/v1_03_layer1.py, simplified)" code={`
fixed = S.flag_F2 + S.flag_F4 + S.flag_F5        # sizes and sides stay as they were
for k in range(N_PERM):
    ib = rng.integers(0, len(pool_t), len(b))      # new buy times, drawn from the market's own activity
    pr = np.where(yes_tok, pool_yes[ib], 1 - pool_yes[ib])
    f3 = np.bincount(bw, shares * pr, nW) / np.bincount(bw, shares, nW) <= FLAGS["F3_price"]
    f1 = account_age_at(first_redrawn_buy) <= FLAGS["F1_days"]
    f6 = hours_before_news(weighted_median(pool_t[ib])) <= FLAGS["F6_hours"]
    null[k] = int((fixed + f1 + f3 + f6 >= FLAGS["HIGH"]).sum())`}/>
    </Section>

    <Section n="07" id="follow" title="Do other traders follow them?">
      <p>If flagged wallets know something, others might pile in after them. I paired each buy by a flagged wallet with buys of a similar size, within six hours, by established wallets in the same market, and counted the wallets that traded the same way in the next 30 minutes.</p>
      <figure className="paper-figure">
        <FollowChart rows={['pooled', ...ORDER].map(sc => {
          const t = wl(30, sc);
          return {label: sc === 'pooled' ? 'All markets' : NAME[sc as MarketId], diff: t.mean_diff, lo: t.ci95[0], hi: t.ci95[1], main: sc === 'pooled'};
        })}/>
        <figcaption><b>Fig. 2</b>Extra followers after a flagged buy, compared with a matched ordinary buy, with 95% intervals.</figcaption>
      </figure>
      <p>They don&apos;t. Overall, flagged buys drew {f(Math.abs(pooled.mean_diff), 1)} fewer followers ({ci(pooled.ci95[0], pooled.ci95[1], 1)}), and once I account for the same wallet appearing many times the difference is not significant (p = {pooled.wallet_clustered_p.toFixed(2)}). The direction also flips between markets: fewer followers in Iran and Maduro, more in Nobel.</p>
    </Section>

    <Section n="08" id="v2" title="Letting the data choose the weights">
      <p>The six thresholds were my choices. Next I let outcomes choose: I took {v2.learned.train_markets} resolved small-group markets (wars, awards, appointments, rate decisions, company news) and fitted a logistic regression on {n0(md.n_train_units)} wallet positions. The market price goes in as an offset, so the features only get credit for what the price did not already know:</p>
      <MathBlock tex={String.raw`\operatorname{logit} P(\text{win}) = \beta_0 + \textstyle\sum_j \beta_j z_j + \operatorname{logit}(\text{price paid})`}/>
      <p>I used a ridge penalty, <M tex={`\\lambda = ${md.lam}`}/>, chosen on an earlier slice of the training data, and bootstrapped the coefficients over markets.</p>
      <Table caption="Table 4 · Learned weights (per standard deviation)"
        head={['Feature', 'Weight', '95% interval']}
        rows={md.all_coefs.map(c => [<code key="c">{c.feature}</code>, sg(c.coef, 4), ci(c.lo, c.hi, 2)])}
        main={md.all_coefs.map((c, i) => c.excludes_zero ? i : -1).filter(i => i >= 0)}/>
      <p>Only one weight is clearly different from zero, and it is small: wallets that held their whole position won slightly less often than the price said ({sg(conv.coef, 2)}). On {v2.learned.val_markets} later markets the model was no better than the market price. Its Brier score was {vv.brier_model.toFixed(3)} against {vv.brier_market.toFixed(3)}, a difference of {sg(vv.diff, 3)} with an interval from {sg(vv.diff_ci[0], 3)} to {sg(vv.diff_ci[1], 3)}.</p>
      <CodeCell title="Fitting the model (src/v2_06_analysis.py)" code={`
def fit(X, y, off, lam, iters=50):
    Xa = np.c_[np.ones(len(X)), X]; w = np.zeros(Xa.shape[1])
    R = lam * np.eye(Xa.shape[1]); R[0, 0] = 0            # don't penalise the intercept
    for _ in range(iters):                                  # Newton's method
        p = sig(Xa @ w + off); g = Xa.T @ (p - y) + R @ w
        H = (Xa * (p * (1 - p))[:, None]).T @ Xa + R
        step = np.linalg.solve(H, g); w -= step
        if np.abs(step).max() < 1e-7: break
    return w

off = lambda df: logit(df.price.values)                    # the price, with its weight fixed at 1`}/>
    </Section>

    <Section n="09" id="forward" title="Ten predictions, locked in advance">
      <p>Validation on past markets can be fooled by choices made along the way, so the real test is one the model has not seen. I wrote the selection rule first, then picked the ten largest open small-group markets ending before 10 December, ran the model once and committed the predictions with a hash. It passes if its Brier score beats the market price on the markets that resolve. With ten markets this can catch an obvious failure but cannot prove the model works.</p>
      <Table caption="Table 5 · Locked predictions (chance of Yes)"
        head={['Market', 'Price', 'Model', 'Result']}
        rows={v2.forward.predictions.map(p => [p.question, pc(p.market, 1), pc(p.model, 1), p.status])}
        note={<>Locked {v2.forward.snapshot_utc.slice(0, 10)} in commit <a href={v2.forward.commit_url} target="_blank" rel="noreferrer" className="underline underline-offset-2">{v2.forward.commit.slice(0, 7)}</a>.</>}/>
    </Section>

    <Section n="10" id="conclusion" title="What I take away">
      <p>A simple screen, fixed before I tested it, put every publicly named wallet in its top band, including the one in the CFTC complaint at 1st of {n0(head.n_in_market)}, {head.hours_before} hours early. But only {beat === 1 ? 'one market' : `${beat} markets`} of three beats random timing, other traders don&apos;t follow flagged wallets, and learned weights don&apos;t beat the price.</p>
      <p>The limits are real: three markets, labels that are partly circular, no way to measure false positives, and nothing to catch someone using an old account, as in the Google case <Source href={SRC.googleAccount}/>. The forward test will be scored when its markets resolve, whatever the result.</p>
      <p className="paper-callout">{NOT_PROOF}</p>
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
