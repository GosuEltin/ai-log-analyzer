from fastapi import APIRouter, UploadFile, File, HTTPException, Form

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


@router.get("/")
def root():
    return {"message": "AI Log Analyzer is running"}


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
        user_query=user_query,
        top_k=4,
    )

    # Phase 4: Initial reasoning
    summary_payload = {
        "user_query": user_query,
        "focus_mode": focus_mode,
        "primary_issue": primary_issue,
        "secondary_issues": secondary_issues,
        "overview": overview.model_dump(),
        "clusters": clusters[:5],
        "probable_causes": probable_causes,
        "recommendations": recommendations,
        "evidence": evidence,
        "retrieved_knowledge": retrieved_knowledge,
        "severity": severity,
        "action_checks": action_checks,
    }

    summary = generate_incident_summary(summary_payload)

    # Phase 5: Execute focused actions
    executed_actions = execute_action_checks(action_checks, max_actions=4)

    # Phase 6: Final reasoning with tool results
    final_payload = {
        "user_query": user_query,
        "focus_mode": focus_mode,
        "primary_issue": primary_issue,
        "secondary_issues": secondary_issues,
        "overview": overview.model_dump(),
        "clusters": clusters[:5],
        "probable_causes": probable_causes,
        "recommendations": recommendations,
        "evidence": evidence,
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