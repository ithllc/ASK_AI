"""
Unit Tests - ASK AI Skills Builder

Tests individual components against the PRD rubric criteria:
- Search engine result structure and validation
- Agent state machine transitions
- OCR response cleaning
- Skill file generation
- URL validation

Each test records results in the rubric tracker for scoring.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.search_engine import SearchEngine, SearchResult
from app.agent import ConversationAgent, AgentState
from app.doc_analyzer import DocAnalyzer


# ─── Search Engine Tests ────────────────────────────────────────


class TestSearchEngine:
    """Unit tests for the search engine module."""

    def test_search_result_dataclass(self, rubric):
        """SearchResult has required fields."""
        r = SearchResult(title="Test", url="https://example.com", snippet="A snippet")
        passed = (
            r.title == "Test"
            and r.url == "https://example.com"
            and r.snippet == "A snippet"
            and r.has_dev_docs is None
        )
        rubric.record(
            "Unit: Search Engine",
            "SearchResult dataclass structure",
            passed,
            weight=1.0,
            criteria="All fields accessible and correctly typed",
        )
        assert passed

    def test_curated_fallback_returns_results(self, rubric):
        """Curated fallback returns at least 3 results."""
        engine = SearchEngine()
        results = engine._curated_fallback("blockchain dapp")
        passed = len(results) >= 3
        rubric.record(
            "Unit: Search Engine",
            "Fallback returns >= 3 results",
            passed,
            weight=1.0,
            criteria="Curated fallback must return >= 3 results for any query",
            details=f"Got {len(results)} results",
        )
        assert passed

    def test_curated_fallback_relevance(self, rubric):
        """Fallback results are relevant to query."""
        engine = SearchEngine()
        results = engine._curated_fallback("base blockchain dapp")
        # First result should be Base-related
        top = results[0]
        passed = "base" in top.title.lower() or "base" in top.url.lower()
        rubric.record(
            "Unit: Search Engine",
            "Fallback results relevance",
            passed,
            weight=1.0,
            criteria="Top result should match query keywords",
            details=f"Top result: {top.title}",
        )
        assert passed

    def test_search_result_url_format(self, rubric):
        """Search results have valid URL format."""
        engine = SearchEngine()
        results = engine._curated_fallback("stripe api")
        all_valid = all(
            r.url.startswith("http://") or r.url.startswith("https://")
            for r in results
        )
        rubric.record(
            "Unit: Search Engine",
            "URL format validation",
            all_valid,
            weight=1.0,
            criteria="All URLs must start with http:// or https://",
        )
        assert all_valid

    def test_search_result_non_empty_fields(self, rubric):
        """All search result fields are non-empty."""
        engine = SearchEngine()
        results = engine._curated_fallback("vercel deployment")
        all_filled = all(
            r.title and r.url and r.snippet
            for r in results
        )
        rubric.record(
            "Unit: Search Engine",
            "Non-empty result fields",
            all_filled,
            weight=1.0,
            criteria="Title, URL, and snippet must all be non-empty",
        )
        assert all_filled


# ─── Agent State Machine Tests ──────────────────────────────────


class TestAgentStateMachine:
    """Unit tests for the conversation agent state machine."""

    def test_initial_state(self, rubric):
        """Agent starts in INTRO state."""
        agent = ConversationAgent()
        passed = agent.state == AgentState.INTRO
        rubric.record(
            "Unit: Agent State Machine",
            "Initial state is INTRO",
            passed,
            weight=1.0,
            criteria="Agent must initialize in INTRO state",
        )
        assert passed

    def test_max_site_tries_default(self, rubric):
        """Default max site tries is 3."""
        agent = ConversationAgent()
        passed = agent.max_site_tries == 3
        rubric.record(
            "Unit: Agent State Machine",
            "Max site tries = 3",
            passed,
            weight=1.0,
            criteria="POC limits to 3 site iterations per PRD",
        )
        assert passed

    def test_agent_has_required_components(self, rubric):
        """Agent has search engine and doc analyzer."""
        agent = ConversationAgent()
        passed = (
            agent.search_engine is not None
            and agent.doc_analyzer is not None
            and isinstance(agent.search_engine, SearchEngine)
            and isinstance(agent.doc_analyzer, DocAnalyzer)
        )
        rubric.record(
            "Unit: Agent State Machine",
            "Required components present",
            passed,
            weight=1.0,
            criteria="Agent must have SearchEngine and DocAnalyzer",
        )
        assert passed

    def test_all_states_defined(self, rubric):
        """All required states are defined in AgentState enum."""
        required_states = [
            "INTRO", "GATHERING", "SEARCHING", "PRESENTING_RESULTS",
            "AWAITING_SELECTION", "CHECKING_DOCS", "FOUND_DOCS",
            "NO_DOCS", "CHECKING_ASK_AI", "INTERACTING_AI",
            "EXTRACTING", "COMPLETE", "ENDED",
        ]
        all_present = all(hasattr(AgentState, s) for s in required_states)
        rubric.record(
            "Unit: Agent State Machine",
            "All states defined",
            all_present,
            weight=2.0,
            criteria="All conversation flow states must exist in enum",
            details=f"Checked {len(required_states)} states",
        )
        assert all_present

    @pytest.mark.asyncio
    async def test_introduce_sets_gathering(self, rubric):
        """Introduction transitions agent to GATHERING state."""
        agent = ConversationAgent()
        messages = []
        statuses = []

        async def capture_msg(msg):
            messages.append(msg)

        async def capture_status(status, detail=""):
            statuses.append(status)

        agent.on_message = capture_msg
        agent.on_status = capture_status

        await agent.introduce()

        passed = (
            agent.state == AgentState.GATHERING
            and len(messages) > 0
            and "ready" in statuses
        )
        rubric.record(
            "Unit: Agent State Machine",
            "Introduction -> GATHERING transition",
            passed,
            weight=2.0,
            criteria="introduce() must emit message and transition to GATHERING",
        )
        assert passed

    @pytest.mark.asyncio
    async def test_empty_input_ignored(self, rubric):
        """Empty input should not change state."""
        agent = ConversationAgent()
        agent.on_message = lambda m: None
        agent.on_status = lambda s, d="": None
        agent.state = AgentState.GATHERING

        await agent.handle_input("")
        await agent.handle_input("   ")

        passed = agent.state == AgentState.GATHERING
        rubric.record(
            "Unit: Agent State Machine",
            "Empty input ignored",
            passed,
            weight=1.0,
            criteria="Blank/whitespace input must not trigger state change",
        )
        assert passed

    @pytest.mark.asyncio
    async def test_ended_state_blocks_input(self, rubric):
        """ENDED state should reject further input."""
        agent = ConversationAgent()
        messages = []
        agent.on_message = lambda m: messages.append(m)
        # Make on_message a coroutine
        async def async_msg(m):
            messages.append(m)
        agent.on_message = async_msg
        agent.on_status = lambda s, d="": None
        async def async_status(s, d=""):
            pass
        agent.on_status = async_status
        agent.state = AgentState.ENDED

        await agent.handle_input("hello")

        passed = agent.state == AgentState.ENDED and len(messages) > 0
        rubric.record(
            "Unit: Agent State Machine",
            "ENDED state blocks further input",
            passed,
            weight=1.0,
            criteria="After ENDED, input should return session-ended message",
        )
        assert passed


# ─── Doc Analyzer Tests ─────────────────────────────────────────


class TestDocAnalyzer:
    """Unit tests for the documentation analyzer."""

    def test_doc_indicators_defined(self, rubric):
        """DocAnalyzer has documentation indicator keywords."""
        analyzer = DocAnalyzer()
        passed = len(analyzer.DOC_INDICATORS) >= 5
        rubric.record(
            "Unit: Doc Analyzer",
            "Documentation indicators defined",
            passed,
            weight=1.0,
            criteria="Must have >= 5 doc indicator keywords",
            details=f"Has {len(analyzer.DOC_INDICATORS)} indicators",
        )
        assert passed

    def test_ask_ai_keywords_defined(self, rubric):
        """DocAnalyzer has ASK AI detection keywords."""
        analyzer = DocAnalyzer()
        passed = len(analyzer.ASK_AI_KEYWORDS) >= 2
        rubric.record(
            "Unit: Doc Analyzer",
            "ASK AI keywords defined",
            passed,
            weight=1.0,
            criteria="Must have >= 2 ASK AI keywords",
        )
        assert passed

    def test_clean_ocr_response(self, rubric):
        """OCR response cleaning removes UI chrome."""
        analyzer = DocAnalyzer()
        raw = """Navigation Menu
