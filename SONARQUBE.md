# SonarQube Configuration

This directory contains the SonarQube configuration for the Smart Heating project.

## Files

- `sonar-project.properties` - Main SonarQube configuration file

## Configuration Details

### Test File Exclusions

Test files are excluded from code quality analysis to focus on production code quality. The following patterns are excluded:

- `tests/**/*` - All test files
- `**/test_*.py` - Python test files
- `**/*_test.py` - Alternative test naming pattern
- `**/conftest.py` - pytest configuration
- `tests/e2e/**` - E2E test files

### Coverage

Test coverage is still collected and reported from test files, but code quality issues (complexity, code smells, etc.) are only reported for production code in the `smart_heating/` directory.

## Usage

### With SonarQube CLI

```bash
# The sonar-project.properties file will be automatically detected
sonar-scanner
```

### With GitHub Actions

The configuration is automatically picked up by the SonarQube GitHub Action when it runs.

## Key Settings

- **Project Key**: `TheFlexican_smart-heating`
- **Organization**: `theflexican`
- **Source Directory**: `smart_heating/`
- **Test Directory**: `tests/`
- **Python Version**: 3.13
- **Coverage Report**: `coverage.xml`

## Why Exclude Tests?

Test files often have different quality standards than production code:

- Tests may have higher cognitive complexity
- Mock/fixture setup code may trigger false positives
- Test-specific patterns may not follow production code standards
- We want to focus quality metrics on code that runs in production

Coverage metrics from tests are still reported to ensure production code is well-tested.
