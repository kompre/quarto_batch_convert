# Release Process

## Release Workflow

### 1. Create PR with Changes
Create a PR targeting the `main` branch with your changes.

**Tip**: Write a clear PR description - it will become your GitHub Release notes!

### 2. Bump Version Manually
On your local branch, bump the version using `uv`:

```bash
# Choose one or more bump types:
uv version --bump patch      # Bug fixes: 2025.8.11 → 2025.8.12
uv version --bump minor      # New features: 2025.8.11 → 2025.9.0
uv version --bump major      # Breaking changes: 2025.8.11 → 2026.0.0

# Pre-release versions:
uv version --bump rc         # Release candidate: 2025.9.0 → 2025.9.0rc1
uv version --bump beta       # Beta: 2025.9.0 → 2025.9.0b1
uv version --bump alpha      # Alpha: 2025.9.0 → 2025.9.0a1
uv version --bump stable     # Remove suffix: 2025.9.0rc1 → 2025.9.0

# Multiple bumps (applied sequentially):
uv version --bump minor --bump rc  # 2025.8.11 → 2025.9.0rc1
```

Commit and push the version change:
```bash
git add pyproject.toml uv.lock
git commit -m "Bump version to $(uv version --short)"
git push
```

### 3. Add Release Type Label
Add ONE of these labels to your PR:
- `release` - Publish to PyPI (production)
- `test-release` - Publish to TestPyPI (testing)

### 4. Wait for Tests
Wait for the test workflow to pass.

### 5. Merge PR
Once tests pass, merge the PR via GitHub UI.

### 6. Automatic Publishing
After merge, the release workflow automatically:
- Builds package
- Runs tests
- Publishes to PyPI or TestPyPI (based on label)
- Creates git tag (e.g., `v2025.9.0`)
- Creates GitHub Release with:
  - PR title and body as release notes
  - Installation instructions (`pipx install quarto-batch-convert`)
  - Links to package, PR, and documentation

---

## Examples

### Example 1: Patch Release to PyPI

```bash
# 1. Make your bug fix changes
# 2. Bump version
uv version --bump patch
git add pyproject.toml uv.lock
git commit -m "Bump version to $(uv version --short)"
git push

# 3. Add 'release' label to PR in GitHub UI
# 4. Merge PR
# 5. Release workflow publishes to PyPI
```

### Example 2: Test Release with RC

```bash
# 1. Make your feature changes
# 2. Bump version
uv version --bump minor --bump rc
git add pyproject.toml uv.lock
git commit -m "Bump version to $(uv version --short)"
git push

# 3. Add 'test-release' label to PR in GitHub UI
# 4. Merge PR
# 5. Release workflow publishes to TestPyPI (not production)
```

---

## Workflow Details

### Test Workflow (`test.yml`)
- **Trigger**: On pull requests to main
- **Actions**: Runs pytest test suite
- **Concurrency**: Cancels previous test runs when new commits pushed

### Release Workflow (`release.yml`)
- **Trigger**: When PR with `release` or `test-release` label is merged to main
- **Actions**:
  - Extracts PR number from merge commit
  - Builds package and runs tests
  - Publishes to PyPI or TestPyPI based on label
  - Creates git tag matching version
  - Creates GitHub Release with PR content as notes
  - Marks test releases as pre-release

---

## Troubleshooting

### Release workflow doesn't run
- Ensure PR was **merged** (not closed)
- Ensure either `release` or `test-release` label is applied
- Check workflow logs in Actions tab for errors

### PyPI publish fails
- Verify PyPI Trusted Publishing is configured correctly
- Check that GitHub environments (`pypi`, `testpypi`) are set up
- Ensure version doesn't already exist on PyPI
- Check that package builds successfully (run `uv build` locally)

### Wrong version published
- Check that you committed the version bump to the PR
- Run `uv version --short` to verify current version
- Ensure `pyproject.toml` and `uv.lock` are both committed

---

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
Main branch protection recommended settings:
- Require pull request before merging
- Require status check: `test`
- Require branches to be up to date

---

## Notes

### Why Manual Version Bumping?

The automated version-bump workflow was archived due to GitHub Actions limitations:
- Commits from `GITHUB_TOKEN` don't trigger other workflows
- This prevented tests from running after automated version bumps
- Caused auto-merge to block indefinitely waiting for test status

See `.github/workflows/archive/version-bump.yml` for details and potential future solutions using GitHub Apps.

### Version Bump Labels (Deprecated)

The following labels exist but are **not used** in the current manual workflow:
- `bump:major`, `bump:minor`, `bump:patch`
- `bump:stable`, `bump:alpha`, `bump:beta`, `bump:rc`, `bump:post`, `bump:dev`

These may be used in the future if automated version bumping is re-implemented with a GitHub App.
