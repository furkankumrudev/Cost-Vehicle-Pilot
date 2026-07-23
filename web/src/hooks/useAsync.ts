import { useEffect, useState } from "react";

export function useAsync<T>(factory: () => Promise<T>, dependencies: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    factory().then((result) => active && setData(result)).catch((reason: Error) => active && setError(reason.message)).finally(() => active && setLoading(false));
    return () => { active = false; };
  // The caller supplies stable dependencies for each endpoint request.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
  return { data, loading, error };
}
