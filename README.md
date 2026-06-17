# Game Mod Guard

Read-only safety checker for downloaded game mods and mod archives.

Game Mod Guard helps players review Farming Simulator, American Truck Simulator,
Euro Truck Simulator, and other game mod downloads before installing them. It
does not prove a mod is safe, but it catches common "stop and look closer" signs:
executables hiding in archives, scripts, nested archives, shortcut files, odd
file types, and Microsoft Defender detections when Defender is available.

## What It Does

- Scans files, folders, `.zip`, and `.scs` archives without running the mod.
- Computes SHA-256 hashes for downloaded files.
- Flags risky file types such as `.exe`, `.msi`, `.bat`, `.cmd`, `.ps1`, `.js`,
  `.vbs`, `.scr`, and `.lnk`.
- Flags nested archives and very large archives for review.
- Calls Microsoft Defender on Windows when `MpCmdRun.exe` is available.
- Prints a simple result: `SAFE-LOOKING`, `REVIEW`, or `STOP`.
- Gives plain removal guidance, but never deletes anything.

## Easiest Windows Setup

This is the simple version for normal players.

1. Install Python from the Microsoft Store or from <https://www.python.org/downloads/>.
   During install, turn on **Add python.exe to PATH** if you see that checkbox.
2. Go to the Game Mod Guard GitHub page.
3. Click the green **Code** button.
4. Click **Download ZIP**.
5. Open your Downloads folder.
6. Right-click the downloaded `game-mod-guard-main.zip`.
7. Click **Extract All...**.
8. Open the extracted `game-mod-guard-main` folder.
9. Find `scan-mod.bat`.
10. Drag a downloaded mod file onto `scan-mod.bat`.

You do **not** need to unzip the game mod first. Drag the mod download itself,
such as `.zip`, `.scs`, or a mod folder, onto `scan-mod.bat`.

If Windows asks whether to run the batch file, choose **Run**. Game Mod Guard is
read-only: it scans and reports, but it does not delete or change the mod.

Important: the GitHub ZIP download does **not** auto-update. To update this
simple version later, download the newest ZIP from GitHub again and extract it
over the old folder.

## Normal Use

After setup, use it like this:

1. Download a mod.
2. Do not open or install it yet.
3. Drag the downloaded mod onto `scan-mod.bat`.
4. Read the result.

If it says `SAFE-LOOKING`, the scanner did not find its known warning signs.

If it says `REVIEW`, ask a technical friend to check it before installing.

If it says `STOP`, do not install it. Delete that downloaded mod and get the mod
from a safer source.

## Brayden / Computer Friend Setup

If you are comfortable with Python packages, install from PyPI:

```powershell
py -m pip install --user game-mod-guard
```

Run it:

```powershell
py -m game_mod_guard "C:\Users\you\Downloads\some-mod.zip"
```

Upgrade later:

```powershell
py -m pip install --user --upgrade game-mod-guard
```

If Windows put Python scripts on PATH, this also works:

```powershell
game-mod-guard "C:\Users\you\Downloads\some-mod.zip"
```

For release/publishing notes, see [docs/PUBLISHING.md](docs/PUBLISHING.md).

## Command Line Use

Windows:

```powershell
python game_mod_guard.py "C:\Users\you\Downloads\some-mod.zip"
```

Linux/macOS:

```bash
python3 game_mod_guard.py ~/Downloads/some-mod.zip
```

Scan several downloads at once:

```bash
python3 game_mod_guard.py ~/Downloads/mod1.zip ~/Downloads/mod2.scs
```

Write a JSON report:

```bash
python3 game_mod_guard.py ~/Downloads/mod.zip --json report.json
```

## How To Read Results

`SAFE-LOOKING` means Game Mod Guard did not find its known local warning signs.
It is not a guarantee. Prefer official sources like GIANTS ModHub, Steam
Workshop, and trusted mod communities.

`REVIEW` means the mod has something unusual: scripts, nested archives,
unexpected file types, a huge archive, or the scanner could not inspect all
contents. Ask a technical friend to review before installing.

`STOP` means the mod contains executable-style content or Microsoft Defender
reported a detection. Do not install it. Delete the downloaded mod file and get
the mod from a safer source.

## If Python Is Missing

If `scan-mod.bat` says Python is missing:

1. Open the Microsoft Store.
2. Search for **Python**.
3. Install the newest Python 3 version.
4. Try dragging the mod onto `scan-mod.bat` again.

Brayden/computer-friend route: install Python from <https://www.python.org/downloads/>
and enable **Add python.exe to PATH** during install.

## Good Habits

- Avoid `.exe` installers for normal mods.
- Avoid password-protected archives.
- Avoid "download manager" buttons and random mirror sites.
- Keep Windows Security / Microsoft Defender enabled.
- Prefer official ModHub and Steam Workshop downloads.

## Scope

This is a local, read-only scanner. It does not upload files, contact a cloud
scanner, remove malware, or modify mods. If you already ran a suspicious file,
use Windows Security Offline Scan or ask a trusted technician for help.
