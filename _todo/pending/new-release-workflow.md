# New Release Workflow

**Status**: In Progress
**Branch**: `feature/automated-release-workflow`
**Started**: 2025-10-21

## Progress Log

### 2025-10-21

#### Initial Setup
- Proposal approved and moved to pending phase
- Created feature branch `feature/automated-release-workflow`
- Decisions finalized:
  - Manual PR approval (no auto-merge requirement)
  - Multiple bump labels allowed (applied sequentially)
  - Deprecate `python-publish.yml` entirely
  - No additional environment approvals beyond PR
  - Use PR descriptions for changelog (no automation)
  - Continue with CalVer versioning

#### Phase 1 & 2 Implementation (Completed)
- ✅ Verified all required labels exist in repository (11 bump labels + 2 release labels)
- ✅ Created `.github/workflows/version-bump.yml`
  - Triggers on PR label events
  - Applies version bumps sequentially
  - Commits changes back to PR branch
  - Posts version change comment
- ✅ Created `.github/workflows/release.yml`
  - Checks for release labels on merged PRs
  - Builds and tests package
  - Publishes to PyPI or TestPyPI
  - Creates git tag and GitHub Release
- ✅ Deleted deprecated `.github/workflows/python-publish.yml`
- ✅ Created `.github/RELEASE.md` documentation
- ✅ Updated `CLAUDE.md` with release workflow section

#### Next Steps
- Create test PR to validate version-bump workflow
- Configure GitHub Environments (pypi, testpypi)
- Configure PyPI Trusted Publishing
- Test release to TestPyPI
- Configure branch protection rules
- Test production release to PyPI

---

## Original Objective
We should move toward branch protection and automate release.

A PR should be able to start the release workflow after it's merged to main.

The steps should be the following:

1. PR gets created
2. CI test action starts running
3. If it's a release type, label gets applied, with 2 types:
   1. `release` -> publish to PyPI
   2. `test-release` -> publish to TestPyPI
   3. Also version `bump` label gets added (create a new label for each bump type `uv version --bump` supports; multiple bump labels can be added simultaneously): this needs to be its own action workflow, that will be a requirement before publishing the package
4. When CI and version bump workflow are completed, then PR can be merged
5. The release should also create a new tag with the same version number of the package just published

## Analysis

### Current State
- **Existing workflow**: `.github/workflows/python-publish.yml` publishes to PyPI on release/tag events
- **Test workflow**: `.github/workflows/test.yml` runs on PRs to main
- **No branch protection**: Main branch has no protection rules
- **No automated versioning**: Manual version updates required
- **No pre-merge version bumping**: Versions updated after merge

### Requirements Analysis

1. **Label-driven workflow**: Use labels to control release type and version bumping
2. **Version bump automation**: Automated workflow to update version based on labels
3. **Status checks**: Version bump must complete before merge is allowed
4. **Branch protection**: Enforce required checks before merging
5. **Post-merge publishing**: Automatic PyPI/TestPyPI publish after merge
6. **Tag creation**: Automatic git tag matching published version

### `uv version --bump` Options
According to `uv version --help`, supported bump types:
- `major` - X.0.0 (breaking changes)
- `minor` - 0.X.0 (new features)
- `patch` - 0.0.X (bug fixes)
- `stable` - Remove pre-release suffix
- `alpha` - Add/increment alpha version
- `beta` - Add/increment beta version
- `rc` - Add/increment release candidate
- `post` - Add/increment post-release
- `dev` - Add/increment development version

## Implementation Plan

### Step 1: Create Version Bump Labels
All labels listed here should be created (see `add-label-for-pr` task):

**Release Type Labels:**
- `release` - Publish to PyPI
- `test-release` - Publish to TestPyPI

**Version Bump Labels** (multiple can be applied):
- `bump:major`
- `bump:minor`
- `bump:patch`
- `bump:stable`
- `bump:alpha`
- `bump:beta`
- `bump:rc`
- `bump:post`
- `bump:dev`

### Step 2: Create Version Bump Workflow
**File**: `.github/workflows/version-bump.yml`

This workflow:
- Triggers when bump labels are added to PR
- Runs `uv version --bump <type>` for each bump label
- Commits the updated `pyproject.toml` and `uv.lock` back to the PR branch
- Reports success/failure as a status check

