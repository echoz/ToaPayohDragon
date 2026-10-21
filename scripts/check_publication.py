"""Read-only checks for the curated repository and its static project site."""
import ast
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "exports/dragon-pla-kit-v03"
ZIP_SHA256 = "614826200cf5f60f3b15884abf88248671c4207a51d37d3097c312009f65d972"


class HTMLReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        for name, value in attrs:
            if value and name in {"href", "src"}:
                is_asset = name == "src" or (
                    tag == "link" and attributes.get("rel") in {"stylesheet", "icon", "preload"}
                )
                self.references.append((value, is_asset))


def check_link(source, target):
    address = urlsplit(target)
    if address.scheme or address.netloc or not address.path:
        return
    destination = (source.parent / unquote(address.path)).resolve()
    if not destination.is_relative_to(ROOT) or not destination.exists():
        raise ValueError(f"Broken or outside-repository link: {source.relative_to(ROOT)} -> {target}")


def check_repository_files():
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    ).decode().split("\0")
    files = sorted({ROOT / name for name in names if name})
    forbidden = {".venv-print", "__pycache__", "research-only", "printkit_archive"}
    for path in files:
        relative = path.relative_to(ROOT)
        if path.is_symlink() or forbidden.intersection(relative.parts):
            raise ValueError(f"Non-public file: {relative}")
        if str(relative).startswith(("references/images/", "references/pages/")):
            raise ValueError(f"Reference download must stay local: {relative}")
        if re.search(r"\.blend\d+$", path.name) or path.suffix in {".pyc", ".pyo"}:
            raise ValueError(f"Backup or cache: {relative}")
        if path.suffix == ".py":
            ast.parse(path.read_text(), filename=str(relative))
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                check_link(path, target)
        if path.suffix == ".html":
            parser = HTMLReferences()
            parser.feed(path.read_text())
            for target, is_asset in parser.references:
                check_link(path, target)
                if relative.parts[0] == "site" and is_asset:
                    address = urlsplit(target)
                    if address.scheme or address.netloc:
                        raise ValueError(f"External website asset: {target}")
                    destination = (path.parent / unquote(address.path)).resolve()
                    if not destination.is_relative_to(ROOT / "site"):
                        raise ValueError(f"Website asset outside site/: {target}")
    return len(files)


def check_kit():
    archive = ROOT / "exports/dragon-pla-kit-v03.zip"
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ZIP_SHA256:
        raise ValueError("The retained v03 ZIP changed; verify a new candidate before changing its checksum.")
    checksums = (KIT / "SHA256SUMS.txt").read_text().splitlines()
    with zipfile.ZipFile(archive) as packaged:
        for line in checksums:
            digest, name = line.split("  ", 1)
            path = (KIT / name).resolve()
            if not path.is_relative_to(KIT) or not path.is_file():
                raise ValueError(f"Missing or invalid kit path: {name}")
            payload = path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != digest:
                raise ValueError(f"Kit checksum mismatch: {name}")
            if packaged.read("dragon-pla-kit-v03/" + name) != payload:
                raise ValueError(f"ZIP and unpacked kit differ: {name}")
    return len(checksums)


def main():
    file_count = check_repository_files()
    checksum_count = check_kit()
    print(f"Publication checks passed: {file_count} files; {checksum_count} kit hashes and ZIP contents match.")
    print("No CAD generation, live Blender execution, slicing or physical fit test was performed.")


if __name__ == "__main__":
    main()
