# Testing Quickstart

This guide explains how to run and verify tests for the Smart Heating integration.

## Backend (Python)

- **Run all tests:**
  ```bash
  bash tests/run_tests.sh
  ```
- **Run specific test file:**
  ```bash
  source venv/bin/activate
  pytest tests/unit/test_area_manager.py -v
  ```
- **Run with coverage report:**
  ```bash
  source venv/bin/activate
  pytest tests/unit --cov=smart_heating --cov-report=html -v
  # Open coverage_html/index.html for report
  ```

## Frontend (TypeScript/React)

- **Install dependencies:**
  ```bash
  cd smart_heating/frontend
  npm install
  ```
- **Run all frontend tests:**
  ```bash
  npm test
  ```
- **Debug tests (headed mode):**
  ```bash
  npm test -- --headed
  ```

## Coverage Requirements
- Minimum 80% coverage for all modules
- Coverage reports generated in `coverage_html/` (backend) and standard output (frontend)

## Troubleshooting
- Ensure virtualenv is activated for Python tests
- Clear browser cache for frontend changes
- Check logs for errors if tests fail

---
For more details, see DEVELOPER.md and ARCHITECTURE.md.
