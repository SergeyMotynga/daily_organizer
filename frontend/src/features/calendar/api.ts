import type { CalendarViewResponse } from "../../entities/task/types";
import { apiRequest } from "../../shared/api";

export function getCalendarView(
  dateFrom: string,
  dateTo: string
): Promise<CalendarViewResponse> {
  const searchParams = new URLSearchParams({ date_from: dateFrom, date_to: dateTo });
  return apiRequest<CalendarViewResponse>(`/calendar?${searchParams.toString()}`);
}
