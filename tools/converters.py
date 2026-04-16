"""Markdown-inline to LaTeX / HTML converters.

Supports a narrow subset intentionally: **bold**, *italic*, and `code`.
Applied to every string field that the templates render.

Why a hand-rolled converter instead of markdown-it-py: the full Markdown
grammar is overkill here (no paragraphs, lists, links — just inline
emphasis), and LaTeX-special escaping is easier to reason about without
an intermediate AST.
"""

from __future__ import annotations

import html
import re

# Regex order matters: the two-char **bold** must be tried before single *italic*.
_BOLD = re.compile(r"\*\*([^*]+?)\*\*")
_ITALIC = re.compile(r"\*([^*]+?)\*")
_CODE = re.compile(r"`([^`]+?)`")

# LaTeX special-character map. Applied in a single regex pass so replacements
# (which themselves contain backslashes and braces) are not re-escaped.
_LATEX_ESCAPE_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_LATEX_SPECIALS_RE = re.compile("|".join(re.escape(k) for k in _LATEX_ESCAPE_MAP))


def _escape_latex(s: str) -> str:
    return _LATEX_SPECIALS_RE.sub(lambda m: _LATEX_ESCAPE_MAP[m.group(0)], s)


# Sentinels stand in for emphasis spans while we escape specials, so the
# backslashes and braces we inject for \textbf / \emph / \texttt aren't
# double-escaped. Using control characters the user's content will never
# contain.
_BOLD_OPEN = "\x01B\x01"
_BOLD_CLOSE = "\x01b\x01"
_ITALIC_OPEN = "\x01I\x01"
_ITALIC_CLOSE = "\x01i\x01"
_CODE_OPEN = "\x01C\x01"
_CODE_CLOSE = "\x01c\x01"


def md_to_latex(s: str) -> str:
    """Convert a Markdown inline string to LaTeX.

    Order:
      1. Replace emphasis runs with non-text sentinels.
      2. Escape LaTeX specials (without touching the sentinels).
      3. Replace sentinels with real LaTeX macros.
    """
    if not s:
        return s

    # Stage 1: emphasis → sentinels. Bold first so ** isn't eaten by *…*.
    s = _BOLD.sub(lambda m: f"{_BOLD_OPEN}{m.group(1)}{_BOLD_CLOSE}", s)
    s = _ITALIC.sub(lambda m: f"{_ITALIC_OPEN}{m.group(1)}{_ITALIC_CLOSE}", s)
    s = _CODE.sub(lambda m: f"{_CODE_OPEN}{m.group(1)}{_CODE_CLOSE}", s)

    # Stage 2: escape LaTeX specials.
    s = _escape_latex(s)

    # Stage 3: sentinels → LaTeX macros.
    s = s.replace(_BOLD_OPEN, r"\textbf{").replace(_BOLD_CLOSE, "}")
    s = s.replace(_ITALIC_OPEN, r"\emph{").replace(_ITALIC_CLOSE, "}")
    s = s.replace(_CODE_OPEN, r"\texttt{").replace(_CODE_CLOSE, "}")
    return s


def md_to_html(s: str) -> str:
    """Convert a Markdown inline string to HTML.

    Order:
      1. Replace emphasis runs with sentinels.
      2. HTML-escape specials.
      3. Replace sentinels with real HTML tags.
    """
    if not s:
        return s

    s = _BOLD.sub(lambda m: f"{_BOLD_OPEN}{m.group(1)}{_BOLD_CLOSE}", s)
    s = _ITALIC.sub(lambda m: f"{_ITALIC_OPEN}{m.group(1)}{_ITALIC_CLOSE}", s)
    s = _CODE.sub(lambda m: f"{_CODE_OPEN}{m.group(1)}{_CODE_CLOSE}", s)

    s = html.escape(s, quote=True)

    s = s.replace(_BOLD_OPEN, "<strong>").replace(_BOLD_CLOSE, "</strong>")
    s = s.replace(_ITALIC_OPEN, "<em>").replace(_ITALIC_CLOSE, "</em>")
    s = s.replace(_CODE_OPEN, "<code>").replace(_CODE_CLOSE, "</code>")
    return s
