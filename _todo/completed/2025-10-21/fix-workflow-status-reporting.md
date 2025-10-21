# Fix Workflow Status Reporting and Auto-Merge

## Problem Analysis

### Current Issues

1. **workflow_run doesn't report status to PR**
   - Test workflow triggered via `workflow_run` runs in **main branch context**
   - Status check not associated with PR commit
   - Branch protection can't see the test result
   - Auto-merge blocked indefinitely

2. **Version bump triggers multiple times**
   - Concurrency control working but cancellations happen after work starts
   - First run (25s) commits version before being cancelled
   - Second run commits again (different version)
   - Wasteful and confusing

3. **Root cause: GITHUB_TOKEN limitations**
   - Commits made with `secrets.GITHUB_TOKEN` deliberately **don't trigger workflows**
   - GitHub's safeguard against infinite workflow loops
   - We're fighting against this design

### Why workflow_run Doesn't Work

From GitHub docs and common issues:
- `workflow_run` executes in the context of the **default branch** (main)
- It does NOT run "on behalf of" the PR
- Status checks created are for the wrong commit SHA
- Branch protection rules on PR don't see these checks

## Best Practice Solutions

### Option A: Use GitHub App or PAT (Recommended)

**How it works:**
1. Create GitHub App or use Personal Access Token (PAT)
2. Store token as repository secret (e.g., `BOT_TOKEN`)
3. Use this token for version bump commits instead of `GITHUB_TOKEN`
4. Commits from this token **DO trigger workflows normally**
5. Test runs automatically, reports to PR, auto-merge works

**Pros:**
- ✅ Clean, standard solution used by major projects
- ✅ No workflow_run hacks
- ✅ Status checks report correctly
- ✅ No manual API calls needed

**Cons:**
- ⚠️ Requires creating GitHub App or PAT
- ⚠️ Additional secret to manage
- ⚠️ Security consideration (token has write access)

**Implementation:**
```yaml
# version-bump.yml
- uses: actions/checkout@v4
  with:
    token: ${{ secrets.BOT_TOKEN }}  # Instead of GITHUB_TOKEN

# Rest of workflow unchanged - commits will trigger test.yml normally
```

**Examples in the wild:**
- Renovate Bot (uses GitHub App)
- Dependabot (uses GitHub App)
- Many semantic-release setups (use PAT)

### Option B: Manual Status Check via API

**How it works:**
1. Version bump workflow commits changes
2. Version bump workflow manually creates passing "test" status via API
3. References the test run that already passed before version bump
4. Auto-merge sees the status and proceeds

**Pros:**
- ✅ No additional tokens needed
- ✅ Uses existing test results

**Cons:**
- ⚠️ Hacky - we're asserting tests pass without re-running them
- ⚠️ Tests don't actually run on bumped version
- ⚠️ Complex API calls in workflow

**Implementation:**
```yaml
# version-bump.yml - after commit
- name: Create test status check
  env:
    GH_TOKEN: ${{ github.token }}
  run: |
    gh api repos/${{ github.repository }}/statuses/${{ github.event.pull_request.head.sha }} \
      -f state=success \
      -f context=test \
      -f description="Tests passed before version bump"
```

### Option C: Remove Auto-Merge (Simplest)

**How it works:**
1. Version bump commits changes
2. User reviews the version bump
3. User manually merges (or clicks merge button)
4. Release workflow triggers

**Pros:**
- ✅ Extremely simple
- ✅ No workflow complexity
- ✅ Human verification of version
- ✅ No token management

**Cons:**
- ⚠️ Not fully automated
- ⚠️ Requires manual action

**Implementation:**
- Remove auto-merge enable step from version-bump.yml
- User merges when ready

### Option D: workflow_dispatch Chain

**How it works:**
1. Version bump commits changes
2. Version bump triggers test via `workflow_dispatch`
3. Test workflow runs in PR context (because we pass the ref)
4. Status reported correctly

**Pros:**
- ✅ No tokens needed
- ✅ Tests run on bumped version
- ✅ Status reports correctly

**Cons:**
- ⚠️ More complex workflow coordination
- ⚠️ Need to pass PR context manually

**Implementation:**
```yaml
# version-bump.yml - after commit
- name: Trigger test workflow
  env:
    GH_TOKEN: ${{ github.token }}
  run: |
    gh workflow run test.yml \
      -f pr_number=${{ github.event.pull_request.number }} \
      -f sha=${{ github.event.pull_request.head.sha }}

# test.yml - add workflow_dispatch trigger
on:
  pull_request:
  workflow_dispatch:
    inputs:
      pr_number:
        required: true
      sha:
        required: true
```

## Recommendation

**Option A (GitHub App/PAT)** is the industry standard and cleanest solution, BUT requires setup.

**Option C (Remove Auto-Merge)** is simplest if you don't mind one manual step.

**For this project, I recommend:**
1. **Short-term: Option C** - Remove auto-merge, keep workflows simple
2. **Long-term: Option A** - If you want full automation, set up GitHub App

## Proposed Implementation (Option C - Simple)

### Changes:
1. **Remove auto-merge step** from version-bump.yml
2. **Remove workflow_run trigger** from test.yml (back to pull_request only)
3. **Update documentation** - user merges after reviewing version bump

### Updated Flow:
1. Create PR with changes
2. Add `bump:*` labels
3. Version bump workflow commits new version
4. **User reviews version bump**
5. **User merges PR** (via UI or gh CLI)
6. Release workflow publishes package

### Pros:
- ✅ Simple, no complex workflow orchestration
- ✅ Human verification of version before release
- ✅ No token management
- ✅ No status check issues
- ✅ Tests run normally on PR

### Cons:
- One manual step (clicking merge button)

## Alternative Recommendation (Option A - Fully Automated)

If you want full automation:

### Setup GitHub App (one-time):
1. Create GitHub App with repo write permissions
2. Install on repository
3. Store private key or create installation token
4. Add as repository secret: `BOT_TOKEN`

### Changes:
1. version-bump.yml: Use `BOT_TOKEN` instead of `GITHUB_TOKEN`
2. test.yml: Back to simple `pull_request` trigger
3. Keep auto-merge step

### Flow:
1. Add labels → version bump commits → test runs → auto-merge → release

Fully automated, no manual steps.

## Questions

1. Do you want full automation (Option A - requires GitHub App setup)?
2. Or accept one manual step for simplicity (Option C - remove auto-merge)?
3. Or try the workflow_dispatch approach (Option D - no tokens, moderately complex)?

<!-- if we have to do version bump manually, then the workflow can be disabled entirely. I will do a manual cli `uv version ...` and commit to the project

add concurrency to the test workflow, so that it will cancel previous, no need to run multiple times.

 -->