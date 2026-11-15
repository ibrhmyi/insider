/** Chart states shared by server and client code (kept out of the 'use client' chart module so server pages get real objects). */
export type ChartState = {
  line: 'none' | 'pre' | 'full';
  dots: 'none' | 'faint' | 'flagged';
  focus: boolean;
  news: boolean;
  callout: boolean;
};

export const STATE_ALL: ChartState = {line: 'full', dots: 'flagged', focus: true, news: true, callout: true};
export const STATE_MARKET: ChartState = {line: 'full', dots: 'flagged', focus: false, news: true, callout: false};
