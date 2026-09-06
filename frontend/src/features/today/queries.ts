import { useQuery } from "@tanstack/react-query";

import { getTodayView } from "./api";

export const todayQueryKeys = {
  view: (timezone: string) => ["task-views", "today", timezone] as const
};

export function useTodayViewQuery() {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  return useQuery({
    queryKey: todayQueryKeys.view(timezone),
    queryFn: () => getTodayView(timezone)
  });
}