```yaml
name: Version Bump

on:
  pull_request:
    types: [labeled, synchronize]
    branches: [main]

jobs:
  bump-version:
    # Only run if PR has at least one bump: label
    if: |
      contains(github.event.pull_request.labels.*.name, 'bump:major') ||
      contains(github.event.pull_request.labels.*.name, 'bump:minor') ||
      contains(github.event.pull_request.labels.*.name, 'bump:patch') ||
      contains(github.event.pull_request.labels.*.name, 'bump:stable') ||
      contains(github.event.pull_request.labels.*.name, 'bump:alpha') ||
      contains(github.event.pull_request.labels.*.name, 'bump:beta') ||
      contains(github.event.pull_request.labels.*.name, 'bump:rc') ||
      contains(github.event.pull_request.labels.*.name, 'bump:post') ||
      contains(github.event.pull_request.labels.*.name, 'bump:dev')

    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Checkout PR branch
        uses: actions/checkout@v4
        with:
          ref: ${{ github.head_ref }}
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          version: "latest"

      - name: Get current version
        id: current-version
        run: |
          CURRENT_VERSION=$(uv version --short)
          echo "version=${CURRENT_VERSION}" >> $GITHUB_OUTPUT
          echo "Current version: ${CURRENT_VERSION}"

      - name: Apply version bumps
        id: bump
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          # Get all labels on the PR
          LABELS=$(gh pr view ${{ github.event.pull_request.number }} --json labels --jq '.labels[].name')

          # Extract bump labels in order of precedence
          BUMP_TYPES=()

          for label in major minor patch stable alpha beta rc post dev; do
            if echo "$LABELS" | grep -q "^bump:${label}$"; then
              BUMP_TYPES+=("$label")
            fi
          done

          if [ ${#BUMP_TYPES[@]} -eq 0 ]; then
            echo "No bump labels found, skipping version bump"
            exit 0
          fi

          echo "Applying bumps: ${BUMP_TYPES[*]}"

          # Apply each bump sequentially
          for bump_type in "${BUMP_TYPES[@]}"; do
            echo "Bumping: $bump_type"
            uv version --bump "$bump_type"
          done

          NEW_VERSION=$(uv version --short)
          echo "new_version=${NEW_VERSION}" >> $GITHUB_OUTPUT
          echo "New version: ${NEW_VERSION}"

      - name: Commit version bump
        if: steps.bump.outputs.new_version != ''
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          git add pyproject.toml uv.lock

          if git diff --staged --quiet; then
            echo "No changes to commit"
          else
            git commit -m "Bump version to ${{ steps.bump.outputs.new_version }}"
            git push
          fi

      - name: Comment on PR
        if: steps.bump.outputs.new_version != ''
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh pr comment ${{ github.event.pull_request.number }} --body \
            "✅ Version bumped: \`${{ steps.current-version.outputs.version }}\` → \`${{ steps.bump.outputs.new_version }}\`"
```

**Key Features:**
- Applies bumps in order of labels
- Commits changes back to PR branch
- Posts comment with version change
- Acts as required status check

### Step 3: Create Release Workflow
**File**: `.github/workflows/release.yml`

This workflow:
- Triggers when PR with `release` or `test-release` label is merged to main
- Builds the package
- Publishes to PyPI or TestPyPI based on label
- Creates a git tag matching the published version
- Creates a GitHub Release

