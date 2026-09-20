import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Poll a fetcher on an interval while active.
 * - interval is clamped to 1000..5000 ms
 * - the latest fetcher closure is used on every tick (timer is not reset on re-render)
 * - errors are swallowed into `error` (fetch failures must not break the UI)
 * - `refresh()` forces a tick immediately (also works while inactive)
 */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  opts: { intervalMs?: number; isActive?: boolean } = {},
) {
  const { intervalMs = 3000, isActive = true } = opts;
  const clamped = Math.min(5000, Math.max(1000, intervalMs));
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const tick = useCallback(async () => {
    try {
      setError("");
      const d = await fetcherRef.current();
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isActive) return;
    void tick();
    const t = setInterval(() => void tick(), clamped);
    return () => clearInterval(t);
  }, [isActive, clamped, tick]);

  return { data, error, loading, refresh: tick };
}