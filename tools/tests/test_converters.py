"""Tests for Markdown→LaTeX and Markdown→HTML inline converters."""

from __future__ import annotations

from tools.converters import md_to_html, md_to_latex


class TestMdToLatex:
    def test_plain_text_unchanged(self) -> None:
        assert md_to_latex("hello world") == "hello world"

    def test_empty_string(self) -> None:
        assert md_to_latex("") == ""

    def test_bold(self) -> None:
        assert md_to_latex("deliver **MVP** fast") == r"deliver \textbf{MVP} fast"

    def test_italic(self) -> None:
        assert md_to_latex("the *key* insight") == r"the \emph{key} insight"

    def test_code(self) -> None:
        assert md_to_latex("use `xelatex` here") == r"use \texttt{xelatex} here"

    def test_multiple_bold(self) -> None:
        assert (
            md_to_latex("**A** and **B**")
            == r"\textbf{A} and \textbf{B}"
        )

    def test_escapes_percent(self) -> None:
        assert md_to_latex("50% off") == r"50\% off"

    def test_escapes_ampersand(self) -> None:
        assert md_to_latex("A & B") == r"A \& B"

    def test_escapes_underscore(self) -> None:
        assert md_to_latex("my_var") == r"my\_var"

    def test_escapes_hash(self) -> None:
        assert md_to_latex("a #tag") == r"a \#tag"

    def test_escapes_dollar(self) -> None:
        assert md_to_latex("$50k") == r"\$50k"

    def test_escapes_caret(self) -> None:
        assert md_to_latex("x^2") == r"x\textasciicircum{}2"

    def test_escapes_tilde(self) -> None:
        assert md_to_latex("~approx") == r"\textasciitilde{}approx"

    def test_escapes_backslash(self) -> None:
        assert md_to_latex("a \\ b") == r"a \textbackslash{} b"

    def test_escapes_braces(self) -> None:
        assert md_to_latex("{foo}") == r"\{foo\}"

    def test_bold_with_percent_inside(self) -> None:
        # Emphasis first, then specials escaped within the output.
        assert md_to_latex("**50% off**") == r"\textbf{50\% off}"

    def test_specials_outside_emphasis(self) -> None:
        assert (
            md_to_latex("up **50%** from Q1 & Q2")
            == r"up \textbf{50\%} from Q1 \& Q2"
        )

    def test_does_not_double_escape_emphasis_markers(self) -> None:
        # The ** markers themselves should not survive as literal asterisks.
        result = md_to_latex("**MVP**")
        assert "*" not in result
        assert result == r"\textbf{MVP}"

    def test_code_with_specials_inside(self) -> None:
        # Inside \texttt{}, underscores and percents still need escaping
        # because LaTeX still parses them.
        assert md_to_latex("`my_var`") == r"\texttt{my\_var}"

    def test_literal_asterisk_not_emphasis(self) -> None:
        # A single trailing asterisk without a pair should be left as-is
        # (safe because LaTeX accepts literal *).
        assert md_to_latex("a* b") == "a* b"

    def test_unicode_preserved(self) -> None:
        assert md_to_latex("2024–2025") == "2024–2025"
        assert md_to_latex("café") == "café"


class TestMdToHtml:
    def test_plain_text_unchanged(self) -> None:
        assert md_to_html("hello") == "hello"

    def test_empty_string(self) -> None:
        assert md_to_html("") == ""

    def test_bold(self) -> None:
        assert md_to_html("**MVP**") == "<strong>MVP</strong>"

    def test_italic(self) -> None:
        assert md_to_html("*key*") == "<em>key</em>"

    def test_code(self) -> None:
        assert md_to_html("`x`") == "<code>x</code>"

    def test_html_escape_lt_gt(self) -> None:
        assert md_to_html("a < b > c") == "a &lt; b &gt; c"

    def test_html_escape_ampersand(self) -> None:
        assert md_to_html("A & B") == "A &amp; B"

    def test_html_escape_quotes(self) -> None:
        assert md_to_html('"x"') == "&quot;x&quot;"

    def test_bold_with_html_specials_inside(self) -> None:
        assert md_to_html("**A & B**") == "<strong>A &amp; B</strong>"

    def test_does_not_convert_percent(self) -> None:
        # % is not a special HTML character.
        assert md_to_html("50%") == "50%"

    def test_unicode_preserved(self) -> None:
        assert md_to_html("2024–2025 café") == "2024–2025 café"
