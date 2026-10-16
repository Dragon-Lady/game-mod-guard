# v0.1.4

- Report unreadable directories and files instead of silently completing.
- Preserve executable STOP findings (exit 2) when metadata cannot be read.
- Refuse existing report files, symlinks, and hardlinks; create reports privately on POSIX.
- Add regression coverage and require full distribution scans before Trusted Publishing.

Directory checks inspect names and metadata, not all file content. This release does not turn the scanner into antivirus software.
