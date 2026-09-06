import { apiRequest } from "../../shared/api";
import type { TodayViewResponse } from "./types";

export function getTodayView(timezone: string): Promise<TodayViewResponse> {
  const searchParams = new URLSearchParams({ timezone });

  return apiRequest<TodayViewResponse>(`/task-views/today?${searchParams.toString()}`);
}
