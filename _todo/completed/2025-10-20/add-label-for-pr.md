# Add Label for PR

## Original Objective
The code-review workflow gets triggered by label `code-review`. Make sure it exists in GitHub.

## Analysis

The `.github/workflows/claude-code-review.yml` workflow triggers when a PR receives the `code-review` label:

```yaml
on:
  pull_request:
    types: [labeled]

jobs:
  code-review:
    if: github.event.label.name == 'code-review'
```

For this workflow to function, the `code-review` label must exist in the GitHub repository. Without it, users cannot manually apply the label to trigger the review.

## Implementation Approaches

### Option 1: Manual Label Creation (Immediate)
**Pros**: Simple, immediate solution
**Cons**: Not automated, requires repository admin access, not tracked in code

Instructions to create manually:
1. Navigate to: `https://github.com/kompre/quarto_batch_convert/labels`
2. Click "New label"
3. Name: `code-review`
4. Description: "Request automated Claude code review"
5. Color: `#0052CC` (blue) or custom preference

### Option 2: GitHub Action to Ensure Label Exists (Automated)
**Pros**: Automated, documented in code, ensures label always exists
**Cons**: Requires workflow run to create label

Create `.github/workflows/label-sync.yml` that runs on push to main and creates missing labels.

### Option 3: Label Configuration File (Best Practice)
**Pros**: Declarative, version-controlled, can sync multiple labels
**Cons**: Requires additional action/tool

Use a labels configuration file (`.github/labels.yml`) with a label sync action to maintain all repository labels.

## Recommended Implementation Plan

**Use Option 2 (Automated workflow) + Option 1 (Manual for immediate use)**

### Step 1: Create manual label immediately
Run via GitHub CLI or web UI:
```bash
gh label create "code-review" \
  --description "Request automated Claude code review" \
  --color "0052CC" \
  --repo kompre/quarto_batch_convert
```

Or provide instructions for manual creation in GitHub UI.

### Step 2: Create automated label sync workflow
**File**: `.github/workflows/ensure-labels.yml`

```yaml
name: Ensure Repository Labels

on:
  push:
    branches: [main]
    paths:
      - '.github/labels.yml'
      - '.github/workflows/ensure-labels.yml'
  workflow_dispatch:

jobs:
  sync-labels:
    runs-on: ubuntu-latest
    permissions:
      issues: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Ensure labels exist
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          # Define labels
          declare -A labels=(
            ["code-review"]="Request automated Claude code review|0052CC"
            ["release"]="Publish package to PyPI|00FF00"
            ["test-release"]="Publish package to TestPyPI|FFFF00"
            ["bump:major"]="Version bump: major|FF0000"
            ["bump:minor"]="Version bump: minor|FFA500"
            ["bump:patch"]="Version bump: patch|FFFF00"
            ["bump:stable"]="Version bump: stable|00FF00"
            ["bump:alpha"]="Version bump: alpha|0000FF"
            ["bump:beta"]="Version bump: beta|800080"
            ["bump:rc"]="Version bump: rc|FF00FF"
            ["bump:post"]="Version bump: post|00FFFF"
            ["bump:dev"]="Version bump: dev|808080"
          )

          # Create each label if it doesn't exist
          for label_name in "${!labels[@]}"; do
            IFS='|' read -r description color <<< "${labels[$label_name]}"

            if ! gh label list --json name --jq '.[].name' | grep -q "^${label_name}$"; then
              echo "Creating label: ${label_name}"
              gh label create "$label_name" \
                --description "$description" \
                --color "$color" || echo "Failed to create $label_name"
            else
              echo "Label already exists: ${label_name}"
            fi
          done
```

This workflow also pre-creates the version bump labels needed for the release workflow (see new-release-workflow task).

### Step 3: Document label usage
Add to `CLAUDE.md` or `CONTRIBUTING.md`:

```markdown
## Repository Labels

### Workflow Trigger Labels
- `code-review` - Trigger automated Claude code review on PR
- `release` - Publish package to PyPI after merge
- `test-release` - Publish package to TestPyPI after merge

### Version Bump Labels
Applied to PRs to indicate semantic version increment:
- `bump:major` - Breaking changes (X.0.0)
- `bump:minor` - New features (0.X.0)
- `bump:patch` - Bug fixes (0.0.X)
- `bump:stable` - Remove pre-release suffix
- `bump:alpha`, `bump:beta`, `bump:rc`, `bump:post`, `bump:dev` - Pre-release versions
```

## Implementation Progress

### 2025-10-20: Labels Created Successfully ✅

All labels have been created manually using GitHub API via `gh api`:

**Created Labels:**
1. ✅ `code-review` - Request automated Claude code review (0052CC)
2. ✅ `release` - Publish package to PyPI (00FF00)
3. ✅ `test-release` - Publish package to TestPyPI (FFFF00)
4. ✅ `bump:major` - Version bump: major (FF0000)
5. ✅ `bump:minor` - Version bump: minor (FFA500)
6. ✅ `bump:patch` - Version bump: patch (FFFF00)
7. ✅ `bump:stable` - Version bump: stable (00FF00)
8. ✅ `bump:alpha` - Version bump: alpha (0000FF)
9. ✅ `bump:beta` - Version bump: beta (800080)
10. ✅ `bump:rc` - Version bump: rc (FF00FF)
11. ✅ `bump:post` - Version bump: post (00FFFF)
12. ✅ `bump:dev` - Version bump: dev (808080)

All labels are now available at: https://github.com/kompre/quarto_batch_convert/labels

**Decision**: Following user preference, labels were created manually without automation workflow.

## Success Criteria

- [x] `code-review` label exists in repository
- [x] Label is usable in PR workflows
- [ ] Optional: Automated label sync workflow prevents label deletion (skipped per user request)
- [x] Optional: All future workflow labels (release, bump:*) are pre-created
- [x] Documentation exists for label usage

## Task Complete ✅

All labels have been successfully created and documented. The task is ready to be archived to `_todo/completed/2025-10-20/`.

## Questions/Decisions Needed

1. **Immediate vs Automated**: Create label manually now, or wait for automated workflow?
   - **Recommendation**: Do both - manual for immediate use, workflow for future maintenance

2. **Additional Labels**: Should we create all labels (release, bump:*) now or wait for release workflow implementation?
   - **Recommendation**: Create all at once since we know the requirements

3. **Label Colors/Descriptions**: Any specific preferences for visual organization?
   - **Recommendation**: Use standard color scheme (blue for workflow, green/yellow/red for release types, rainbow for bump types)

## Estimated Complexity
**Low** - Simple label creation, either manual or automated. The workflow approach adds value for future maintenance.

## Related Tasks
This task enables:
- `claude-code-review.yml` workflow to function correctly
- Future `new-release-workflow` implementation (requires `release`, `test-release`, and `bump:*` labels)

<!-- just create them manually, no need for automation -->