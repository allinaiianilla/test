from pathlib import Path
from datetime import datetime
class ChatLogger:
    def __init__(self):
        Path("history").mkdir(exist_ok=True)
        self.path=Path("history")/f"{datetime.now():%Y%m%d_%H%M%S}.md"
        self.path.write_text("# Chat\n\n",encoding="utf8")
    def append(self,role,content):
        with self.path.open("a",encoding="utf8") as f:
            f.write(f"## {role}\n\n{content}\n\n---\n")
