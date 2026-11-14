# 23 — Development workflow

1. Create a Git branch before making changes.
2. Read `AGENTS.md` and relevant docs.
3. Inspect exact source paths and current git diff.
4. Define a narrow issue, expected behavior, and acceptance criteria.
5. Make minimal changes.
6. Run `npm run lint` and `npm run build` for frontend changes.
7. For backend changes, run syntax/import tests and relevant API/pipeline tests.
8. If pipeline changes, test with a known sample video and preserve logs/artifacts.
9. Update API contract, PRD, testing notes, and changelog as needed.
10. Review diff for unrelated edits, secrets, absolute paths, and data deletion.
11. Commit changes with a concise message and open a PR if collaborating.

## Pull request checklist
- [ ] Requirements and scope described
- [ ] Source changes limited to intended area
- [ ] Tests executed and results stated
- [ ] No secrets or personal paths added
- [ ] API/docs updated if contract changed
- [ ] Known limitations listed
- [ ] Sample output or screenshots attached when useful
