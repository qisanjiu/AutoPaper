#!/usr/bin/env python3
"""Initialize a new SpiralResearch project in the sibling directory."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from spiral.project import create_project

def main():
    topic = input("Research topic: ").strip()
    if not topic:
        print("Topic required.")
        sys.exit(1)
    name = input(f"Project name (default: auto from topic): ").strip()
    # projects_root is sibling to AutoPaper framework root
    # init_project.py -> scripts/ -> framework_root/ -> ../projects
    framework_root = Path(__file__).parent.parent.resolve()
    projects_root = framework_root.parent / "projects"
    projects_root.mkdir(parents=True, exist_ok=True)
    proj = create_project(topic, name or None, projects_root)
    print(f"\nCreated: {proj}")

if __name__ == "__main__":
    main()
