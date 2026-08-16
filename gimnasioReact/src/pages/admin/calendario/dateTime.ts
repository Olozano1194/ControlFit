// ─── Timezone helpers ─────────────────────────────────────────────────────────
// Backend stores UTC (TIME_ZONE='UTC', USE_TZ=True). Browsers render in the
// user's local zone (e.g. Colombia UTC-5). These helpers bridge both worlds:
// the API always receives UTC ISO; inputs always show LOCAL wall-clock time.

const pad = (n: number): string => String(n).padStart(2, '0');

/**
 * Formats a Date as a local wall-clock value for `datetime-local` inputs
 * (YYYY-MM-DDTHH:mm in the browser's timezone).
 */
export const toLocalInputValue = (date: Date): string => {
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
        date.getHours()
    )}:${pad(date.getMinutes())}`;
};

/**
 * Converts a Date to UTC ISO for the API payload.
 */
export const toApiISO = (date: Date): string => date.toISOString();

/**
 * Normalizes a slot end before prefilling the creation form.
 * react-big-calendar's month view delivers end = next day at 00:00;
 * convert that to 23:59 of the previous day so the event does not
 * spill into the following day.
 */
export const normalizeSlotEnd = (end: Date): Date => {
    const isMidnight =
        end.getHours() === 0 && end.getMinutes() === 0 && end.getSeconds() === 0;
    return isMidnight ? new Date(end.getTime() - 60 * 1000) : end;
};