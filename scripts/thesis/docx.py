"""Build the Word version of the thesis from its Markdown source.

    python -m scripts.thesis.docx [output.docx]

Concatenates the chapter files in document order, turns the cover into centred
paragraphs, puts a Word table of contents where section 3 (Índice) goes, starts every
chapter on a new page and drops the ``> COMPLETAR`` notes, then hands the result to
pandoc (which must be on PATH). Word asks to refresh the index when the file opens.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THESIS = ROOT / "docs" / "tfc" / "tesis"
DEFAULT_OUT = ROOT / "docs" / "tfc" / "tesis.docx"
CHAPTERS = [
    "06-resumen.md",
    "07-introduccion.md",
    "08-marco-teorico.md",
    "09-analisis.md",
    "10-diseno.md",
    "11-implantacion.md",
    "12-conclusiones.md",
    "13-bibliografia.md",
    "14-anexos.md",
    "15-glosario.md",
]

PAGE_BREAK = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```'
TOC = (
    "```{=openxml}\n"
    '<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
    '<w:r><w:instrText xml:space="preserve">TOC \\o "1-3" \\h \\z \\u</w:instrText></w:r>'
    '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
    "<w:r><w:t>Actualizar el índice: clic derecho, Actualizar campo.</w:t></w:r>"
    '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>\n'
    "```"
)
_COMPLETAR = re.compile(r"^> COMPLETAR.*\n(?:>.*\n)*\n?", re.MULTILINE)


def drop_notes(text: str) -> str:
    """Remove the ``> COMPLETAR (Joaquín): …`` blockquotes left for the author."""
    return _COMPLETAR.sub("", text)


def cover(lines: list[str]) -> str:
    """Centred cover page; bold lines are titles and get a larger size."""
    paras = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        bold = line.startswith("**") and line.endswith("**")
        text = escape(line.strip("*"), quote=False)
        rpr = '<w:b/><w:sz w:val="32"/>' if bold else '<w:sz w:val="24"/>'
        paras.append(
            '<w:p><w:pPr><w:spacing w:before="240" w:after="240"/><w:jc w:val="center"/></w:pPr>'
            f"<w:r><w:rPr>{rpr}</w:rPr><w:t>{text}</w:t></w:r></w:p>"
        )
    return "```{=openxml}\n" + "".join(paras) + "\n```"


def preliminaries(text: str) -> str:
    """Sections 1, 2, 4 and 5 come in one file; the index (3) goes between 2 and 4."""
    sections = re.split(r"^## ", drop_notes(text), flags=re.MULTILINE)[1:]
    parts = []
    for section in sections:
        title, _, body = section.partition("\n")
        if title.startswith("1."):
            parts.append(cover(_join_wrapped(body)))
            continue
        parts.append(f"# {title}\n{body.strip()}")
        if title.startswith("2."):
            parts.append(f"# 3. Índice\n\n{TOC}")
    return f"\n\n{PAGE_BREAK}\n\n".join(parts)


def _join_wrapped(body: str) -> list[str]:
    """Join a bold title that the source wraps over two lines."""
    lines, buf = [], ""
    for line in body.splitlines():
        if buf:
            buf += " " + line.strip()
            if buf.endswith("**"):
                lines.append(buf)
                buf = ""
        elif line.startswith("**") and not line.rstrip().endswith("**"):
            buf = line.strip()
        else:
            lines.append(line)
    return lines


def chapter(text: str) -> str:
    return drop_notes(text).strip()


def source(root: Path = THESIS) -> str:
    parts = [preliminaries((root / "01-preliminares.md").read_text(encoding="utf-8"))]
    parts += [chapter((root / name).read_text(encoding="utf-8")) for name in CHAPTERS]
    return f"\n\n{PAGE_BREAK}\n\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    if shutil.which("pandoc") is None:
        print("pandoc no está instalado (brew install pandoc).", file=sys.stderr)
        return 1
    out = Path(argv[0]) if argv else DEFAULT_OUT
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as tmp:
        tmp.write(source())
    subprocess.run(
        [
            "pandoc", tmp.name,
            "-f", "markdown-implicit_figures",
            "-t", "docx",
            "--resource-path", str(THESIS),
            "-o", str(out),
        ],
        check=True,
    )
    Path(tmp.name).unlink()
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
