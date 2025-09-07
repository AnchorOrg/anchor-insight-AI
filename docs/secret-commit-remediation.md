---
name: 'Doc of Git commit hook'
about: how to revert a commit and confirm that that wrong commit
title: ''
labels: ['req', ]
assignees: '@Lysander086'
---
# 📋 Checklist（必要に応じて @Your_Name をメンションしてください）

- [x] Approval from member / メンバーからの承認 [ From "Ready" to "In Progress" ( To mark the completeness and validity of this issue and removed the draft label. ) ]
- [x] Technical design document created and approved / 技術設計書の作成と技術レビュー完了

# ✅ Definition of Done (DoD)

- All requirement are implemented. 機能要件の100%実装完了.
- Check list all done.

---


# 🎯 Feature Overview / 機能概要

## 目的・背景 / Background ( Optional )

- Objective: Provide a fast, auditable way to undo an accidental commit that contains secrets (API keys, private keys, credentials) and confirm the sensitive change is no longer tracked or propagating through the repository.
- Context: This repository uses pre-commit–based secret scanning (detect-secrets and gitleaks) with Hoppscotch docs and large assets excluded. This guide standardizes the response for both “not pushed yet” and “already pushed” scenarios, ensuring key rotation, history cleanup, and verification are completed end-to-end.

## Requirements / 解決する課題

- Local-only (not pushed) bad commit: Undo the commit, remove sensitive content, recommit a sanitized version, and verify no leaks with local hooks.
- Already pushed (shared branch) bad commit: Immediately revoke/rotate the leaked secret and choose either a “revert commit (preserve history)” or “rewrite history (rebase/force-push)” to eradicate it; notify collaborators to reconcile their local history.
- Verification: Re-scan the entire repo using detect-secrets and gitleaks from pre-commit; if needed, clean Git objects to ensure the sensitive commit is unreachable.
- Note: Hoppscotch documentation files (docs/hoppscotch.*) are excluded from scanning; never store real secrets in these files.

## Use Cases (Optional) / ユーザーケース

1) Local bad commit not pushed yet (preferred)

- Undo the last commit (keep changes for cleanup):
  - `git reset --soft HEAD^`
  - Keep working tree but unstage files: `git reset HEAD .`
  - Discard all changes from the last commit (dangerous): `git reset --hard HEAD^`
- Stop tracking mistakenly added sensitive files (e.g., .env):
  - `git rm --cached .env`
  - Ensure `.gitignore` lists `.env` (it does in this repo)
- Remove secret fragments from code and rotate the secret server-side (revoke old keys).
- Recommit a sanitized version:
  - `git add -A && git commit -m "chore: sanitize secret leak"`
- Verify locally with secret scans:
  - All hooks: `pipenv run pre-commit run --all-files -v`
  - detect-secrets only: `pipenv run pre-commit run detect-secrets --all-files -v`
  - gitleaks only: `pipenv run pre-commit run gitleaks --all-files -v`
- Optional: Ensure the bad commit is unreachable locally:
  - Inspect history: `git log --oneline -n 20`
  - Check unreachable objects: `git fsck --no-reflogs --full --unreachable --lost-found`
  - Garbage-collect: `git gc --prune=now --aggressive`

2) Bad commit already pushed to a shared branch (incident response)

Short-term containment (preserve history for quick recovery):
- Immediately revoke/rotate the leaked secret (via cloud console or your KMS).
- Create a revert commit to remove the content: `git revert <leak_commit_sha>` and push normally.
- Inform the team to avoid reposting secrets in discussions, issues, or branch names.

Permanent eradication (history rewrite; requires coordination):
- Choose a tool (recommend `git filter-repo`; otherwise use BFG Repo-Cleaner):
  - Remove a file’s entire history: `git filter-repo --path .env --invert-paths`
  - Replace leaked tokens across history:
    1) Create `replacements.txt`, e.g.: `regex:(sk-[A-Za-z0-9_-]{20,})==>***REMOVED***`
    2) Run: `git filter-repo --replace-text replacements.txt`
- Force-push safely: `git push --force-with-lease origin <branch>`
- Ask collaborators to do one of the following:
  - Option A: Re-clone the repository after cleanup.
  - Option B: `git fetch --all --prune`, rebase local work on top of the updated remote history, and remove local references to rewritten commits.

Verification (local/remote parity):
- Local full scan: `pipenv run pre-commit run --all-files -v`
- Deeper gitleaks scan (non-staged): `gitleaks detect -c .gitleaks.toml --no-banner --redact -s .`
- If using GitHub Advanced Security/Secret Scanning, confirm alerts are closed or no longer triggered.

3) Sensitive samples mistakenly added to test assets or docs

- Stop tracking the leaky artifact: `git rm --cached path/to/leaky_asset`
- Regenerate or sanitize the artifact; remember Hoppscotch docs are scan-excluded—do not store real secrets there.
- Complete history cleanup and validation following the “not pushed” or “already pushed” flow as appropriate.

# 📚 Reference / リソース

- pre-commit: https://pre-commit.com/
- gitleaks: https://github.com/gitleaks/gitleaks

# 📝 Progress Update / 進捗更新

## 📅 Schedule / スケジュール

| Phase             | Real End Date | Owner | Status |
| ----------------- | ------------- | ----- | ------ |
| Analysis & Design |               |       |        |
| DEV               |               |       |        |
| Review            |               |       |        |
| QA                |               |       |        |
| PROD Deployment   |               |       |        |