Search...
Ask a question
Found results for building dApps
Here's how to build a dApp:
1. Install dependencies
2. Configure your project
Powered by AI
Cookie Policy"""

        cleaned = analyzer._clean_ocr_response(raw, "building dApps")
        passed = (
            "Navigation Menu" not in cleaned
            and "Cookie Policy" not in cleaned
            and "Powered by" not in cleaned
            and "Here's how" in cleaned
        )
        rubric.record(
            "Unit: Doc Analyzer",
            "OCR response cleaning",
            passed,
            weight=2.0,
            criteria="Must remove UI chrome and keep AI response content",
            details=f"Cleaned length: {len(cleaned)} chars",
        )
        assert passed

    @pytest.mark.asyncio
    async def test_save_skill_creates_file(self, rubric, skills_dir):
        """save_skill creates a valid markdown file."""
        import app.doc_analyzer as da
        original_dir = da.SKILLS_DIR
        da.SKILLS_DIR = skills_dir

        analyzer = DocAnalyzer()
        site = SearchResult(
            title="Test Site",
            url="https://test.example.com",
            snippet="Test snippet",
        )

        filepath = await analyzer.save_skill(site, "test query", "test response")

        exists = os.path.exists(filepath)
        content = ""
        if exists:
            with open(filepath) as f:
                content = f.read()

        passed = (
            exists
            and "# AI Skill: Test Site" in content
            and "test query" in content
            and "test response" in content
            and filepath.endswith("_skill.md")
        )

        da.SKILLS_DIR = original_dir

        rubric.record(
            "Unit: Doc Analyzer",
            "Skill file generation",
            passed,
            weight=2.0,
            criteria="Must create valid markdown with source URL, query, and response",
        )
        assert passed


# ─── Performance / Configuration Tests ──────────────────────────


class TestConfiguration:
    """Tests for project configuration and requirements."""

    def test_skills_dir_constant(self, rubric):
        """SKILLS_DIR is correctly defined."""
        from app.doc_analyzer import SKILLS_DIR
        passed = SKILLS_DIR.endswith("skills")
        rubric.record(
            "Unit: Configuration",
            "SKILLS_DIR path correct",
            passed,
            weight=0.5,
            criteria="SKILLS_DIR must end with 'skills'",
        )
        assert passed

    def test_agent_state_enum_values(self, rubric):
        """AgentState enum values are lowercase strings."""
        all_lower = all(s.value == s.value.lower() for s in AgentState)
        rubric.record(
            "Unit: Configuration",
            "State enum values are lowercase",
            all_lower,
            weight=0.5,
            criteria="Enum values should be lowercase for JSON serialization",
        )
        assert all_lower
