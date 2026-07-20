from rich.console import Console
from rich.markdown import Markdown
console=Console()
def show(text):
    console.print(Markdown(text))
