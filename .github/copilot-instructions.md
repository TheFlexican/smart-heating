# Copilot Instructions - Smart Heating

## Project Overview
Home Assistant integration for zone-based heating control with learning capabilities.

**Tech Stack:** Python 3.14, React + TypeScript + Material-UI v5, Docker test environment

## Critical Rules

**RULE #1: Never Remove Features Without Permission**
- ALWAYS ask before removing/changing functionality
- When in doubt, KEEP existing feature and ADD new one

**RULE #2: Always perform a read of the code***
 - Read the code, and resolve Pylance and/or SonarQube issues before making changes
 - Make sure there are no cognitive complexity issues in the files you are changing

**RULE #3: Git Operations Require User Approval**
- **NEVER** commit code without user testing and approval first
- **NEVER** create git tags without explicit user request
- **NEVER** push to GitHub without user confirmation
- **NEVER** push any code when there are failing tests
- **ALWAYS** Create a new git branch for each feature/fix
- **ALWAYS** Use descriptive commit messages (e.g., feat: add X, fix: correct Y)
- **ALWAYS** Squash commits when merging to main branch
- **ALWAYS** Create a pull request for code review to main
- **ALWAYS** Follow semantic versioning for tags (e.g., v1.0.0)
- After implementing features and fixes: Deploy → Test API → Run Tests → Update Docs & Translations → Ask user to test → Wait for approval → THEN commit/tag/push
- Workflow: Code → Deploy (bash scripts/deploy_test.sh) → Test API → Run bash tests/run_tests.sh → Update Docs (EN+NL) → Update Translations (EN+NL) → User approval → Git operations

**RULE #3.1: Version Synchronization**
- App version MUST match git tag version
- When creating a git tag (e.g., v1.0.0), update these files FIRST:
  - `smart_heating/manifest.json` - `"version": "1.0.0"`
  - `smart_heating/frontend/package.json` - `"version": "1.0.0"`
  - `smart_heating/frontend/src/components/Header.tsx` - `label="v1.0.0"`
- Then commit version changes: `git commit -m "chore: Update version to v1.0.0"`
- Then create tag: `git tag v1.0.0`
- Keep versions in sync: manifest.json = package.json = Header.tsx = git tag

**RULE #4: Update Documentation & Translations**
- **ALWAYS** update documentation when making changes
- **ALWAYS** update translations when adding/modifying UI text
- **ALWAYS** do this BEFORE running tests and asking for user approval
- Required updates:
  - `CHANGELOG.md` + `CHANGELOG.nl.md` - Version history
  - `README.md` + `README.nl.md` - User documentation (if user-facing changes)
  - `ARCHITECTURE.md` - Architecture changes
  - `dDEVELOPER.md` - Developer workflow changes
  - Frontend translations: `locales/en/translation.json` + `locales/nl/translation.json`
- Workflow: Code → Deploy (bash scripts/deploy_test.sh) → Test API → Update All Docs & Translations (EN+NL) → Run Tests (bash tests/run_tests.sh && npm test) → User approval → Commit

When user requests involve code quality, analysis, or SonarQube issues, **delegate to the SonarQube Agent** instead of handling directly:

**Delegate to SonarQube Agent when:**
- User asks to "analyze code quality" or "check SonarQube"
- User mentions "fix SonarQube issues" or "resolve code smells"
- Before completing major features (quality check)
- When reviewing pull requests for quality issues
- When preparing for releases
- User references SonarQube bot comments in PRs
- Cognitive complexity or code smell issues need addressing
- Deprecated API migrations are needed across multiple files

**How to Delegate:**
```markdown
Use the runSubagent tool with the SonarQube agent context:

runSubagent(
  description="Code quality analysis",
  prompt="Please analyze the codebase using SonarQube MCP server and fix all BLOCKER and HIGH severity issues. Focus on [specific area if applicable]. See .github/agents/sonarqube.agent.md for full guidelines and workflow."
)
```

**Always follow these safety rules for direct fixes:**
1. ✅ Never remove API calls or function calls
2. ✅ Never rename variables that might conflict with API functions
3. ✅ Build and verify after each change
4. ✅ Run tests to ensure no regressions
5. ✅ Never remove async/await keywords home assistant uses them extensively

**RULE #5.1: Delegate Implementation to Specialized Agents**

