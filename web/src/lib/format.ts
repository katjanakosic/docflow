const money = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  
  /** 2081.92 → 2’081.92, the Swiss way of writing amounts. */
  export function formatMoney(value: string | number): string {
    return money.format(Number(value)).replaceAll(",", "’");
  }
  
  /** A date without time, like 2026-02-27 → 27.02.2026. */
  export function formatDate(value: string): string {
    return new Date(value).toLocaleDateString("de-CH", { timeZone: "UTC", dateStyle: "medium" });
  }
  
  /** A moment in time, shown in Swiss local time. */
  export function formatDateTime(value: string): string {
    return new Date(value).toLocaleString("de-CH", {
      timeZone: "Europe/Zurich",
      dateStyle: "medium",
      timeStyle: "short",
    });
  }