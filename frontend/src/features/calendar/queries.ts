import { useQuery } from "@tanstack/react-query";

import { getCalendarView } from "./api";

export const calendarQueryKeys = {
  all: ["calendar"] as const,
  range: (dateFrom: string, dateTo: string) => ["calendar", dateFrom, dateTo] as const
};

export function useCalendarViewQuery(dateFrom: string, dateTo: string) {
  return useQuery({
    queryKey: calendarQueryKeys.range(dateFrom, dateTo),
    queryFn: () => getCalendarView(dateFrom, dateTo),
    placeholderData: (previousData) => previousData
  });
}
