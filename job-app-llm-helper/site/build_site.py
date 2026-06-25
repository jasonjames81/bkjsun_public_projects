"""Render site/index.html by injecting canonical paste-blocks from platform-guide/*.md.

Stdlib only. Run after editing any of the three source guides:
    python site/build_site.py
The rendered index.html is committed; do not hand-edit the INJECT regions.
"""

from __future__ import annotations

import html as html_mod
import re
from pathlib import Path

# (source markdown filename, marker name, extractor function name)
BLOCKS = [
    ("project-instructions.md", "project-instructions", "below_divider"),
    ("kickoff-template.md", "kickoff", "message_body"),
    ("interview-prep-template.md", "interview-prep", "message_body"),
]


def extract_below_divider(md: str) -> str:
    """Return everything after the first line that is exactly '---', stripped."""
    lines = md.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "---":
            return "\n".join(lines[i + 1 :]).strip()
    raise ValueError("no '---' divider found")


def extract_message_body(md: str) -> str:
    """Return the text between the first and second lines that are exactly '---'."""
    lines = md.splitlines()
    idx = [i for i, line in enumerate(lines) if line.strip() == "---"]
    if len(idx) < 2:
        raise ValueError("expected two '---' fences")
    return "\n".join(lines[idx[0] + 1 : idx[1]]).strip()


def render_block(text: str) -> str:
    """Wrap escaped text in a <pre> the copy JS reads via innerText."""
    return f'<pre class="paste-block">{html_mod.escape(text)}</pre>'


def inject(html: str, name: str, block_html: str) -> str:
    """Replace the content between the named INJECT markers; idempotent."""
    pattern = re.compile(
        rf"(<!-- INJECT:{re.escape(name)} -->).*?(<!-- /INJECT:{re.escape(name)} -->)",
        re.DOTALL,
    )
    if not pattern.search(html):
        raise ValueError(f"marker for {name!r} not found in index.html")
    return pattern.sub(lambda m: m.group(1) + block_html + m.group(2), html, count=1)


_EXTRACTORS = {
    "below_divider": extract_below_divider,
    "message_body": extract_message_body,
}


def build(project_dir: Path) -> str:
    """Read index.html + the three guides, return rendered HTML."""
    html = (project_dir / "site" / "index.html").read_text(encoding="utf-8")
    guide_dir = project_dir / "platform-guide"
    for filename, name, extractor in BLOCKS:
        md = (guide_dir / filename).read_text(encoding="utf-8")
        text = _EXTRACTORS[extractor](md)
        html = inject(html, name, render_block(text))
    return html


def main() -> None:
    project_dir = Path(__file__).resolve().parent.parent
    (project_dir / "site" / "index.html").write_text(build(project_dir), encoding="utf-8")
    print("rendered site/index.html")


if __name__ == "__main__":
    main()
