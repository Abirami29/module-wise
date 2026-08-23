"""
Extracts inline/block comments from raw .tf text (hcl2.load discards these).
Comments often carry the "why" that structured HCL blocks don't - decision
context, deprecation notes, compliance drivers.
"""
import re
from pathlib import Path

COMMENT_RE = re.compile(
    r'#\s*(.+?)$|//\s*(.+?)$|/\*(.+?)\*/',
    re.MULTILINE,
)
COMMENT_RE_BLOCK = re.compile(r'/\*(.+?)\*/', re.DOTALL)


def extract_comments(tf_file_path: Path) -> list[str]:
    """Return all comment text found in a .tf file, cleaned up."""
    text = tf_file_path.read_text()
    comments = []

    # Block comments first (need DOTALL to span multiple lines)
    for match in COMMENT_RE_BLOCK.finditer(text):
        comment_text = match.group(1).strip()
        if comment_text:
            comments.append(comment_text)

    # Then strip block comments out so line-comment regex doesn't double-match inside them
    text_no_blocks = COMMENT_RE_BLOCK.sub("", text)

    line_comment_re = re.compile(r'#\s*(.+)$|//\s*(.+)$', re.MULTILINE)
    for match in line_comment_re.finditer(text_no_blocks):
        comment_text = next((g for g in match.groups() if g), "").strip()
        if comment_text:
            comments.append(comment_text)

    return comments


def extract_comments_for_module(module_dir: Path) -> list[str]:
    """Aggregate comments across all .tf files in a module directory."""
    all_comments = []
    for tf_file in module_dir.glob("*.tf"):
        all_comments.extend(extract_comments(tf_file))
    return all_comments