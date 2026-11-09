const money = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  
  /** 2081.92 → 2’081.92, the Swiss way of writing amounts. */
  export function formatMoney(value: string | number): string {
    return money.format(Number(value)).replaceAll(",", "’");
  }
  
/** A date without time: 2026-02-27 → 27.02.2026. */
export function formatDate(value: string): string {
    const [year, month, day] = value.slice(0, 10).split("-");
    return `${day}.${month}.${year}`;
  }
  
  const zurichTime = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Zurich",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });
  
  /** A moment in time in Swiss local time: 08.11.2026, 17:30. */
  export function formatDateTime(value: string): string {
    const parts = Object.fromEntries(
      zurichTime.formatToParts(new Date(value)).map((part) => [part.type, part.value]),
    );
    return `${parts.day}.${parts.month}.${parts.year}, ${parts.hour}:${parts.minute}`;
  }