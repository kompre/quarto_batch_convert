# Release Process

## Automated Release Workflow

### 1. Create PR with Changes
Create a PR targeting the `main` branch with your changes.

### 2. Add Version Bump Label
Add ONE OR MORE of these labels to indicate version change:
- `bump:major` - Breaking changes (2025.8.11 → 2026.0.0)
- `bump:minor` - New features (2025.8.11 → 2025.9.0)
- `bump:patch` - Bug fixes (2025.8.11 → 2025.8.12)
- `bump:stable` - Remove pre-release suffix
- `bump:alpha`, `bump:beta`, `bump:rc`, `bump:post`, `bump:dev` - Pre-release

The version-bump workflow will automatically update `pyproject.toml` and commit to your PR.

### 3. Add Release Type Label
Add ONE of these labels:
- `release` - Publish to PyPI (production)
- `test-release` - Publish to TestPyPI (testing)

### 4. Wait for Checks
Required checks must pass:
- ✅ Tests (`test.yml`)
- ✅ Version bump (`version-bump.yml`, if bump labels present)

### 5. Merge PR
Once approved and checks pass, merge the PR.

### 6. Automatic Publishing
After merge:
- Package is built and tested
- Published to PyPI or TestPyPI
- Git tag created (e.g., `v2025.9.0`)
- GitHub Release created

## Example: Patch Release to PyPI

1. Create PR: "Fix bug in file collection"
2. Add labels: `bump:patch`, `release`
3. Version bump workflow: `2025.8.11` → `2025.8.12`
4. Merge PR
5. Release workflow publishes to PyPI and creates tag `v2025.8.12`

## Example: Test Release

1. Create PR: "Test new feature"
2. Add labels: `bump:minor`, `bump:beta`, `test-release`
3. Version bump workflow: `2025.8.11` → `2025.9.0b1`
4. Merge PR
5. Release workflow publishes to TestPyPI (not production PyPI)

## Multiple Version Bumps

You can apply multiple bump labels simultaneously. They will be applied sequentially in this order: major, minor, patch, stable, alpha, beta, rc, post, dev.

Example:
- Labels: `bump:minor`, `bump:rc`
- Result: `2025.8.11` → `2025.9.0rc1`

## Workflow Details

### Version Bump Workflow (`version-bump.yml`)
- **Trigger**: When bump labels are added to a PR targeting main
- **Actions**:
  - Applies version bumps using `uv version --bump <type>`
  - Commits updated `pyproject.toml` and `uv.lock` to PR branch
  - Posts comment with version change
  - Acts as required status check

### Release Workflow (`release.yml`)
- **Trigger**: When PR with release label is merged to main
- **Actions**:
  - Builds package
  - Runs tests
  - Publishes to PyPI or TestPyPI based on label
  - Creates git tag matching version
  - Creates GitHub Release
  - Test releases marked as pre-release

## Troubleshooting

### Version bump workflow doesn't run
- Ensure at least one `bump:*` label is applied
- Check that PR targets the `main` branch
- Verify workflow file is present in `.github/workflows/version-bump.yml`

### Release workflow doesn't run
- Ensure PR was merged (not closed)
- Ensure either `release` or `test-release` label is applied
- Check workflow logs for errors

### PyPI publish fails
- Verify PyPI Trusted Publishing is configured correctly
- Check that GitHub environments (`pypi`, `testpypi`) are set up
- Ensure version doesn't already exist on PyPI

## Configuration Requirements

### GitHub Environments
Two environments must be configured in repository settings:
- `pypi` - For production releases
- `testpypi` - For test releases

### PyPI Trusted Publishing
Configure at https://pypi.org/manage/account/publishing/:
- Repository: `kompre/quarto_batch_convert`
- Workflow: `release.yml`
- Environment: `pypi` (and separately for `testpypi`)

### Branch Protection
Main branch should have:
- Require pull request before merging
- Require status checks: `test`, `bump-version`
- Require branches to be up to date
