export interface CacheStatsResponse {
  total: number;
  currentsize: number;
  hits: number;
  misses: number;
  evicted: number;
  [key: string]: number;
}
