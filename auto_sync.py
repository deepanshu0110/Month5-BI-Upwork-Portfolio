"""
Month 5 — Auto Sync Script
Watches C:\\Users\\Deepanshu\\OneDrive\\Desktop\\Month5
Auto commits and pushes to deepanshu0110/Month5-BI-Upwork-Portfolio
Tracks: .xlsx, .pbix, .twbx, .ipynb, .pdf, .py, .md

Usage:
    cd "C:\\Users\\Deepanshu\\OneDrive\\Desktop\\Month5"
    python auto_sync.py

Stop: Ctrl+C
"""

import subprocess
import time
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_FOLDER  = r"C:\Users\Deepanshu\OneDrive\Desktop\Month5"
TRACKED_EXTS  = {".xlsx", ".pbix", ".twbx", ".ipynb", ".pdf", ".py", ".md"}
BRANCH        = "main"
REMOTE        = "origin"
DEBOUNCE_SECS = 2.0   # wait before committing (file must finish saving)

# ── README template ───────────────────────────────────────────────────────────
README_TEMPLATE = """# Month 5 — BI Depth + Upwork Activation Portfolio

**Author:** Deepanshu Garg | [deepanshu0110](https://github.com/deepanshu0110)

Part of a structured 12-month Data Analytics + Data Science program.
Month 5 covers advanced Power BI, advanced Tableau, end-to-end analytics pipelines,
and Upwork activation (first 5 bids in Week 4).

---

## Tableau Public Portfolio
[TechMart India Sales Story](https://public.tableau.com/app/profile/deepanshu.garg8585/viz/TechMart-India-Sales-Story/TechMartIndiaSalesStory)

---

## Month Schedule

| Week | Focus | Status |
|------|-------|--------|
| Week 1 | Advanced Power BI (RLS, Bookmarks, Drill-through) | ⏳ |
| Week 2 | Advanced Tableau (LOD, Parameters, Storytelling) | ⏳ |
| Week 3 | End-to-end pipeline: SQL → Python EDA → BI Dashboard | ⏳ |
| Week 4 | Upwork activation — first 5 proposals sent | ⏳ |

---

## Files

{file_list}

---

## Tools
Power BI Desktop · Tableau Public · Python · Pandas · SQL · Excel

## Connect
- GitHub: [deepanshu0110](https://github.com/deepanshu0110)
- Tableau Public: [Profile](https://public.tableau.com/app/profile/deepanshu.garg8585)
"""

def run(cmd):
    """Run a shell command and return output."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        cwd=WATCH_FOLDER
    )
    return result.stdout.strip(), result.stderr.strip()

def get_file_list():
    """Build a markdown list of all tracked files in the folder."""
    lines = []
    for f in sorted(os.listdir(WATCH_FOLDER)):
        ext = os.path.splitext(f)[1].lower()
        if ext in TRACKED_EXTS and f != "auto_sync.py":
            size_kb = os.path.getsize(os.path.join(WATCH_FOLDER, f)) // 1024
            lines.append(f"- `{f}` ({size_kb} KB)")
    return "\n".join(lines) if lines else "_No files yet._"

def update_readme():
    """Regenerate README.md with current file list."""
    readme_path = os.path.join(WATCH_FOLDER, "README.md")
    content = README_TEMPLATE.format(file_list=get_file_list())
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

def git_push(filename):
    """Stage, commit, push."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    update_readme()

    out, err = run("git add -A")
    
    # Check if there's actually anything to commit
    status, _ = run("git status --porcelain")
    if not status:
        print(f"  [skip] No changes to commit for {filename}")
        return

    commit_msg = f"feat: add/update {filename} [{now}]"
    out, err = run(f'git commit -m "{commit_msg}"')
    print(f"  Committed: {commit_msg}")

    out, err = run(f"git push {REMOTE} {BRANCH}")
    if err and "error" in err.lower():
        print(f"  ⚠ Push error: {err}")
    else:
        print(f"  ✅ Pushed to GitHub: {BRANCH}")

class SyncHandler(FileSystemEventHandler):
    def __init__(self):
        self._pending = {}

    def should_track(self, path):
        ext = os.path.splitext(path)[1].lower()
        name = os.path.basename(path)
        return ext in TRACKED_EXTS and not name.startswith("~$")

    def schedule_push(self, path):
        if not self.should_track(path):
            return
        filename = os.path.basename(path)
        print(f"\n  Detected: {filename} — waiting {DEBOUNCE_SECS}s...")
        self._pending[path] = time.time()

    def on_created(self, event):
        if not event.is_directory:
            self.schedule_push(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.schedule_push(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.schedule_push(event.dest_path)

    def flush_pending(self):
        """Push files that have been stable for DEBOUNCE_SECS."""
        now = time.time()
        to_push = [
            p for p, t in self._pending.items()
            if now - t >= DEBOUNCE_SECS
        ]
        for path in to_push:
            del self._pending[path]
            filename = os.path.basename(path)
            print(f"\n  Syncing: {filename}")
            git_push(filename)

def main():
    print("=" * 55)
    print("  Month 5 Auto Sync — deepanshu0110")
    print(f"  Watching: {WATCH_FOLDER}")
    print(f"  Tracking: {', '.join(sorted(TRACKED_EXTS))}")
    print("  Press Ctrl+C to stop")
    print("=" * 55)

    if not os.path.exists(WATCH_FOLDER):
        print(f"\n⚠  Folder not found: {WATCH_FOLDER}")
        print("Create it first, then rerun this script.")
        return

    # Initial README push on startup
    print("\n  Initialising README...")
    git_push("README.md (startup)")

    handler = SyncHandler()
    observer = Observer()
    observer.schedule(handler, WATCH_FOLDER, recursive=False)
    observer.start()
    print("\n  Watching for changes...\n")

    try:
        while True:
            handler.flush_pending()
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n  Auto Sync stopped. Goodbye.")
    observer.join()

if __name__ == "__main__":
    main()