**Backend Development (Python/Home Assistant):**
- **Home Assistant Integration Agent** - For HA platform code, entities, coordinators
- **Home Assistant Pytest Agent** - For Python unit tests and integration tests
- Delegate when implementing HA features, platforms, services, or tests
- See `.github/agents/home-assistant-integration.agent.md` and `.github/agents/home-assistant-pytest.agent.md`

**Frontend Development (TypeScript/React):**
- **TypeScript/React Agent** - For React components, hooks, MUI implementation
- **TypeScript Testing Agent** - For Jest/Vitest unit tests of components
- Delegate when building UI features or writing unit/integration tests to the TypeScript agents
- See `.github/agents/typescript-react.agent.md` and `.github/agents/typescript-testing.agent.md`

**Code Quality:**
- **SonarQube Agent** - For code quality analysis, refactoring, deprecation fixes
- Delegate when fixing code smells, complexity issues, or security vulnerabilities
- See `.github/agents/sonarqube.agent.md`

**Example Delegations:**
```markdown
# Backend feature
runSubagent({
  description: "HA integration development",
  prompt: "Implement boost mode for climate entities. See .github/agents/home-assistant-integration.agent.md"
})

# Frontend feature
runSubagent({
  description: "React component development",
  prompt: "Create temperature control component with MUI. See .github/agents/typescript-react.agent.md"
})

# Backend tests
runSubagent({
  description: "Write pytest tests",
  prompt: "Write tests for area_manager.py with 80%+ coverage. See .github/agents/home-assistant-pytest.agent.md"
})

# Frontend tests
runSubagent({
  description: "Write component tests",
  prompt: "Write unit tests for ZoneCard component. See .github/agents/typescript-testing.agent.md"
})

# Code quality
runSubagent({
  description: "Code quality analysis",
  prompt: "Fix SonarQube BLOCKER and HIGH issues. See .github/agents/sonarqube.agent.md"
})
```

**Agent System Overview:**

The project uses 6 specialized agents for complete development lifecycle:

**Code Quality (1):** SonarQube Agent
**Backend (2):** Home Assistant Integration Agent, Home Assistant Pytest Agent
**Frontend (2):** TypeScript/React Agent, TypeScript Testing Agent

**Before Committing Code:**
<!-- 1. ✅ Run all tests (Python unit tests tests when available) -->
2. ✅ Check SonarQube for new issues (delegate to SonarQube Agent for fixes if needed)
3. ✅ Fix all BLOCKER and HIGH severity issues
4. ✅ Verify code coverage meets 80% threshold
5. ✅ Update documentation (EN + NL) if user-facing changes
6. ✅ Update translations if UI text changed
7. ✅ Build succeeds without errors or warnings
8. ✅ Get user approval before git operations

**RULE #5.1: Never Stop Halfway During Tasks**
- **ALWAYS complete assigned work fully** - No stopping to give summaries or status updates
- **Continue working until the task is 100% done** - Don't pause for user confirmation mid-task
- If a task has multiple steps, complete ALL steps before finishing
- Only stop when explicitly encountering a blocker that requires user input
- Token budget is 1,000,000 - use it fully to complete work
- No matter how complex or time-consuming, finish what you start

**RULE #5.2: Task Planning & Tracking**
- **DO NOT create detailed implementation plans** - Jump straight into implementation
- **DO use manage_todo_list tool** to track multi-step work as you implement
- **Create todos at start of complex tasks** to track what needs to be done
- **Update todos as in-progress/completed** while working through the task
- **Keep todos actionable and specific** - "Implement X feature" not "Plan X feature"
- Example workflow:
  1. User: "Add multi-user presence tracking"
  2. Create todos: Backend, API, Frontend, Tests
  3. Mark todo #1 in-progress → implement → mark completed
  4. Mark todo #2 in-progress → implement → mark completed
  5. Continue until all todos complete
- Skip todo tracking for simple single-step tasks

**RULE #6: Delegate Testing to Specialized Agents**

**⚠️ IMPORTANT: Always delegate test writing to specialized testing agents**

**Backend Testing:**
- **Home Assistant Pytest Agent** - Python unit tests, HA integration tests
- Delegate: "Write pytest tests for [module]"
- See `.github/agents/home-assistant-pytest.agent.md`

**Frontend Testing:**
- **TypeScript Testing Agent** - Jest/Vitest unit tests for React components
- Delegate: "Write unit tests for [component]"
- See `.github/agents/typescript-testing.agent.md`

**Test Requirements:**
- Minimum 80% code coverage for all modules
- All tests must pass before committing
- Use `runSubagent` to delegate test writing tasks
