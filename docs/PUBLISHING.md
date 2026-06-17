# Publishing To PyPI

Package name: `game-mod-guard`

The recommended publish path is PyPI Trusted Publishing from GitHub Actions.
This avoids storing a PyPI API token in the repo.

## One-Time PyPI Setup

1. Create or log into a PyPI account.
2. Create the `game-mod-guard` project on PyPI, or use PyPI's pending publisher
   flow when creating the first release.
3. Add a trusted publisher for this GitHub repository:
   - Owner: `Dragon-Lady`
   - Repository: `game-mod-guard`
   - Workflow: `publish.yml`
   - Environment: leave blank unless the workflow is changed to use one

## Release

1. Bump the version in `pyproject.toml` and `game_mod_guard.py`.
2. Run tests.
3. Commit and push.
4. Create a GitHub Release with a tag matching the package version, such as
   `v0.1.1`.
5. GitHub Actions builds and publishes to PyPI.

## Brayden Install / Upgrade

Install with pip:

```powershell
py -m pip install --user game-mod-guard
```

Upgrade later:

```powershell
py -m pip install --user --upgrade game-mod-guard
```

Run:

```powershell
py -m game_mod_guard "C:\Users\you\Downloads\some-mod.zip"
```

If the `game-mod-guard` command is on PATH, this also works:

```powershell
game-mod-guard "C:\Users\you\Downloads\some-mod.zip"
```
