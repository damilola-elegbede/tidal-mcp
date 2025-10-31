# Branch Protection Setup Guide

This guide walks you through setting up branch protection rules for the Tidal MCP repository to ensure code quality and prevent breaking changes.

## Repository Settings

### 1. Navigate to Branch Protection
1. Go to your repository on GitHub
2. Click **Settings** > **Branches**
3. Click **Add rule** for the main branch

### 2. Recommended Protection Rules

#### Branch Name Pattern
```
main
```

#### Protection Settings

**✅ Required Settings:**
- [x] Require pull request reviews before merging
  - Required approving reviews: 1
  - [x] Dismiss stale PR approvals when new commits are pushed
  - [x] Require review from code owners (if CODEOWNERS file exists)

- [x] Require status checks to pass before merging
  - [x] Require branches to be up to date before merging
  - **Required status checks:** (Add these as they become available)
    - `CI / test (3.10)`
    - `CI / test (3.11)`
    - `CI / test (3.12)`
    - `CI / lint-and-format`
    - `Quality Gates / security-scan`
    - `CodeQL / analyze`

- [x] Require conversation resolution before merging

**📋 Optional but Recommended:**
- [x] Restrict pushes that create files larger than 100MB
- [x] Require signed commits (for enhanced security)
- [x] Require linear history (for cleaner git history)

**👑 Admin Settings:**
- [ ] Include administrators (recommended for team repos)
- [x] Allow force pushes (⚠️ Only enable if needed)
- [ ] Allow deletions

### 3. Environment Protection (Optional)

For production deployments, consider setting up environment protection:

1. Go to **Settings** > **Environments**
2. Create `production` environment
3. Add protection rules:
   - Required reviewers
   - Wait timer (e.g., 5 minutes)
   - Deployment branches (restrict to `main`)

## CI/CD Integration

### Status Checks Configuration

The following GitHub Actions workflows will provide status checks:

#### Main CI Pipeline (`ci.yml`)
- `CI / test (3.10)` - Python 3.10 tests
- `CI / test (3.11)` - Python 3.11 tests
- `CI / test (3.12)` - Python 3.12 tests
- `CI / lint-and-format` - Code style validation
- `CI / build` - Package build verification

#### Quality Gates (`quality.yml`)
- `Quality Gates / security-scan` - Security vulnerability scanning
- `Quality Gates / complexity-check` - Code complexity analysis
- `Quality Gates / dependency-audit` - Dependency vulnerability check

#### Security Analysis (`codeql.yml`)
- `CodeQL / analyze` - Semantic code analysis

### Branch Protection Enforcement

Once configured, the following will be enforced:

1. **No direct pushes to main** - All changes must go through PRs
2. **Automated testing** - All tests must pass before merge
3. **Code review required** - At least 1 approval needed
4. **Security scanning** - Vulnerabilities block merges
5. **Branch up-to-date** - Must rebase/merge latest changes

## Manual Setup Steps

### 1. Enable Branch Protection
```bash
# After pushing to GitHub, go to:
# Repository Settings > Branches > Add rule
```

### 2. Configure Required Status Checks
```bash
# First, trigger a few CI runs to populate available checks
git push origin feature-branch
# Then add the check names to branch protection
```

### 3. Set up CODEOWNERS (Optional)
```bash
# Create .github/CODEOWNERS file
echo "* @your-username" > .github/CODEOWNERS
git add .github/CODEOWNERS
git commit -m "Add CODEOWNERS file"
```

## Verification

To verify branch protection is working:

1. Try to push directly to main (should fail)
2. Create a PR with failing tests (should be blocked)
3. Create a PR that passes all checks (should be mergeable)

## Troubleshooting

### Status Checks Not Appearing
- Ensure GitHub Actions have run at least once
- Check that workflow names match exactly
- Verify workflows are on the main branch

### Branch Protection Too Strict
- Temporarily disable specific rules during setup
- Use "Restrict pushes that create files" instead of blocking all pushes
- Allow administrators to bypass rules during initial setup

### False Positives
- Review security scan results and add exceptions if needed
- Adjust quality gates thresholds in workflow files
- Use `[skip ci]` in commit messages for documentation-only changes

## Best Practices

1. **Start Lenient**: Begin with basic protections and tighten over time
2. **Test Thoroughly**: Verify all CI checks work before enabling as required
3. **Document Exceptions**: Clearly document any bypasses or exceptions
4. **Regular Reviews**: Periodically review and update protection rules
5. **Team Training**: Ensure all team members understand the workflow

---

**Next Steps:** Once branch protection is configured, all future changes will go through the quality gates, ensuring the Tidal MCP maintains high code quality and reliability.
