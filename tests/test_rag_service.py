"""
Tests for app.services.rag_service — RAG retrieval logic.

Validates:
- Query construction from analysis context
- Document type ranking
- Focus-mode document filtering
- End-to-end retrieval (if vector store is available)
"""
import pytest

from app.services.rag_service import (
    build_retrieval_query,
    _doc_type_rank,
    _is_backend_doc,
    _is_access_doc,
    _should_drop_doc,
    _focus_rank,
)


# =============================================================================
# Query Building
# =============================================================================

class TestBuildRetrievalQuery:
    """Test semantic search query construction."""

    def test_includes_user_query(self):
        q = build_retrieval_query([], [], [], user_query="check tomcat")
        assert "check tomcat" in q

    def test_includes_clusters(self):
        q = build_retrieval_query(["mod_jk error"], [], [])
        assert "mod_jk error" in q

    def test_includes_causes(self):
        q = build_retrieval_query([], ["backend down"], [])
        assert "backend down" in q

    def test_includes_evidence(self):
        q = build_retrieval_query([], [], ["connection refused"])
        assert "connection refused" in q

    def test_empty_returns_empty(self):
        q = build_retrieval_query([], [], [], user_query="")
        assert q == ""

    def test_combined_query(self):
        q = build_retrieval_query(
            cluster_labels=["mod_jk error"],
            probable_causes=["backend timeout"],
            evidence=["connection refused"],
            user_query="check AJP port",
        )
        assert "User goal" in q
        assert "Clusters" in q
        assert "Causes" in q
        assert "Evidence" in q


# =============================================================================
# Document Type Ranking
# =============================================================================

class TestDocTypeRank:
    """Test knowledge document type priority."""

    def test_runbook_highest(self):
        assert _doc_type_rank({"doc_type": "runbook"}) == 0

    def test_text_note_second(self):
        assert _doc_type_rank({"doc_type": "text_note"}) == 1

    def test_apache_docs_third(self):
        assert _doc_type_rank({"doc_type": "apache_official_docs"}) == 2

    def test_unknown_lowest(self):
        assert _doc_type_rank({"doc_type": "random"}) == 3
        assert _doc_type_rank({}) == 3


# =============================================================================
# Document Classification
# =============================================================================

class TestDocClassification:
    """Test backend vs access document classification."""

    def test_backend_doc(self):
        assert _is_backend_doc({"source": "mod_jk_guide.md", "topic": "worker"}) is True

    def test_access_doc(self):
        assert _is_access_doc({"source": "htaccess_guide.md", "topic": "forbidden"}) is True

    def test_neither(self):
        meta = {"source": "readme.md", "topic": "general"}
        assert _is_backend_doc(meta) is False
        assert _is_access_doc(meta) is False


# =============================================================================
# Focus-Mode Filtering
# =============================================================================

class TestFocusFiltering:
    """Test document dropping and ranking by focus mode."""

    def test_backend_focus_drops_access(self):
        meta = {"source": "forbidden_guide.md", "topic": "directory"}
        assert _should_drop_doc(meta, "backend_connectivity") is True

    def test_access_focus_drops_backend(self):
        meta = {"source": "mod_jk_guide.md", "topic": "worker"}
        assert _should_drop_doc(meta, "access_control") is True

    def test_general_drops_nothing(self):
        meta = {"source": "anything.md", "topic": "whatever"}
        assert _should_drop_doc(meta, "general") is False

    def test_focus_rank_backend(self):
        meta = {"source": "mod_jk.md", "topic": "worker"}
        assert _focus_rank(meta, "backend_connectivity") == 0

    def test_focus_rank_unrelated(self):
        meta = {"source": "readme.md", "topic": "general"}
        assert _focus_rank(meta, "backend_connectivity") == 10

    def test_focus_rank_general_always_zero(self):
        meta = {"source": "anything.md", "topic": "whatever"}
        assert _focus_rank(meta, "general") == 0
