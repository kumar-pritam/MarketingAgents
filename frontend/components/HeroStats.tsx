"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type StatItem = { label: string; value: number; suffix?: string };

export function HeroStats({ items }: { items: StatItem[] }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [started, setStarted] = useState(false);
  const [counts, setCounts] = useState<number[]>(items.map(() => 0));

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setStarted(true);
          obs.disconnect();
        }
      },
      { threshold: 0.3 },
    );
    obs.observe(node);
    return () => obs.disconnect();
  }, []);

  const targets = useMemo(() => items.map((item) => item.value), [items]);

  useEffect(() => {
    if (!started) return;
    const start = performance.now();
    const duration = 1000;
    let raf = 0;

    function tick(now: number) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCounts(targets.map((target) => Math.round(target * eased)));
      if (progress < 1) raf = requestAnimationFrame(tick);
    }

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [started, targets]);

  return (
    <div ref={ref} className="hero-stats-row">
      {items.map((item, idx) => (
        <div key={item.label} className="hero-stat">
          <p className="hero-stat-value">
            {counts[idx]}
            {item.suffix || ""}
          </p>
          <p className="hero-stat-label">{item.label}</p>
        </div>
      ))}
    </div>
  );
}

