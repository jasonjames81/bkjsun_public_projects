import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
sys.path.insert(0, str(SITE))

import build_site as bs  # noqa: E402


def test_extract_below_divider():
    md = "# Title\n\nintro\n\n---\n\nreal body\nmore\n"
    assert bs.extract_below_divider(md) == "real body\nmore"


def test_extract_message_body():
    md = "# Title\n\ntip\n\n---\n\nbody line 1\nbody line 2\n\n---\n\n## Tips\n- x\n"
    assert bs.extract_message_body(md) == "body line 1\nbody line 2"


def test_render_block_escapes():
    out = bs.render_block('a < b & "c"')
    assert "&lt;" in out and "&amp;" in out and "&quot;" in out
    assert out.startswith('<pre class="paste-block">')
    assert out.endswith("</pre>")


def test_inject_replaces_region_and_is_idempotent():
    html = "X<!-- INJECT:foo -->OLD<!-- /INJECT:foo -->Y"
    once = bs.inject(html, "foo", "NEW")
    assert once == "X<!-- INJECT:foo -->NEW<!-- /INJECT:foo -->Y"
    twice = bs.inject(once, "foo", "NEW")
    assert twice == once
