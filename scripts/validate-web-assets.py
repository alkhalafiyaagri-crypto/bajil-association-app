from html.parser import HTMLParser
from pathlib import Path
import subprocess, tempfile

html = Path("bajil_android_project/app/src/main/assets/index.html").read_text(encoding="utf-8")
class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.external = False
        self.parts = []
        self.current = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            self.inside = True
            self.external = any(k.lower() == "src" for k, _ in attrs)
            self.current = []
    def handle_data(self, data):
        if self.inside and not self.external:
            self.current.append(data)
    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.inside:
            if not self.external:
                self.parts.append("".join(self.current))
            self.inside = False
            self.external = False

parser = Scripts()
parser.feed(html)
if not parser.parts:
    raise SystemExit("No inline JavaScript blocks found in index.html")
with tempfile.TemporaryDirectory() as tmp:
    count = 0
    for i, source in enumerate(parser.parts):
        if not source.strip():
            continue
        path = Path(tmp) / f"inline-{i}.js"
        path.write_text(source, encoding="utf-8")
        result = subprocess.run(["node", "--check", str(path)], text=True, capture_output=True)
        if result.returncode:
            print(result.stdout)
            print(result.stderr)
            raise SystemExit(f"JavaScript syntax validation failed in inline script {i}")
        count += 1
print(f"JavaScript syntax validation passed for {count} inline script block(s).")
