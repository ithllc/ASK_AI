"""
Conversational Agent Module

Implements a state-machine-based conversational agent that guides users
through the ASK AI Skills Builder workflow:

1. Introduction and request gathering
2. Web search for documentation sites (Google ADK-style deep search)
3. Site selection by user
4. Developer docs verification
5. ASK AI button detection and interaction
6. Response extraction and skill generation

Follows Google ADK Agent patterns for tool orchestration.
"""

import enum
from typing import Callable, Optional, List

from app.search_engine import SearchEngine, SearchResult
from app.doc_analyzer import DocAnalyzer


class AgentState(enum.Enum):
    INTRO = "intro"
    GATHERING = "gathering"
    SEARCHING = "searching"
    PRESENTING_RESULTS = "presenting_results"
    AWAITING_SELECTION = "awaiting_selection"
    CHECKING_DOCS = "checking_docs"
    FOUND_DOCS = "found_docs"
    NO_DOCS = "no_docs"
    CHECKING_ASK_AI = "checking_ask_ai"
    INTERACTING_AI = "interacting_ai"
    EXTRACTING = "extracting"
    COMPLETE = "complete"
    ENDED = "ended"


class ConversationAgent:
    """
    Stateful conversational agent for the ASK AI Skills Builder.

    Manages the full conversation lifecycle with status callbacks
    for real-time UI updates.
    """

    def __init__(self):
        self.state = AgentState.INTRO
        self.search_engine = SearchEngine()
        self.doc_analyzer = DocAnalyzer()
        self.search_results: List[SearchResult] = []
        self.selected_site: Optional[SearchResult] = None
        self.sites_tried = 0
        self.max_site_tries = 3
        self.user_query = ""
        self.on_status: Optional[Callable] = None
        self.on_message: Optional[Callable] = None

    async def _emit_status(self, status: str, detail: str = ""):
        if self.on_status:
            await self.on_status(status, detail)

    async def _emit_message(self, message: str):
        if self.on_message:
            await self.on_message(message)

    async def introduce(self):
        """Send the introduction message and transition to GATHERING state."""
        self.state = AgentState.INTRO
        await self._emit_status("ready", "Agent initialized and ready")
        await self._emit_message(
            "Welcome to the **ASK AI Skills Builder**! "
            "I help you discover and interact with AI assistants embedded in developer documentation sites.\n\n"
            "Here's how I work:\n"
            "1. You tell me what technology or documentation you're looking for\n"
            "2. I search the web to find relevant documentation sites\n"
            "3. You pick a site from the results\n"
            "4. I check if it has developer docs and an **ASK AI** feature\n"
            "5. If found, I interact with the AI and extract the response for you\n\n"
            "**What technology, framework, or API documentation are you looking for?**\n\n"
            "_Example: \"building dApps on Base\", \"Stripe payment API\", \"Vercel deployment\"_"
        )
        self.state = AgentState.GATHERING

    async def handle_input(self, user_input: str):
        """Route user input to the appropriate handler based on current state."""
        user_input = user_input.strip()
        if not user_input:
            return

        handlers = {
            AgentState.GATHERING: self._handle_gathering,
            AgentState.AWAITING_SELECTION: self._handle_selection,
            AgentState.NO_DOCS: self._handle_no_docs_response,
        }

        handler = handlers.get(self.state)
        if handler:
            await handler(user_input)
        elif self.state == AgentState.ENDED:
            await self._emit_message(
                "This session has ended. Refresh the page to start a new conversation."
            )
        else:
            await self._emit_message(
                "I'm currently processing your request. Please wait a moment..."
            )

    async def _handle_gathering(self, query: str):
        """Handle the initial user query - perform web search."""
        self.user_query = query
        self.state = AgentState.SEARCHING

        await self._emit_status("searching", f"Searching for: {query}")
        await self._emit_message(
            f"Searching for documentation sites related to **\"{query}\"**...\n\n"
            "_Using Google Deep Search to find the most relevant developer resources..._"
        )

        # Perform search
        await self._emit_status("deep_search", "Executing deep search across the web")
        search_query = f"{query} developer documentation site"
        results = await self.search_engine.search(search_query)

        if not results:
            await self._emit_status("no_results", "Search returned no results")
            await self._emit_message(
                "I couldn't find any results for that query. "
                "Could you try rephrasing? For example, be more specific about the technology or framework."
            )
            self.state = AgentState.GATHERING
            return

        self.search_results = results[:5]
        self.state = AgentState.PRESENTING_RESULTS

        await self._emit_status(
            "results_found", f"Found {len(self.search_results)} documentation sites"
        )

        msg = "Here are the top documentation sites I found:\n\n"
        for i, r in enumerate(self.search_results, 1):
            msg += f"**{i}.** [{r.title}]({r.url})\n"
            msg += f"   _{r.snippet}_\n\n"

        msg += (
            f"**Which site would you like me to explore?** "
            f"Enter a number (1-{len(self.search_results)})."
        )

        await self._emit_message(msg)
        self.state = AgentState.AWAITING_SELECTION

    async def _handle_selection(self, selection: str):
        """Handle site selection from search results."""
        # Try to parse as number
        try:
            idx = int(selection.strip()) - 1
            if 0 <= idx < len(self.search_results):
                self.selected_site = self.search_results[idx]
                self.sites_tried += 1
                await self._emit_status(
                    "site_selected",
                    f"Selected: {self.selected_site.title}"
                )
                await self._emit_message(
                    f"Great choice! I'll explore **{self.selected_site.title}** "
                    f"at `{self.selected_site.url}`.\n\n"
                    "Let me check for developer documentation..."
                )
                await self._check_developer_docs()
                return
            else:
                await self._emit_message(
                    f"Please enter a number between 1 and {len(self.search_results)}."
                )
                return
        except ValueError:
            pass

        # Try to match by name
        for i, r in enumerate(self.search_results):
            if selection.lower() in r.title.lower() or selection.lower() in r.url.lower():
                self.selected_site = self.search_results[i]
                self.sites_tried += 1
                await self._emit_status(
                    "site_selected", f"Selected: {self.selected_site.title}"
                )
                await self._emit_message(
                    f"I found a match! I'll explore **{self.selected_site.title}** "
                    f"at `{self.selected_site.url}`.\n\n"
                    "Checking for developer documentation..."
                )
                await self._check_developer_docs()
                return

        await self._emit_message(
            "I didn't recognize that selection. "
            f"Please enter a number (1-{len(self.search_results)}) "
            "or part of the site name."
        )

    async def _check_developer_docs(self):
        """Check if the selected site has developer documentation."""
        self.state = AgentState.CHECKING_DOCS

        await self._emit_status(
            "checking_docs",
            f"Analyzing {self.selected_site.url} for developer documentation"
        )

        has_docs = await self.doc_analyzer.check_dev_docs(self.selected_site.url)

        if has_docs:
            self.state = AgentState.FOUND_DOCS
            await self._emit_status("docs_found", "Developer documentation confirmed")
            await self._emit_message(
                f"Developer documentation detected on **{self.selected_site.title}**!\n\n"
                "Now scanning the page for an **ASK AI** feature using OCR visual recognition..."
            )
            await self._check_ask_ai()
        else:
            await self._handle_no_docs()

    async def _handle_no_docs(self):
        """Handle case where no developer docs are found."""
        self.state = AgentState.NO_DOCS
        await self._emit_status("no_docs", "No public developer documentation found")

        if self.sites_tried < self.max_site_tries:
            remaining = self.max_site_tries - self.sites_tried
            await self._emit_message(
                f"I couldn't find public developer documentation on "
                f"**{self.selected_site.title}**.\n\n"
                f"Would you like to try another site from the list? "
                f"({remaining} attempt{'s' if remaining > 1 else ''} remaining)\n\n"
                "Type **yes** to pick another site, or **no** to end the session."
            )
        else:
            await self._emit_message(
                "I've checked 3 different sites and couldn't find suitable "
                "developer documentation with an ASK AI feature.\n\n"
                "Thank you for using the **ASK AI Skills Builder**! "
                "Feel free to refresh the page and try a different search."
            )
            self.state = AgentState.ENDED
            await self._emit_status("ended", "Session complete - max retries reached")

    async def _handle_no_docs_response(self, response: str):
        """Handle user response when no docs were found."""
        if response.lower().strip() in ("yes", "y", "yeah", "sure", "ok"):
            self.state = AgentState.PRESENTING_RESULTS
            msg = "Here are the available sites again:\n\n"
            for i, r in enumerate(self.search_results, 1):
                msg += f"**{i}.** [{r.title}]({r.url})\n"
                msg += f"   _{r.snippet}_\n\n"
            msg += "**Which site would you like me to try next?** Enter the number."
            await self._emit_message(msg)
            self.state = AgentState.AWAITING_SELECTION
        else:
            await self._emit_message(
                "Thank you for using the **ASK AI Skills Builder**! "
                "Feel free to come back anytime. Goodbye!"
            )
            self.state = AgentState.ENDED
            await self._emit_status("ended", "Session ended by user")

    async def _check_ask_ai(self):
        """Look for an ASK AI button on the selected site."""
        self.state = AgentState.CHECKING_ASK_AI

        await self._emit_status(
            "checking_ask_ai", "Scanning page for ASK AI button via OCR"
        )

        result = await self.doc_analyzer.find_ask_ai(self.selected_site.url)

        if result.get("found"):
            label = result.get("label", "Ask AI")
            x, y = result.get("x", 0), result.get("y", 0)
            await self._emit_status(
                "ask_ai_found", f"Button '{label}' at ({x}, {y})"
            )
            await self._emit_message(
                f"Found the **ASK AI** button! (detected as `{label}` at coordinates {x}, {y})\n\n"
                "Interacting with the AI assistant now. This may take 10-15 seconds..."
            )
            await self._interact_with_ai()
        else:
            await self._emit_status("no_ask_ai", "No ASK AI button detected")

            if self.sites_tried < self.max_site_tries:
                self.state = AgentState.NO_DOCS
                remaining = self.max_site_tries - self.sites_tried
                await self._emit_message(
                    f"I couldn't find an **ASK AI** button on **{self.selected_site.title}**.\n\n"
                    f"Would you like to try another site? "
                    f"({remaining} attempt{'s' if remaining > 1 else ''} remaining)\n\n"
                    "Type **yes** to pick another, or **no** to end."
                )
            else:
                await self._emit_message(
                    "I've reached the maximum number of site attempts (3). "
                    "Thank you for using the **ASK AI Skills Builder**!"
                )
                self.state = AgentState.ENDED
                await self._emit_status("ended", "Max retries reached")

    async def _interact_with_ai(self):
        """Send a query to the site's ASK AI and extract the response."""
        self.state = AgentState.INTERACTING_AI

        query = f"How do I get started with {self.user_query}?"
        await self._emit_status("interacting", f"Sending query: {query[:50]}...")

        result = await self.doc_analyzer.interact_with_ask_ai(
            self.selected_site.url, query
        )

        self.state = AgentState.EXTRACTING
        await self._emit_status("extracting", "Processing AI response via OCR")

        if result.get("response"):
            response_text = result["response"]

            # Save as skill file
            skill_path = await self.doc_analyzer.save_skill(
                self.selected_site, query, response_text
            )

            self.state = AgentState.COMPLETE
            await self._emit_status("complete", f"Skill saved to {skill_path}")
            await self._emit_message(
                f"Successfully extracted the AI response!\n\n"
                f"---\n\n"
                f"### Response from {self.selected_site.title}\n\n"
                f"**Query:** _{query}_\n\n"
                f"{response_text}\n\n"
                f"---\n\n"
                f"Skill file saved to: `{skill_path}`\n\n"
                "Thank you for using the **ASK AI Skills Builder**! "
                "Refresh to start a new session."
            )
            self.state = AgentState.ENDED
            await self._emit_status("ended", "Session complete - skill generated")
        else:
            error = result.get("error", "Unknown error")
            await self._emit_status("error", f"Extraction failed: {error}")

            if self.sites_tried < self.max_site_tries:
                self.state = AgentState.NO_DOCS
                remaining = self.max_site_tries - self.sites_tried
                await self._emit_message(
                    f"I wasn't able to extract a response from the AI assistant. "
                    f"Error: _{error}_\n\n"
                    f"Would you like to try another site? "
                    f"({remaining} attempt{'s' if remaining > 1 else ''} remaining)\n\n"
                    "Type **yes** or **no**."
                )
            else:
                await self._emit_message(
                    "I was unable to extract a response and have reached the "
                    "maximum attempts. Thank you for using the **ASK AI Skills Builder**!"
                )
                self.state = AgentState.ENDED
                await self._emit_status("ended", "Session ended - extraction failed")
