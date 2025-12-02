import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

export function useAuthCheck() {
  const { setUser, setLoading } = useAuthStore();

  const { data, isLoading, error } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: api.auth.me,
    staleTime: Infinity,
    retry: false,
  });

  useEffect(() => {
    if (isLoading) {
      setLoading(true);
    } else if (data) {
      setUser(data);
      setLoading(false);
    } else {
      setUser(null);
      setLoading(false);
    }
  }, [data, isLoading, setUser, setLoading]);

  return { user: data || null, loading: isLoading, error };
}