```yaml
name: Release

on:
  pull_request:
    types: [closed]
    branches: [main]

jobs:
  check-release-label:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    outputs:
      should-release: ${{ steps.check.outputs.release }}
      is-test: ${{ steps.check.outputs.test }}
    steps:
      - name: Check for release labels
        id: check
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          LABELS=$(gh pr view ${{ github.event.pull_request.number }} --json labels --jq '.labels[].name')

          if echo "$LABELS" | grep -q "^release$"; then
            echo "release=true" >> $GITHUB_OUTPUT
            echo "test=false" >> $GITHUB_OUTPUT
          elif echo "$LABELS" | grep -q "^test-release$"; then
            echo "release=true" >> $GITHUB_OUTPUT
            echo "test=true" >> $GITHUB_OUTPUT
          else
            echo "release=false" >> $GITHUB_OUTPUT
            echo "test=false" >> $GITHUB_OUTPUT
          fi

  build:
    needs: check-release-label
    if: needs.check-release-label.outputs.should-release == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout main branch
        uses: actions/checkout@v4
        with:
          ref: main

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          version: "latest"

      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      - name: Run tests
        run: uv run pytest tests -v

      - name: Build package
        run: uv build

      - name: Get version
        id: version
        run: |
          VERSION=$(uv version --short)
          echo "version=${VERSION}" >> $GITHUB_OUTPUT
          echo "Package version: ${VERSION}"

      - name: Upload distributions
        uses: actions/upload-artifact@v4
        with:
          name: release-dists
          path: dist/

    outputs:
      version: ${{ steps.version.outputs.version }}

  publish-pypi:
    needs: [check-release-label, build]
    if: needs.check-release-label.outputs.is-test == 'false'
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    environment:
      name: pypi
      url: https://pypi.org/p/quarto-batch-convert

    steps:
      - name: Download distributions
        uses: actions/download-artifact@v4
        with:
          name: release-dists
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist/

  publish-testpypi:
    needs: [check-release-label, build]
    if: needs.check-release-label.outputs.is-test == 'true'
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    environment:
      name: testpypi
      url: https://test.pypi.org/p/quarto-batch-convert

    steps:
      - name: Download distributions
        uses: actions/download-artifact@v4
        with:
          name: release-dists
          path: dist/

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
          packages-dir: dist/

  create-tag-and-release:
    needs: [check-release-label, build, publish-pypi]
    if: |
      always() &&
      needs.check-release-label.outputs.should-release == 'true' &&
      (needs.publish-pypi.result == 'success' || needs.publish-testpypi.result == 'success')
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout main branch
        uses: actions/checkout@v4
        with:
          ref: main

      - name: Create and push tag
        env:
          VERSION: ${{ needs.build.outputs.version }}
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          git tag -a "v${VERSION}" -m "Release v${VERSION}"
          git push origin "v${VERSION}"

      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ github.token }}
          VERSION: ${{ needs.build.outputs.version }}
        run: |
          RELEASE_TYPE="${{ needs.check-release-label.outputs.is-test == 'true' && 'test' || 'production' }}"

          gh release create "v${VERSION}" \
            --title "v${VERSION}" \
            --notes "Release v${VERSION} (${RELEASE_TYPE})

            Published from PR #${{ github.event.pull_request.number }}

            See [CHANGELOG](https://github.com/${{ github.repository }}/blob/main/CHANGELOG.md) for details." \
            --draft=false \
            --prerelease=${{ needs.check-release-label.outputs.is-test == 'true' }}
```

**Key Features:**
- Only runs on merged PRs with release labels
- Separate publish jobs for PyPI vs TestPyPI
- Creates git tag after successful publish
- Creates GitHub Release with version tag
- Test releases marked as pre-release

### Step 4: Configure Branch Protection
**Repository Settings** → **Branches** → **Branch protection rules** for `main`:

Enable:
- ✅ Require a pull request before merging
  - ✅ Require approvals: 1 (optional, adjust as needed)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - **Required checks:**
    - `test` (from test.yml)
    - `bump-version` (from version-bump.yml, if bump labels present)
- ✅ Do not allow bypassing the above settings

**Notes:**
- The `bump-version` check should only be required if bump labels are present
- May need to use branch protection rules API or rulesets for conditional requirements

### Step 5: Configure PyPI Environments
**GitHub Repository Settings** → **Environments**

Create two environments:

**Environment: `pypi`**
- Required reviewers: (optional, for production safety)
- Deployment branches: Only `main`

**Environment: `testpypi`**
- Required reviewers: None
- Deployment branches: Only `main`

**PyPI Trusted Publishing:**
Both PyPI and TestPyPI need to be configured for trusted publishing:

1. Go to PyPI account settings → Publishing
2. Add publisher:
   - Repository: `kompre/quarto_batch_convert`
   - Workflow: `release.yml`
   - Environment: `pypi` (or `testpypi`)

### Step 6: Remove Existing python-publish.yml
**Decision**: Deprecate the existing `python-publish.yml` workflow entirely.

**Action**: Delete `.github/workflows/python-publish.yml` to enforce PR-based release workflow only.

**Rationale**: The new release workflow provides all necessary functionality. Keeping the old workflow could cause confusion or accidental releases.

### Step 7: Documentation

**Create `.github/RELEASE.md`:**
```markdown
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
```

**Update CLAUDE.md** with release workflow section.

## Workflow Diagram

```
┌─────────────────┐
│  Create PR      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Add Labels:    │
│  - bump:*       │──┐
│  - release OR   │  │
│    test-release │  │
└────────┬────────┘  │
         │           │
         │           ▼
         │    ┌──────────────────┐
         │    │  version-bump    │
         │    │  workflow runs   │
         │    │  (required check)│
         │    └────────┬─────────┘
         │             │
         ▼             ▼
┌─────────────────────────────┐
│  test workflow runs         │
│  (required check)           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────┐
│  PR Approved    │
│  All checks ✅  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Merge to main  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  release workflow triggers  │
│  - Build package            │
│  - Run tests                │
│  - Publish to PyPI/TestPyPI │
│  - Create git tag           │
│  - Create GitHub Release    │
└─────────────────────────────┘
```

