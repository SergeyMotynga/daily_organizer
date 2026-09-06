import { useQuery } from "@tanstack/react-query";

import { getTodayView } from "./api";

export const todayQueryKeys = {
  all: ["task-views", "today"] as const,
  view: (timezone: string) => [...todayQueryKeys.all, timezone] as const
};

export function useTodayViewQuery() {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  return useQuery({
    queryKey: todayQueryKeys.view(timezone),
    queryFn: () => getTodayView(timezone)
  });
}
