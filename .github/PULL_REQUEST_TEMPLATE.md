## Summary

What does this PR change and why?

## Related issue

Closes #

## Checklist

- [ ] Targets UE 5.9 (Win64); upstream copyright headers preserved.
- [ ] No `Intermediate/`, `Saved/`, `*.pdb`, `*.exp` committed.
- [ ] If C++ changed: rebuilt and refreshed `Binaries/Win64` drop-in binary.
- [ ] `python tools/check_repo.py` prints `RESULT: PASS`.
- [ ] If protocol/importer changed: ran `tools/validate_bridge.py` against a 5.9 editor
      (ping-only and/or full import) — see VALIDATION.md.
- [ ] Updated CHANGELOG.md and affected docs.

## Validation output

Paste the validator `RESULT_JSON=...` line or describe how you tested.
