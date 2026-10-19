export interface BrandGapItem {
  brand: string;
  n_reviews: number;
  avg_rating: number;
  merit_score: number;
  norm_name: string;
  brand_key: string | null;
  mentions: number;
  avg_rank: number | null;
  coverage: number;
  visibility_index: number;
  merit_pct: number;
  gap: number | null;
  label: 'under-visible' | 'over-visible' | 'invisible' | 'aligned' | 'low-evidence';
}

export interface BrandVisibilityItem {
  brand_key: string;
  mentions: number;
  avg_rank: number;
  n_providers: number;
  n_personas: number;
  coverage: number;
  pos_weighted: number;
  share_of_voice: number;
  visibility_index: number;
  brand_canonical: string;
  match_method: string;
  merit_category: string;
  merit_n_reviews: number | null;
  merit_score: number | null;
  merit_percentile: number | null;
  brand: string;
}

export interface LeaderboardBrandItem {
  category: string;
  rank: number;
  brand_canonical: string;
  n_products: number;
  merit_score: number;
  merit_raw: number;
  n_reviews: number;
  avg_rating: number;
  recency_weighted_rating: number;
  recency_factor: number;
  avg_sentiment: number;
  pct_positive: number;
  pct_neutral: number;
  pct_negative: number;
}

export interface LeaderboardProductItem {
  category: string;
  rank: number;
  parent_asin: string;
  product_title: string;
  store: string;
  merit_score: number;
  merit_raw: number;
  n_reviews: number;
  avg_rating: number;
  recency_weighted_rating: number;
  recency_factor: number;
  avg_sentiment: number;
  pct_positive: number;
  pct_neutral: number;
  pct_negative: number;
}

export interface MonthlyTrendItem {
  category: string;
  month: string;
  n_reviews: number;
  avg_rating: number;
  avg_sentiment: number;
}

export interface ProbingResponseItem {
  provider: string;
  model: string;
  category: string;
  query_id: string;
  intent: string;
  prompt: string;
  response_text: string;
  product_mentions?: unknown[];
  prompt_id: string;
  base_query_id: string;
  persona: string;
  target_brands: string[];
  comparison_brands?: string[] | null;
}

export interface RejectedEntityItem {
  provider: string;
  prompt_id: string;
  raw: string;
  method: string;
}

export interface PipelineSummary {
  pipeline: string;
  status: string;
  categories: string[];
  tables: Record<string, { rows: number }>;
  exports: Record<string, { exists: boolean; size_bytes: number }>;
  merit: {
    product: Record<string, { total_entities: number; ranked_entities: number }>;
    brand: Record<string, { total_entities: number; ranked_entities: number }>;
  };
}
