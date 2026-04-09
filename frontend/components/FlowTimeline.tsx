"use client";

import { useEffect, useRef, useState } from "react";

export function FlowTimeline({ steps }: { steps: string[] }) {
  const refs = useRef<Array<HTMLDivElement | null>>([]);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => (a.intersectionRatio < b.intersectionRatio ? 1 : -1));
        if (visible[0]) {
          const idx = Number(visible[0].target.getAttribute("data-step-idx") || 0);
          setActive(idx);
        }
      },
      { threshold: [0.3, 0.5, 0.7] },
    );

    refs.current.forEach((node) => node && observer.observe(node));
    return () => observer.disconnect();
  }, [steps.length]);

  return (
    <div className="flow-timeline">
      {steps.map((step, idx) => (
        <div
          key={step}
          ref={(node) => {
            refs.current[idx] = node;
          }}
          data-step-idx={idx}
          className={`flow-step ${active === idx ? "active" : ""}`}
        >
          <span className="flow-step-no">{String(idx + 1).padStart(2, "0")}</span>
          <p>{step}</p>
        </div>
      ))}
    </div>
  );
}

