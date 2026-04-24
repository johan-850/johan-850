import json
import os
import re
import urllib.request
from pathlib import Path


def fetch_events(user: str):
    url = f"https://api.github.com/users/{user}/events/public?per_page=30"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-activity-bot"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def build_lines(events):
    lines = []
    seen = set()

    for event in events:
        event_type = event.get("type", "")
        repo = event.get("repo", {}).get("name", "")
        created = (event.get("created_at") or "")[:10]

        if event_type == "PullRequestEvent":
            action = event.get("payload", {}).get("action", "updated")
            pr = event.get("payload", {}).get("pull_request", {})
            title = pr.get("title", "Pull Request")
            link = pr.get("html_url", "")
            if action in {"opened", "closed", "reopened", "synchronize"} and link and link not in seen:
                lines.append(f"- {created}: PR {action} en [{repo}]({link}) - {title}")
                seen.add(link)

        elif event_type == "PushEvent":
            commits = event.get("payload", {}).get("size", 0)
            key = (repo, created, commits)
            if repo and commits and commits > 0 and key not in seen:
                lines.append(f"- {created}: {commits} commit(s) en **{repo}**")
                seen.add(key)

        elif event_type == "CreateEvent":
            ref_type = event.get("payload", {}).get("ref_type", "")
            key = (repo, created, ref_type)
            if repo and ref_type == "repository" and key not in seen:
                lines.append(f"- {created}: nuevo repositorio creado **{repo}**")
                seen.add(key)

        if len(lines) >= 8:
            break

    if not lines:
        return ["- Sin actividad publica reciente para mostrar."]

    return lines


def update_readme(lines):
    readme = Path("README.md")
    content = readme.read_text(encoding="utf-8")

    start = "<!--START_SECTION:activity-->"
    end = "<!--END_SECTION:activity-->"
    block = start + "\n" + "\n".join(lines) + "\n" + end

    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), flags=re.S)
    updated = pattern.sub(block, content)
    readme.write_text(updated, encoding="utf-8")


def main():
    user = os.environ.get("GH_USER", "johan-850")
    events = fetch_events(user)
    lines = build_lines(events)
    update_readme(lines)


if __name__ == "__main__":
    main()