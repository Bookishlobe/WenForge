"""Local file system storage for WenForge projects, chapters, and settings.

Replaces Electron IPC handlers with HTTP API endpoints.
All data stored in Documents/WenForge/ (no server upload).
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("wenforge.storage")

# Base directory for all WenForge data
USER_DATA_DIR = Path.home() / "Documents" / "WenForge"
PROJECTS_DIR = USER_DATA_DIR / "stories"
SETTINGS_FILE = USER_DATA_DIR / "settings.json"


def ensure_dirs():
    """Create data directories on startup."""
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def load_settings():
    """Load settings from JSON file."""
    try:
        if SETTINGS_FILE.exists():
            return json.loads(SETTINGS_FILE.read_text("utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load settings: {e}")
    return {}


def save_settings(settings: dict) -> bool:
    """Save settings to JSON file."""
    try:
        SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), "utf-8")
        return True
    except OSError as e:
        logger.error(f"Failed to save settings: {e}")
        return False


def list_projects():
    """List all projects (directories with meta.json)."""
    try:
        if not PROJECTS_DIR.exists():
            return []
        projects = []
        for d in PROJECTS_DIR.iterdir():
            if d.is_dir():
                meta_file = d / "meta.json"
                if meta_file.exists():
                    try:
                        projects.append(json.loads(meta_file.read_text("utf-8")))
                    except (json.JSONDecodeError, OSError):
                        projects.append({"name": d.name, "title": d.name})
        return projects
    except OSError as e:
        logger.error(f"Failed to list projects: {e}")
        return []


def create_project(title: str, author: str = "", genre: str = ""):
    """Create a new project directory with meta.json."""
    dir_name = "".join(c if c not in r'\/:*?"<>|' else "_" for c in title)
    project_dir = PROJECTS_DIR / dir_name
    project_dir.mkdir(parents=True, exist_ok=True)
    chapters_dir = project_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "name": dir_name,
        "title": title,
        "author": author or "",
        "genre": genre or "",
        "createdAt": datetime.now().isoformat(),
    }
    meta_file = project_dir / "meta.json"
    meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False), "utf-8")
    return meta


def list_chapters(project_name: str):
    """List chapter files in a project."""
    chapters_dir = PROJECTS_DIR / project_name / "chapters"
    if not chapters_dir.exists():
        return []
    files = sorted(chapters_dir.glob("*.md"))
    chapters = []
    for f in files:
        stat = f.stat()
        chapters.append({
            "name": f.stem,
            "file": f.name,
            "updatedAt": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return chapters


def read_chapter(project_name: str, chapter_file: str) -> str:
    """Read chapter content."""
    file_path = PROJECTS_DIR / project_name / "chapters" / chapter_file
    if file_path.exists():
        return file_path.read_text("utf-8")
    return ""


def save_chapter(project_name: str, chapter_file: str, content: str) -> bool:
    """Save chapter content."""
    file_path = PROJECTS_DIR / project_name / "chapters" / chapter_file
    try:
        file_path.write_text(content, "utf-8")
        return True
    except OSError as e:
        logger.error(f"Failed to save chapter: {e}")
        return False


def create_chapter(project_name: str, title: str) -> str:
    """Create a new chapter file."""
    file_name = "".join(c if c not in r'\/:*?"<>|' else "_" for c in title) + ".md"
    file_path = PROJECTS_DIR / project_name / "chapters" / file_name
    if not file_path.exists():
        file_path.write_text(f"# {title}\n\n", "utf-8")
    return file_name


def delete_chapter(project_name: str, chapter_file: str) -> bool:
    """Delete a chapter file."""
    file_path = PROJECTS_DIR / project_name / "chapters" / chapter_file
    try:
        if file_path.exists():
            file_path.unlink()
        return True
    except OSError as e:
        logger.error(f"Failed to delete chapter: {e}")
        return False
