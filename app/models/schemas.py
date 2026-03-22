from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class LogRecord(BaseModel):
    timestamp: Optional[str] = None
    level: str = "UNKNOWN"
    service: str = "unknown-service"
    message: str
    raw: str


class ErrorCluster(BaseModel):
    label: str
    count: int
    services: List[str]
    samples: List[str]


class Overview(BaseModel):
    total_lines: int
    parsed_lines: int
    failed_lines: int
    info_count: int
    warn_count: int
    error_count: int
    top_services: Dict[str, int]
    failed_lines_content: List[str] = []


class ActionCheck(BaseModel):
    title: str
    tool: str
    args: Dict[str, Any]
    command: str
    purpose: str
    priority: int
    category: str
    platform: str = "linux"


class ToolExecutionResult(BaseModel):
    title: str
    tool: str
    args: Dict[str, Any]
    success: bool
    output: str
    error: Optional[str] = None
    priority: int
    category: str


class AnalysisResult(BaseModel):
    overview: Overview
    clusters: List[ErrorCluster]
    probable_causes: List[str]
    recommendations: List[str]
    evidence: List[str]
    summary: str
    retrieved_knowledge: List[str] = []
    severity: str = "LOW"
    action_checks: List[ActionCheck] = []
    executed_actions: List[ToolExecutionResult] = []
    final_summary: str = ""
    final_diagnosis: List[str] = []
    translated_query: str = ""


class AnalyzeResponse(BaseModel):
    success: bool
    filename: str
    result: AnalysisResult