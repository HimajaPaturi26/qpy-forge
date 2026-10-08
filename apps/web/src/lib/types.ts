export type Diagnostic = {
  code: string;
  stage: string;
  severity: string;
  support: string;
  message: string;
  line: number;
  col: number;
};

export type TokenInfo = {
  kind: string;
  text: string;
  line: number;
  col: number;
  lit_type: string | null;
  null: boolean;
};

export type Translation = {
  source: string;
  support: string;
  features: string[];
  tokens: TokenInfo[];
  python: string;
  maps: Array<{ python_line: number; q_line: number; q_col: number }>;
  diagnostics: Diagnostic[];
  stages: Record<string, string>;
  ast: unknown;
  ir: unknown;
  oracle: OracleStatus;
};

export type Validation = Translation & {
  executed: boolean;
  matched: boolean | null;
  signal: string | null;
  display: string;
  canon: unknown;
  expected: unknown;
  expected_signal: string | null;
  comparison: string;
};

export type OracleStatus = {
  available: boolean;
  status: string;
  reason: string;
  binary?: string;
  license_env_present?: boolean;
};

export type CorpusCase = {
  id: string;
  split: string;
  support: string;
  source: string;
  features?: string[];
  expected?: unknown;
  expected_signal?: string | null;
  expect_support?: string;
  note?: string;
};

export type ConstructMetric = {
  feature: string;
  n: number;
  matched: number;
  rate: number | null;
};

export type MetricsReport = {
  corpus_version: string;
  corpus_hash: string;
  corpus_counts: { all: number; holdout: number; dev: number; coverage: number };
  split: string;
  commit: string;
  target: number;
  sample_size: number;
  successes: number;
  semantic_accuracy: number | null;
  wilson_low: number;
  wilson_high: number;
  target_met: boolean;
  parse_rate: number | null;
  translation_rate: number | null;
  compile_rate: number | null;
  runtime_success_rate: number | null;
  value_match_rate: number | null;
  oracle_match_rate: number | null;
  oracle: OracleStatus;
  constructs: ConstructMetric[];
  failure_categories: Array<{ category: string; count: number }>;
  top_failures: Array<{
    id: string;
    source: string;
    failure: string;
    signal: string | null;
    display: string;
  }>;
  history: Array<{
    id: number;
    created_at: string;
    corpus_version: string;
    corpus_hash: string;
    commit: string;
    semantic_accuracy: number | null;
    sample_size: number | null;
    target_met: boolean | null;
  }>;
};

export type HistoryEvent = {
  id: number;
  created_at: string;
  kind: string;
  source: string;
  status: string;
  support: string;
  payload?: unknown;
};

export type StatusPayload = {
  version: string;
  oracle: OracleStatus;
  corpus: {
    version: string;
    target: number;
    hash: string;
    counts: { all: number; holdout: number; dev: number; coverage: number };
  };
  sandbox: {
    user_runs: string;
    limits: { timeout_seconds: number; cpu_seconds: number; address_space_bytes: number };
  };
  support_levels: string[];
};
