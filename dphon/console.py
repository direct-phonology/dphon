# -*- coding: utf-8 -*-

from typing import List, Tuple

from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme
from spacy.tokens import Span

from .g2p import GraphemesToPhonemes
from .match import Match

# Default color scheme for highlighting matches
DEFAULT_THEME = Theme(
    {"context": "dim", "variant": "blue", "insertion": "green", "mismatch": "red"}
)

# Consoles for rendering output
console = Console(theme=DEFAULT_THEME, soft_wrap=True)
err_console = Console(theme=DEFAULT_THEME, stderr=True)


class MatchHighlighter(RegexHighlighter):
    """Highlighter that adds Rich markup to matches for console rendering."""

    context: int
    gap_char: str
    g2p: GraphemesToPhonemes

    def __init__(
        self, g2p: GraphemesToPhonemes, context: int = 0, gap_char: str = "-"
    ) -> None:
        """Create a new highlighter with optional context for each match."""
        # can't have negative context
        if context < 0:
            raise ValueError(f"{self.__class__} context must be greater than 0")

        # store parameters
        self.context = context
        self.gap_char = gap_char
        self.g2p = g2p
        super().__init__()

    def format_match(self, match: Match) -> Tuple[str, str]:
        """Return match sequences as Rich format strings, with optional context.

        Adds markup for highlighting insertions, mismatches, etc. If context is
        set, also adds highlighted context to either end of the match.
        """
        return (
            self.format_span(match.utxt, match.vtxt, match.au, match.av),
            self.format_span(match.vtxt, match.utxt, match.av, match.au),
        )

    def transcribe_match(self, match: Match) -> Tuple[str, str]:
        """Render a phonemic transcription for a Match."""
        return (self.transcribe_span(match.utxt), self.transcribe_span(match.vtxt))

    def format_span(
        self,
        span: Span,
        other: Span = None,
        alignment: str = None,
        other_alignment: str = None,
    ) -> str:
        """Return a Span as a Rich format string, with optional context.

        Adds markup for highlighting insertions, mismatches, etc. if a second
        reference Span is provided. If context is set, also adds highlighted
        context to either end of the match.
        """
        highlighted_span = self._mark_span(span, alignment, other, other_alignment)
        if self.context > 0:
            context_left, context_right = self._add_span_context(span)
            formatted_span = context_left + highlighted_span + context_right
        return formatted_span

    def transcribe_span(self, span: Span) -> str:
        """Render a phonemic transcription for a Span."""
        return "*" + " ".join(span._.syllables)

    def _mark_span(
        self, span: Span, alignment: str, other: Span, other_alignment: str
    ) -> str:
        """Mark up a Span for colorization with a theme, in relation to another Span.

        - Adds markup for insertions (tokens in one Span but not another).
        - Adds markup for mismatches (differing tokens in the same position).
        - Adds markup for graphic variants (mismatches with same phonemes).
        """
        # if no alignment, just return the text because we can't highlight
        if not alignment or not other or not other_alignment:
            return span.text

        # o(N) implementation: step through each sequence adding markup
        # TODO convert to a DFA so there's less markup repetition?
        marked_span: List[str] = []
        span_ptr = 0
        other_ptr = 0
        for i in range(len(span)):
            # gap in u: insertion in v (if not punctuation)
            if alignment[i] == self.gap_char and other_alignment[i].isalnum():
                other_ptr += 1
                continue

            # gap in v: insertion in u (if not punctuation)
            if other_alignment[i] == self.gap_char and alignment[i].isalnum():
                marked_span.append(f"[insertion]{alignment[i]}[/insertion]")
                span_ptr += 1
                continue

            # variants (both u and v)
            if self.g2p.are_graphic_variants(span[span_ptr], other[other_ptr]):
                marked_span.append(f"[variant]{alignment[i]}[/variant]")
                span_ptr += 1
                other_ptr += 1
                continue

            # mismatch (both u and v) - only highlight if alphanumeric
            if alignment[i] != other_alignment[i]:
                if alignment[i].isalnum() and other_alignment[i].isalnum():
                    marked_span.append(f"[mismatch]{alignment[i]}[/mismatch]")
                    span_ptr += 1
                    other_ptr += 1
                    continue

            # equality; nothing to highlight
            marked_span.append(alignment[i])
            span_ptr += 1
            other_ptr += 1

        return "".join(marked_span)

    def _add_span_context(self, span: Span) -> Tuple[str, str]:
        """Add context to either side of the Span.

        Context coloration can be changed by the default theme; a dim appearance
        is used in terminals.
        """
        context_left = span.doc[span.start - self.context : span.start]
        context_right = span.doc[span.end : span.end + self.context]
        return (
            f"[context]{context_left.text.rjust(self.context, "　")}[/context]",
            f"[context]{context_right.text.ljust(self.context, "　")}[/context]",
        )
