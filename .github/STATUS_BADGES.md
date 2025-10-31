# Status Badges for README.md

Add these status badges to your main README.md file to show the current CI/CD status:

```markdown
<!-- CI/CD Status Badges -->
[![CI](https://github.com/tidal-mcp/tidal-mcp/workflows/CI/badge.svg)](https://github.com/tidal-mcp/tidal-mcp/actions/workflows/ci.yml)
[![Quality Gates](https://github.com/tidal-mcp/tidal-mcp/workflows/Quality%20Gates/badge.svg)](https://github.com/tidal-mcp/tidal-mcp/actions/workflows/quality.yml)
[![CodeQL](https://github.com/tidal-mcp/tidal-mcp/workflows/CodeQL%20Advanced%20Security/badge.svg)](https://github.com/tidal-mcp/tidal-mcp/actions/workflows/codeql.yml)

<!-- Code Quality Badges -->
[![codecov](https://codecov.io/gh/tidal-mcp/tidal-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/tidal-mcp/tidal-mcp)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Linting: flake8](https://img.shields.io/badge/linting-flake8-yellowgreen)](https://flake8.pycqa.org/)

<!-- Security Badges -->
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Known Vulnerabilities](https://snyk.io/test/github/tidal-mcp/tidal-mcp/badge.svg)](https://snyk.io/test/github/tidal-mcp/tidal-mcp)

<!-- Python & Package Badges -->
[![Python Versions](https://img.shields.io/pypi/pyversions/tidal-mcp.svg)](https://pypi.org/project/tidal-mcp/)
[![PyPI version](https://badge.fury.io/py/tidal-mcp.svg)](https://badge.fury.io/py/tidal-mcp)
[![Downloads](https://pepy.tech/badge/tidal-mcp)](https://pepy.tech/project/tidal-mcp)

<!-- Project Status -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/tidal-mcp/tidal-mcp/graphs/commit-activity)
```

## Additional Badges (Optional)

```markdown
<!-- Development Status -->
[![Development Status](https://img.shields.io/pypi/status/tidal-mcp.svg)](https://pypi.org/project/tidal-mcp/)
[![GitHub issues](https://img.shields.io/github/issues/tidal-mcp/tidal-mcp.svg)](https://github.com/tidal-mcp/tidal-mcp/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/tidal-mcp/tidal-mcp.svg)](https://github.com/tidal-mcp/tidal-mcp/pulls)

<!-- Community -->
[![GitHub stars](https://img.shields.io/github/stars/tidal-mcp/tidal-mcp.svg?style=social&label=Star)](https://github.com/tidal-mcp/tidal-mcp)
[![GitHub forks](https://img.shields.io/github/forks/tidal-mcp/tidal-mcp.svg?style=social&label=Fork)](https://github.com/tidal-mcp/tidal-mcp/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/tidal-mcp/tidal-mcp.svg?style=social&label=Watch)](https://github.com/tidal-mcp/tidal-mcp)

<!-- Release Info -->
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/tidal-mcp/tidal-mcp?sort=semver)](https://github.com/tidal-mcp/tidal-mcp/releases)
[![GitHub commits since tagged version](https://img.shields.io/github/commits-since/tidal-mcp/tidal-mcp/v0.1.0)](https://github.com/tidal-mcp/tidal-mcp/commits/main)
```

## Badge Placement in README

Typically place the badges in one of these locations:

1. **At the top** (right after the title and description)
2. **In a dedicated "Status" section**
3. **In the table of contents area**

Example placement:

```markdown
# Tidal MCP

A Model Context Protocol (MCP) server for interacting with Tidal music streaming service.

<!-- Badges go here -->
[![CI](https://github.com/tidal-mcp/tidal-mcp/workflows/CI/badge.svg)](https://github.com/tidal-mcp/tidal-mcp/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tidal-mcp/tidal-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/tidal-mcp/tidal-mcp)
[![Python Versions](https://img.shields.io/pypi/pyversions/tidal-mcp.svg)](https://pypi.org/project/tidal-mcp/)

## Table of Contents
...
```

## Badge Customization

You can customize badge colors and styles:

- **Style options**: `flat`, `flat-square`, `plastic`, `for-the-badge`, `social`
- **Color options**: `brightgreen`, `green`, `yellowgreen`, `yellow`, `orange`, `red`, `lightgrey`, `blue`

Example with custom styling:
```markdown
[![Custom Badge](https://img.shields.io/badge/custom-badge-blue.svg?style=for-the-badge&logo=python)](https://example.com)
```
