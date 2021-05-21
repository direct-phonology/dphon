from typing import Tuple, List

from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme

from .match import Match
from .g2p import GraphemesToPhonemes


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

        su, sv = self._mark(match)
        if self.context > 0:
            cul, cur, cvl, cvr = self._add_context(match)
            su = cul + su + cur
            sv = cvl + sv + cvr
        return su, sv

    def _mark(self, match: Match) -> Tuple[str, str]:
        """Mark up the match for colorization with a theme.

        - Adds markup for insertions (tokens in one sequence but not another).
        - Adds markup for mismatches (differing tokens in the same position).
        - Adds markup for graphic variants (mismatches with same phonemes).
        """

        # if no alignment, just convert to strings because we can't highlight
        if not match.au or not match.av:
            return match.utxt.text, match.vtxt.text

        # o(N) implementation: step through each sequence adding markup
        # TODO convert to a DFA so there's less markup repetition
        su: List[str] = []
        sv: List[str] = []
        u_ptr = 0
        v_ptr = 0
        for i in range(len(match)):

            # gap in u: insertion in v (if not punctuation)
            if match.au[i] == self.gap_char and match.av[i].isalnum():
                su.append(match.au[i])
                sv.append(f"[insertion]{match.av[i]}[/insertion]")
                v_ptr += 1
                continue

            # gap in v: insertion in u (if not punctuation)
            if match.av[i] == self.gap_char and match.au[i].isalnum():
                su.append(f"[insertion]{match.au[i]}[/insertion]")
                sv.append(match.av[i])
                u_ptr += 1
                continue

            # variants (both u and v)
            if self.g2p.are_graphic_variants(match.utxt[u_ptr], match.vtxt[v_ptr]):
                su.append(f"[variant]{match.au[i]}[/variant]")
                sv.append(f"[variant]{match.av[i]}[/variant]")
                u_ptr += 1
                v_ptr += 1
                continue

            # mismatch (both u and v) - only highlight if alphanumeric
            if match.au[i] != match.av[i]:
                if match.au[i].isalnum() and match.av[i].isalnum():
                    su.append(f"[mismatch]{match.au[i]}[/mismatch]")
                    sv.append(f"[mismatch]{match.av[i]}[/mismatch]")
                    u_ptr += 1
                    v_ptr += 1
                    continue

            # equality; nothing to highlight
            su.append(match.au[i])
            sv.append(match.av[i])
            u_ptr += 1
            v_ptr += 1

        return "".join(su), "".join(sv)

    def _add_context(self, match: Match) -> Tuple[str, str, str, str]:
        """Add context to either side of the match sequences.

        Context coloration can be changed by the default theme; a dim appearance
        is used in terminals.
        """

        utxt, vtxt = match.utxt, match.vtxt
        u, v = utxt.doc, vtxt.doc
        cul = f"[context]{u[utxt.start-self.context:utxt.start]}[/context]"
        cur = f"[context]{u[utxt.end:utxt.end+self.context]}[/context]"
        cvl = f"[context]{v[vtxt.start-self.context:vtxt.start]}[/context]"
        cvr = f"[context]{v[vtxt.end:vtxt.end+self.context]}[/context]"
        return (cul, cur, cvl, cvr)

    def transcription(self, match: Match) -> Tuple[str, str]:
        """Get the phonemic transcription for the match for display."""
        return (
            "*" + " ".join(match.utxt._.syllables),
            "*" + " ".join(match.vtxt._.syllables),
        )
