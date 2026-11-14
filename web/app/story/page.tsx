import type {Metadata} from 'next';
import {Story, type StoryData} from '@/components/app/story';
import {MARKET_IDS, getAlerts, getMarket, getMarkets, getV0, getValidation, getWallets} from '@/lib/data';

export const metadata: Metadata = {title: 'Story'};

export default function StoryPage() {
  const {flags, headline, markets, impact} = getMarkets();
  const val = getValidation();
  const docKeys = new Set(val.map(v => `${v.market}:${v.wallet_id}`));
  const dist = Array.from({length: 7}, (_, score) => ({
    score,
    wallets: markets.reduce((a, m) => a + (m.score_dist[String(score)] ?? 0), 0),
    documented: [...docKeys].filter(k => { const [m, id] = k.split(':'); return val.find(v => v.market === m && v.wallet_id === id)!.score === score; }).length,
  }));
  const top = val.find(v => v.label_id === 'MAD-CFTC-1')!;
  const w = getWallets('maduro').find(x => x.id === top.wallet_id)!;
  const data: StoryData = {
    v0: getV0(),
    dist,
    headline,
    perm: MARKET_IDS.map(id => { const m = getMarket(id)!; return {short: m.short, observed: m.permutation.observed, null_mean: m.permutation.null_mean, p: m.permutation.p_value}; }),
    alert: {wallet: w, market: getMarket('maduro')!, flags, seeds: getAlerts('maduro')[w.id] ?? [], labels: val.filter(v => v.market === 'maduro' && v.wallet_id === w.id), impact},
  };
  return <Story data={data}/>;
}
