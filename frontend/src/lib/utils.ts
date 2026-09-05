import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatINR(amount: number | string | undefined | null): string {
  if (amount === undefined || amount === null) return "₹0.00";
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(num)) return "₹0.00";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatPercentage(val: number | string | undefined | null): string {
  if (val === undefined || val === null) return "0.0%";
  const num = typeof val === "string" ? parseFloat(val) : val;
  if (isNaN(num)) return "0.0%";
  return `${(num * 100).toFixed(1)}%`;
}

export function formatDateTime(dateStr: string | undefined | null): string {
  if (!dateStr) return "--";
  try {
    const d = new Date(dateStr);
    return new Intl.DateTimeFormat("en-IN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    }).format(d);
  } catch {
    return dateStr;
  }
}
