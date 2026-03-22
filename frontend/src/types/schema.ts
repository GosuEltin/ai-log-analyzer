export interface ErrorCluster {
  label: string;
  count: number;
  services: string[];
  samples: string[];
}

export interface Overview {
  total_lines: number;
  parsed_lines: number;
  failed_lines: number;
  error_count: number;
  top_services: Record<string, number>;
}

export interface ActionCheck {
  title: string;
  tool: string;
  args: Record<string, any>;
  command: string;
  purpose: string;
  priority: number;
  category: string;
  platform: string;
}

export interface ToolExecutionResult {
  title: string;
  tool: string;
  args: Record<string, any>;
  success: boolean;
  output: string;
  error: string | null;
  priority: number;
  category: string;
}

export interface AnalysisResult {
  overview: Overview;
  clusters: ErrorCluster[];
  probable_causes: string[];
  recommendations: string[];
  evidence: string[];
  summary: string;
  retrieved_knowledge: string[];
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN" | string;
  action_checks: ActionCheck[];
  executed_actions: ToolExecutionResult[];
  final_summary: string;
  final_diagnosis: string[];
}

export interface AnalyzeResponse {
  success: boolean;
  filename: string;
  result: AnalysisResult;
}
