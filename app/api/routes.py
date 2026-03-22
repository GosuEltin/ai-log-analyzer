from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
import os
import re

from app.models.schemas import AnalyzeResponse
from app.services.parser import parse_log_text
from app.services.analyzer import (
    build_overview,
    build_clusters,
    derive_probable_causes,
    derive_recommendations,
    collect_evidence,
    derive_severity,
    derive_action_checks,
)
from app.services.llm_service import (
    generate_incident_summary,
    generate_final_incident_report,
    translate_query_to_english,
)
from app.services.rag_service import retrieve_knowledge
from app.services.tool_executor import execute_action_checks
from app.services.investigation_focus import (
    detect_focus_mode,
    filter_clusters_by_focus,
    filter_list_by_focus,
    filter_action_checks_by_focus,
    annotate_issue_roles,
)

router = APIRouter()


def _extract_line_limit(query: str) -> int | None:
    """Extract line limit from user query.
    
    Supports patterns like:
      - Vietnamese: '100 dòng đầu', '1 dòng đầu', 'phân tích 50 dòng', '200 dòng đầu tiên', 'dòng đầu' (default 1)
      - English:    'first 100 lines', 'top 50 lines', 'analyze 200 lines', 'only 100 lines', 'first line' (default 1)
    """
    if not query:
        return None
    q = query.lower().strip()
    
    # Vietnamese patterns with number: "100 dòng đầu", "1 dòng đầu", "phân tích 50 dòng"
    m = re.search(r'(\d+)\s*dòng', q)
    if m:
        return int(m.group(1))
    
    # Vietnamese pattern WITHOUT number: "dòng đầu", "dòng đầu tiên" → default to 1
    if re.search(r'dòng\s*(?:đầu|đầu\s*tiên)', q):
        return 1
    
    # English patterns with number: "first 100 lines", "top 200 lines", "only 50 lines", "analyze 100 lines"
    # Support both singular "line" and plural "lines"
    m = re.search(r'(?:first|top|only|analyze|check|scan|read)\s+(\d+)\s+lines?', q)
    if m:
        return int(m.group(1))
    
    # English pattern WITHOUT number: "first line", "top line" → default to 1
    if re.search(r'(?:first|top|only|analyze|check|scan|read)\s+lines?', q):
        return 1
    
    # "100 lines" at the start or standalone
    m = re.search(r'(\d+)\s+lines?', q)
    if m:
        return int(m.group(1))
    
    return None



@router.get("/")
def root():
    index_path = os.path.join(os.getcwd(), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Log Analyzer Backend is running, but index.html was not found in root."}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/analyze-log", response_model=AnalyzeResponse)
async def analyze_log(
    file: UploadFile = File(...),
    user_query: str = Form(""),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Thiếu tên file.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File rỗng.")

    text = content.decode("utf-8", errors="ignore")

    # Phase 0: Translate Vietnamese query to English for better AI understanding
    translated_query = translate_query_to_english(user_query)

    # Phase 0.5: Detect line limit from user query
    # Supports: "first 100 lines", "100 dòng đầu", "top 50 lines", "analyze 200 lines", etc.
    line_limit = _extract_line_limit(user_query) or _extract_line_limit(translated_query)
    if line_limit:
        lines = text.splitlines()
        text = "\n".join(lines[:line_limit])

    # Phase 1: Raw analyze
    records, failed_lines = parse_log_text(text)
    overview = build_overview(records, failed_lines)
    raw_clusters = build_clusters(records)
    raw_probable_causes = derive_probable_causes(raw_clusters)
    raw_recommendations = derive_recommendations(raw_clusters)
    evidence = collect_evidence(raw_clusters)
    severity = derive_severity(raw_clusters)
    raw_action_checks = derive_action_checks(raw_clusters)

    # Phase 2: Focus by user intent
    focus_mode = detect_focus_mode(user_query)

    clusters_dict = [c.model_dump() for c in raw_clusters]
    clusters_dict = filter_clusters_by_focus(clusters_dict, focus_mode)
    clusters = clusters_dict

    probable_causes = filter_list_by_focus(raw_probable_causes, focus_mode)
    recommendations = filter_list_by_focus(raw_recommendations, focus_mode)
    action_checks = filter_action_checks_by_focus(raw_action_checks, focus_mode)
    probable_causes = probable_causes[:4]
    recommendations = recommendations[:4]
    primary_issue, secondary_issues = annotate_issue_roles(clusters, focus_mode)

    cluster_labels = [c["label"] for c in clusters]

    # Phase 3: Retrieve knowledge with intent
    retrieved_knowledge = retrieve_knowledge(
        cluster_labels=cluster_labels,
        probable_causes=probable_causes,
        evidence=evidence,
        user_query=translated_query,
        top_k=4,
    )

    # Phase 4: Initial reasoning
    # Limit cluster samples for summary generation to speed up LLM
    clusters_for_summary = []
    for c in clusters[:5]:
        c_copy = c.copy()
        if "samples" in c_copy and len(c_copy["samples"]) > 3:
            c_copy["samples"] = c_copy["samples"][:3]
        clusters_for_summary.append(c_copy)

    summary_payload = {
        "user_query": translated_query,
        "focus_mode": focus_mode,
        "primary_issue": primary_issue,
        "secondary_issues": secondary_issues,
        "overview": overview.model_dump(),
        "clusters": clusters_for_summary,
        "probable_causes": probable_causes,
        "recommendations": recommendations,
        "evidence": evidence[:5],
        "retrieved_knowledge": retrieved_knowledge,
        "severity": severity,
        "action_checks": action_checks,
    }

    summary = generate_incident_summary(summary_payload)

    # Phase 5: Execute focused actions
    executed_actions = execute_action_checks(action_checks, max_actions=4)

    # Phase 6: Final reasoning with tool results
    # Limit cluster samples to max 2 per cluster to reduce payload size for LLM
    clusters_for_final = []
    for c in clusters[:5]:
        c_copy = c.copy()
        if "samples" in c_copy and len(c_copy["samples"]) > 2:
            c_copy["samples"] = c_copy["samples"][:2]
        clusters_for_final.append(c_copy)
    
    final_payload = {
        "user_query": translated_query,
        "focus_mode": focus_mode,
        "primary_issue": primary_issue,
        "secondary_issues": secondary_issues,
        "overview": overview.model_dump(),
        "clusters": clusters_for_final,
        "probable_causes": probable_causes,
        "recommendations": recommendations,
        "evidence": evidence[:5],  # Limit to top 5 evidence samples
        "retrieved_knowledge": retrieved_knowledge,
        "severity": severity,
        "initial_summary": summary,
        "planned_actions": action_checks,
        "tool_results": [x.model_dump() for x in executed_actions],
    }

    final_summary, final_diagnosis = generate_final_incident_report(final_payload)

    return AnalyzeResponse(
        success=True,
        filename=file.filename,
        result={
            "overview": overview.model_dump(),
            "clusters": clusters,
            "probable_causes": probable_causes,
            "recommendations": recommendations,
            "evidence": evidence,
            "summary": summary,
            "retrieved_knowledge": retrieved_knowledge,
            "severity": severity,
            "action_checks": action_checks,
            "executed_actions": [x.model_dump() for x in executed_actions],
            "final_summary": final_summary,
            "final_diagnosis": final_diagnosis,
        },
    )