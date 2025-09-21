# Branch Protection Configuration

This document outlines the recommended branch protection rules for the Tidal MCP repository.

## Main Branch Protection

Apply these settings to the `main` branch:

### Required Status Checks
- **Require status checks to pass before merging**: ✅ Enabled
- **Require branches to be up to date before merging**: ✅ Enabled

**Required Checks:**
- `CI / Test Python 3.10 on ubuntu-latest`
- `CI / Test Python 3.11 on ubuntu-latest`
- `CI / Test Python 3.12 on ubuntu-latest`
- `CI / Security Scan`
- `CI / Build Package`
- `Quality Gates / Code Quality Assessment`
- `Quality Gates / Dependency Audit`
- `Quality Gates / Documentation Quality Check`
- `CodeQL Advanced Security / Analyze (python)`
- `PR Validation / Quick Validation Checks`
- `PR Validation / Quick Test Subset`

### Pull Request Requirements
- **Require a pull request before merging**: ✅ Enabled
- **Require approvals**: ✅ Enabled (minimum 1 approval)
- **Dismiss stale pull request approvals**: ✅ Enabled
- **Require review from code owners**: ✅ Enabled
- **Restrict approvals to members of specific teams**: ✅ Enabled
  - Teams: `@tidal-mcp/maintainers`, `@tidal-mcp/core-team`

### Additional Restrictions
- **Restrict pushes that create files**: ❌ Disabled
- **Require signed commits**: ✅ Enabled (recommended)
- **Require linear history**: ✅ Enabled
- **Allow force pushes**: ❌ Disabled
- **Allow deletions**: ❌ Disabled

### Administrative Settings
- **Include administrators**: ✅ Enabled
- **Allow specified actors to bypass required pull requests**: ❌ Disabled

## Develop Branch Protection

Apply these settings to the `develop` branch (if using GitFlow):

### Required Status Checks
- **Require status checks to pass before merging**: ✅ Enabled
- **Require branches to be up to date before merging**: ✅ Enabled

**Required Checks:**
- `CI / Test Python 3.11 on ubuntu-latest` (minimum subset)
- `PR Validation / Quick Validation Checks`
- `PR Validation / Quick Test Subset`

### Pull Request Requirements
- **Require a pull request before merging**: ✅ Enabled
- **Require approvals**: ✅ Enabled (minimum 1 approval)
- **Dismiss stale pull request approvals**: ❌ Disabled (more lenient for development)
- **Require review from code owners**: ❌ Disabled (more lenient for development)

### Additional Restrictions
- **Require linear history**: ❌ Disabled (allow merge commits in develop)
- **Allow force pushes**: ❌ Disabled
- **Allow deletions**: ❌ Disabled

## Release Branch Protection

For release branches (`release/*`):

### Required Status Checks
- **Require status checks to pass before merging**: ✅ Enabled
- **Require branches to be up to date before merging**: ✅ Enabled

**Required Checks:**
- Full CI suite (all Python versions, all platforms)
- Security scans
- Quality gates

### Pull Request Requirements
- **Require a pull request before merging**: ✅ Enabled
- **Require approvals**: ✅ Enabled (minimum 2 approvals)
- **Require review from code owners**: ✅ Enabled

## Configuration via GitHub CLI

You can apply these settings using the GitHub CLI:

```bash
# Main branch protection
gh api repos/tidal-mcp/tidal-mcp/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["CI / Test Python 3.11 on ubuntu-latest","CI / Security Scan","Quality Gates / Code Quality Assessment"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false

# Develop branch protection (if applicable)
gh api repos/tidal-mcp/tidal-mcp/branches/develop/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["CI / Test Python 3.11 on ubuntu-latest","PR Validation / Quick Validation Checks"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":false,"require_code_owner_reviews":false}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

## Configuration via Terraform (Optional)

If using Infrastructure as Code:

```hcl
resource "github_branch_protection" "main" {
  repository_id = "tidal-mcp"
  pattern       = "main"

  required_status_checks {
    strict = true
    contexts = [
      "CI / Test Python 3.10 on ubuntu-latest",
      "CI / Test Python 3.11 on ubuntu-latest",
      "CI / Test Python 3.12 on ubuntu-latest",
      "CI / Security Scan",
      "Quality Gates / Code Quality Assessment",
      "CodeQL Advanced Security / Analyze (python)"
    ]
  }

  required_pull_request_reviews {
    required_approving_review_count = 1
    dismiss_stale_reviews          = true
    require_code_owner_reviews     = true
    restrict_dismissals            = true
    dismissal_restrictions         = ["tidal-mcp/maintainers"]
  }

  enforce_admins        = true
  allows_deletions     = false
  allows_force_pushes  = false
  require_signed_commits = true
}
```

## Manual Configuration Steps

1. **Navigate to Settings** → **Branches** in your GitHub repository
2. **Click "Add rule"** or edit existing protection rule for `main`
3. **Configure the settings** as outlined above
4. **Save the protection rule**
5. **Repeat for other protected branches** (`develop`, `release/*`)

## Code Owners File

Create a `.github/CODEOWNERS` file to specify review requirements:

```
# Global owners
* @tidal-mcp/maintainers

# CI/CD and deployment
/.github/ @tidal-mcp/devops @tidal-mcp/maintainers
/pyproject.toml @tidal-mcp/maintainers
/requirements*.txt @tidal-mcp/maintainers

# Core application code
/src/ @tidal-mcp/core-team @tidal-mcp/maintainers

# Tests
/tests/ @tidal-mcp/qa-team @tidal-mcp/core-team

# Documentation
/docs/ @tidal-mcp/docs-team
README.md @tidal-mcp/docs-team @tidal-mcp/maintainers
```

## Troubleshooting

### Common Issues

1. **Status checks not appearing**: Ensure the workflow has run at least once on the branch
2. **Required checks failing**: Verify all specified check names match exactly with workflow job names
3. **Admin bypass not working**: Check that "Include administrators" is properly configured

### Updating Protection Rules

When adding new required checks:
1. Add the new workflow/job
2. Let it run successfully on a test PR
3. Update the branch protection rule to include the new check
4. Verify the check appears in the required list

## Security Considerations

- **Enable signed commits** to ensure commit authenticity
- **Require code owner reviews** for sensitive areas
- **Use least privilege** for team permissions
- **Regularly audit** protection rules and team memberships
- **Monitor bypass events** in audit logs

## Monitoring and Alerts

Set up monitoring for:
- Failed required status checks
- Branch protection rule changes
- Bypass events
- Failed merge attempts

Use GitHub's audit log and webhooks to track these events.
