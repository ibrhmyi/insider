'use client';
import {useEffect, useRef} from 'react';

// Faint ASCII swirl behind the page, the same pattern as iyildiz.me/yvonne.
// Adapted from github.com/mattialoszach/ascii-animation-web (MIT).
const CHARS = ['.', ':', '+', '*', 'o', 'O', '#', '%', '@', '$'];

export function Swirl() {
  const ref = useRef<HTMLPreElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let w = 0, h = 0, raf = 0, last = 0;
    const resize = () => {
      w = Math.max(40, Math.ceil(window.innerWidth / 7.2));
      h = Math.max(20, Math.ceil(window.innerHeight / 15));
    };
    const draw = (t: number) => {
      let out = '';
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const fx = (x - w / 2) * 0.04, fy = (y - h / 2) * 0.04;
          const r = Math.sqrt(fx * fx + fy * fy);
          const v = Math.sin(8 * Math.atan2(fy, fx) - r * 3 - t * 0.0015) + (Math.random() - 0.5) * 0.2;
          out += CHARS[Math.max(0, Math.min(CHARS.length - 1, Math.floor(((v + 1) / 2) * (CHARS.length - 1))))];
        }
        out += '\n';
      }
      el.textContent = out;
    };
    // About 24 frames a second is plenty for a background; skip work while the tab is hidden.
    const loop = (t: number) => {
      if (!document.hidden && t - last > 40) { draw(t); last = t; }
      raf = requestAnimationFrame(loop);
    };
    resize();
    window.addEventListener('resize', resize);
    if (reduced) draw(0); else raf = requestAnimationFrame(loop);
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); };
  }, []);
  return <pre ref={ref} aria-hidden="true" className="swirl"/>;
}
