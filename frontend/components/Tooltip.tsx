"use client";

import { useState, useRef, useEffect, ReactNode } from "react";

type TooltipProps = {
  content: string;
  children: ReactNode;
  position?: "top" | "bottom" | "left" | "right";
};

export function Tooltip({ content, children, position = "top" }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const showTooltip = () => {
    timeoutRef.current = setTimeout(() => setVisible(true), 300);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const positionStyles: Record<string, string> = {
    top: "tooltip-bottom",
    bottom: "tooltip-top",
    left: "tooltip-right",
    right: "tooltip-left",
  };

  return (
    <div
      className="tooltip-wrapper"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      {visible && (
        <div className={`tooltip ${positionStyles[position]}`} role="tooltip">
          {content}
        </div>
      )}
    </div>
  );
}

export function HelpIcon({ content }: { content: string }) {
  return (
    <Tooltip content={content} position="right">
      <span className="help-icon" aria-label="Help">?</span>
    </Tooltip>
  );
}