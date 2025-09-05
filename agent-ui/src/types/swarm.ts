export interface Team {
  id: string;
  name: string;
  description?: string;
  members?: string[];
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  inputs?: Record<string, any>;
}

export interface ToolCall {
  name: string;
  args?: Record<string, any>;
  result?: any;
}

export interface JudgeDecision {
  decision: 'accept' | 'merge' | 'reject';
  selected?: string;
  runner_instructions?: string[];
  rationale?: string[];
  merged_spec?: Record<string, any>;
}

export interface CriticReview {
  verdict: 'pass' | 'revise';
  findings?: {
    security?: string[];
    data_integrity?: string[];
    logic_correctness?: string[];
    performance?: string[];
    usability?: string[];
    maintainability?: string[];
  };
  must_fix?: string[];
  nice_to_have?: string[];
  minimal_patch_notes?: string;
}

export interface Citation {
  path?: string;
  start_line?: number;
  end_line?: number;
  lang?: string;
  content?: string;
}

export interface StreamResponse {
  token?: string;
  final?: any;
  critic?: CriticReview;
  judge?: JudgeDecision;
  tool_calls?: ToolCall[];
  citations?: Citation[];
  error?: string;
}
