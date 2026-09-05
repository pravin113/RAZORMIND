import React, { useEffect, useState, useRef } from "react";

interface AnimatedCounterProps {
  value: number | string;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
  formatFn?: (val: number) => string;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({
  value,
  duration = 900,
  decimals = 0,
  prefix = "",
  suffix = "",
  className = "",
  formatFn,
}) => {
  const numericValue = typeof value === "string" ? parseFloat(value) || 0 : Number(value) || 0;
  const [displayValue, setDisplayValue] = useState<number>(0);
  const startTimestampRef = useRef<number | null>(null);
  const startValRef = useRef<number>(0);
  const targetValRef = useRef<number>(numericValue);

  useEffect(() => {
    startValRef.current = displayValue;
    targetValRef.current = numericValue;
    startTimestampRef.current = null;

    let frameId: number;

    const step = (timestamp: number) => {
      if (!startTimestampRef.current) startTimestampRef.current = timestamp;
      const elapsed = timestamp - startTimestampRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Cubic ease-out
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const current = startValRef.current + (targetValRef.current - startValRef.current) * easeProgress;

      setDisplayValue(current);

      if (progress < 1) {
        frameId = requestAnimationFrame(step);
      } else {
        setDisplayValue(targetValRef.current);
      }
    };

    frameId = requestAnimationFrame(step);

    return () => cancelAnimationFrame(frameId);
  }, [value, duration]);

  const formatted = formatFn
    ? formatFn(displayValue)
    : `${prefix}${displayValue.toLocaleString("en-IN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}${suffix}`;

  return <span className={className}>{formatted}</span>;
};