## Success Criteria

- [ ] All version bump labels (`bump:*`) exist in repository
- [ ] Release type labels (`release`, `test-release`) exist in repository
- [ ] `version-bump.yml` workflow created and functional
- [ ] `release.yml` workflow created and functional
- [ ] Branch protection rules configured on `main` branch
- [ ] PyPI and TestPyPI environments configured
- [ ] PyPI trusted publishing configured for both environments
- [ ] Documentation created (`.github/RELEASE.md`)
- [ ] `CLAUDE.md` updated with release workflow guidance
- [ ] Successfully complete a test release to TestPyPI
- [ ] Successfully complete a production release to PyPI

## Decisions

1. **Branch Protection Strictness**:
   - **Decision**: User will manually approve PRs or toggle auto-merge
   - **Implementation**: Configure branch protection to require 1 approval (can be bypassed by repo admin)

2. **Version Bump Conflict Resolution**:
   - **Decision**: Allow multiple bump labels; they will be applied in sequence
   - **Behavior**: Workflow triggers on label events, applies all present bump labels in order (major, minor, patch, stable, alpha, beta, rc, post, dev)
   - **Note**: Order matters only if labels are added separately (triggering workflow multiple times). If added together, all bumps apply in single workflow run.

3. **Existing python-publish.yml**:
   - **Decision**: Deprecate the existing `python-publish.yml` workflow
   - **Implementation**: Remove the file entirely to enforce PR-based release workflow only

4. **TestPyPI vs PyPI Environment Protection**:
   - **Decision**: No additional environment approvals beyond PR approval
   - **Clarification**: GitHub Environments can require separate approval for deployment (independent of PR approval). We will NOT use this feature - PR approval is sufficient.
   - **Implementation**: Create environments without required reviewers

5. **Automated Changelog**:
   - **Decision**: Use PR descriptions for release notes (no automated changelog generation)
   - **Implementation**: Manual changelog updates in PR body, which can be referenced in GitHub Release notes

6. **Version Scheme**:
   - **Decision**: Continue using current CalVer (YYYY.M.D) scheme
   - **Note**: All bump types still work with CalVer (patch increments day, minor increments month, etc.)

## Estimated Complexity
**High** - Complex multi-workflow system with dependencies, branch protection, and external integrations (PyPI). Requires careful testing and likely multiple iterations.

## Implementation Phases

**Phase 1: Labels and Version Bump** (Can be done first)
- Create all labels (via `add-label-for-pr` task)
- Implement `version-bump.yml`
- Test on draft PR

**Phase 2: Release Workflow** (Depends on Phase 1)
- Implement `release.yml`
- Configure TestPyPI environment
- Test release to TestPyPI

**Phase 3: Branch Protection** (After Phase 1 & 2 working)
- Enable branch protection on main
- Add required status checks
- Test enforcement

**Phase 4: Production Release** (Final validation)
- Configure PyPI environment
- Perform production release to PyPI
- Validate tag and GitHub Release creation

## Related Tasks
- **Dependency**: `add-label-for-pr` - Must create labels before workflows can use them
- **Related**: `fix-test-workflow` - Test workflow must be working for branch protection

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Workflow publishes wrong version | Version bump must be required check; publish job reads version from built package |
| Multiple bump labels cause confusion | Apply in precedence order; document expected behavior; consider enforcing single label |
| PyPI publish fails but tag created | Tag creation happens AFTER successful publish |
| Branch protection blocks emergency fixes | Keep manual-release.yml as fallback; admin bypass available |
| Trusted publishing not configured | Detailed documentation; test with TestPyPI first |

## Testing Plan

1. **Test Version Bump Workflow**:
   - Create test PR with `bump:patch` label
   - Verify version updated in PR
   - Verify commit pushed to PR branch

2. **Test TestPyPI Release**:
   - Create test PR with `bump:patch` and `test-release` labels
   - Merge PR
   - Verify package published to TestPyPI
   - Verify tag created
   - Verify GitHub Release created (marked as pre-release)

3. **Test Production Release**:
   - Create PR with `bump:minor` and `release` labels
   - Merge PR
   - Verify package published to PyPI
   - Verify tag created
   - Verify GitHub Release created

4. **Test Branch Protection**:
   - Create PR without labels
   - Verify cannot merge without required checks
   - Add bump label
   - Verify version bump check required and passes
   - Verify can now merge
