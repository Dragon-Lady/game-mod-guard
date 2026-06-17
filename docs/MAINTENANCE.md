# Maintenance

Game Mod Guard should stay boring, small, and read-only.

## Monthly Check

Once a month:

1. Check open issues for false positives or missed risky files.
2. Search public reporting for game mod malware, fake mod installers, Steam
   Workshop issues, and new archive tricks.
3. Add new risky extensions or patterns only when they are defensible.
4. Run the test suite:

   ```bash
   python -m unittest discover -s tests -v
   ```

5. Test one safe-looking archive and one STOP archive manually.
6. If behavior changes, bump the version in both:
   - `pyproject.toml`
   - `game_mod_guard.py`
7. Tag a release if PyPI users should upgrade.

## Release Checklist

1. Confirm the tree is clean except intended changes.
2. Run:

   ```bash
   python -m py_compile game_mod_guard.py tests/test_game_mod_guard.py
   python -m unittest discover -s tests -v
   ```

3. Update README if install or output changed.
4. Commit and push.
5. Create a GitHub Release tag such as `v0.1.1`.
6. The PyPI workflow publishes when a release is created.

## Boundaries

- Do not delete files.
- Do not quarantine files automatically.
- Do not upload mods to third-party services by default.
- Do not claim a clean scan proves a mod is safe.
- Keep output simple enough for non-technical players.

