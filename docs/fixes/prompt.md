# Original User Prompt - ASK AI Skills Builder Fix Request

**Date:** 2026-02-14
**Context:** Code review and rebuild request

---

## Full Prompt

Review and analyze the entire code base, I need you confirm if the app works or not by asking a different question, if it doesn't work, you need to generate a new technical implementation plan to fix the issues and your technical implementation plan should include a rubric system to ensure that unit tests and integration tests work based on the product requirement documentation. Also, once done, you need generate web interface for this and all users to interface with the agent by speaking to it or typing to the chat bot. I have added png that shows what the website for the example looks like. Since the site will be aimed at developers, from programming levels from novice to expert, show agent status changes so the end user knows what is going on behind the scenes. Also, use port 8074 for rendering the site. The flow of the site should be as follows: introduction and request gathering, use google's ADK and google's deep search to find site that the requestor is talking about, requestor should specify which site from the list and agent should acknowledge, agent should look for developer docs for the site, if no public developer docs can be found, the agent should let the user know and ask if they want to try another website from the search list, if the requestor says yes, then the flow continues with that search, for the proof-of-concept, it can only iterate through 3 websites on the list. if no, politely end the conversation. Continuing with the flow if yes, if website does have developer docs, then look for the "ASK AI" and follow the original documentation (with the fixes or addendums added). Remove this png file once you have finished and add this prompt to the "fixes" sub-folders and also generate a script to be used for demo purposes. This must be built in 30 minutes.

---

## Key Requirements Extracted

1. **Code Review**: Confirm if existing app works
2. **Fix Issues**: Generate new technical implementation plan
3. **Rubric System**: Unit + integration tests based on PRD
4. **Web Interface**: Chat + voice input on port 8074
5. **Developer-Focused**: Show agent status changes (novice to expert)
6. **Conversation Flow**:
   - Introduction and request gathering
   - Google ADK + Deep Search for sites
   - User selects site from list
   - Check for developer docs
   - If no docs: offer alternatives (max 3 iterations)
   - If docs found: look for ASK AI feature
   - Follow original documentation flow
7. **Cleanup**: Remove PNG, save prompt to fixes/
8. **Demo Script**: Generate demo script
9. **Time Constraint**: 30 minutes
