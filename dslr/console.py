from functools import partial

from rich.console import Console

console = Console()
error_console = Console(stderr=True)

cprint = partial(console.print, highlight=False)
eprint = partial(error_console.print, style="bold red", highlight=False)
