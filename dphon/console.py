from rich.console import Console
from rich.theme import Theme

# Default color scheme for highlighting matches
DEFAULT_THEME = Theme({
    "context": "dim",
    "variant": "blue",
    "insertion": "green",
    "mismatch": "red"
})

# Consoles for rendering output
console = Console(theme=DEFAULT_THEME, soft_wrap=False)
err_console = Console(theme=DEFAULT_THEME, stderr=True)
