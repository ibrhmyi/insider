import {Story, type StoryData} from '@/components/one/story';
import {getBuys, getMarket, getMarkets, getTimeline, getValidation, getWallets} from '@/lib/data';

const CHARGED = 'MAD-CFTC-1';
const REPO = 'https://github.com/ibrhmyi/insider';

export default function Home() {
  const {headline: h} = getMarkets();
  const m = getMarket('maduro')!;
  const tl = getTimeline('maduro'), bf = getBuys('maduro');
  const label = getValidation().find(v => v.label_id === CHARGED)!;
  const w = getWallets('maduro').find(x => x.id === label.wallet_id)!;
  const x0 = m.t_news - 48 * 3600;
  const me = bf.wallets.findIndex(x => x.id === w.id);

  const d: StoryData = {
    chart: {
      price: tl.price, tNews: m.t_news, x1: tl.resolution_epoch,
      others: bf.buys.filter(b => b[0] >= x0 && b[3] !== me).map(([t, y, usd]) => [t, y, usd]),
      // all of the wallet's pre-news buys as one dot: at its USD-weighted median buy time and its average price
      dot: {t: m.t_news - w.hours * 3600, y: w.avg_price, label: `$${Math.round(w.usd).toLocaleString('en-US')} at ${Math.round(w.avg_price * 100)}¢`},
    },
    signs: [
      {word: 'New account', value: `${w.f1_days.toFixed(1)} days`},
      {word: 'All-in', value: `${Math.round((w.f2_share ?? 0) * 100)}% on one market`},
      {word: 'Cheap', value: `${Math.round(w.avg_price * 100)}¢`},
      {word: 'Big', value: `$${Math.round(w.usd).toLocaleString('en-US')}`},
      {word: 'One-way', value: `${Math.round(w.f5 * 100)}%`},
      {word: 'Early', value: `${w.hours.toFixed(1)} h before news`},
    ],
    source: label.source,
    rank: h.rank, n: h.n_in_market, hoursEarly: h.hours_before, named: h.documented_flagged, namedTotal: h.documented_total,
    othersFlagged: h.n_high_total - h.documented_total,
    repo: REPO,
  };
  return <Story d={d}/>;
}
