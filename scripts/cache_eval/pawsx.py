"""PAWS-X Spanish test pairs: read the official TSV and attach both models' cosines.

PAWS-X (Yang et al., EMNLP 2019) is the evaluation data of the cache measurement, set (a) of
``benchmarks/cache/v1/preregistration.md``. Label 1 = paraphrase.

    python -m scripts.cache_eval.pawsx

downloads the test file (the official archive, or the Hugging Face copy published by the same
Google Research organization when the archive is not served), embeds both sentences of every
valid pair with ``nomic-embed-text`` (production) and ``nomic-embed-text-v2-moe``
(sensitivity), and writes ``benchmarks/cache/v1/pawsx/pairs.jsonl``.
"""

from __future__ import annotations

import hashlib
import json
import tarfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import httpx

from scripts.cache_eval import embed

COLUMNS = ("id", "sentence1", "sentence2", "label")
# The dataset README asks users to clean the translated dev and test files of the "NS"
# placeholder, a sentence that failed translation.
PLACEHOLDER = "NS"
ARCHIVE_MEMBER = "x-final/es/test_2k.tsv"
TEST_TSV_NAME = "es_test_2k.tsv"

OFFICIAL_URL = "https://storage.googleapis.com/paws/pawsx/x-final.tar.gz"
MIRROR_ROWS_URL = "https://datasets-server.huggingface.co/rows"
MIRROR_DATASET = "google-research-datasets/paws-x"
MIRROR_PAGE = 100  # the rows endpoint serves at most 100 rows per request

DOWNLOADS = Path("artifacts/cache-eval/downloads")
OFFICIAL_DIR = DOWNLOADS / "pawsx"
MIRROR_DIR = DOWNLOADS / "pawsx-hf"
OUT_PATH = Path("benchmarks/cache/v1/pawsx/pairs.jsonl")
PRODUCTION_MODEL = "nomic-embed-text"
SENSITIVITY_MODEL = "nomic-embed-text-v2-moe"


@dataclass(frozen=True)
class PawsPair:
    id: str
    sentence1: str
    sentence2: str
    label: int


@dataclass(frozen=True)
class SkippedRow:
    line: int
    id: str
    reason: str


@dataclass(frozen=True)
class PawsLoad:
    pairs: list[PawsPair]
    skipped: list[SkippedRow]


def read_pairs(tsv_path: Path) -> PawsLoad:
    """Valid pairs of a PAWS-X TSV, plus every row that was dropped and why."""
    pairs: list[PawsPair] = []
    skipped: list[SkippedRow] = []
    text = tsv_path.read_text(encoding="utf-8")
    for number, line in enumerate(text.split("\n"), start=1):
        line = line.rstrip("\r")
        if not line:
            continue
        fields = line.split("\t")
        if number == 1 and tuple(fields) == COLUMNS:
            continue
        row_id = fields[0]
        if len(fields) != len(COLUMNS):
            skipped.append(SkippedRow(number, row_id, f"expected 4 columns, found {len(fields)}"))
            continue
        _, sentence1, sentence2, label = fields
        if label not in ("0", "1"):
            skipped.append(SkippedRow(number, row_id, "label is not 0 or 1"))
        elif PLACEHOLDER in (sentence1.strip(), sentence2.strip()):
            skipped.append(SkippedRow(number, row_id, f"placeholder sentence {PLACEHOLDER}"))
        elif not sentence1.strip() or not sentence2.strip():
            skipped.append(SkippedRow(number, row_id, "empty sentence"))
        else:
            pairs.append(PawsPair(row_id, sentence1, sentence2, int(label)))
    return PawsLoad(pairs, skipped)


def load_pairs(tsv_path: Path) -> list[PawsPair]:
    return read_pairs(tsv_path).pairs


def extract_test_tsv(archive: Path, dest_dir: Path) -> Path:
    """Copy the one member we need out of the archive, which is treated as untrusted data.

    Nothing else is extracted and the member's own path is never used for the destination, so
    a crafted archive cannot write elsewhere; only a regular file is accepted.
    """
    with tarfile.open(archive, "r:gz") as tar:
        try:
            member = tar.getmember(ARCHIVE_MEMBER)
        except KeyError:
            raise FileNotFoundError(f"{ARCHIVE_MEMBER} is not in {archive}.") from None
        source = tar.extractfile(member) if member.isfile() else None
        if source is None:
            raise ValueError(f"{ARCHIVE_MEMBER} in {archive} is not a regular file.")
        dest_dir.mkdir(parents=True, exist_ok=True)
        target = dest_dir / TEST_TSV_NAME
        target.write_bytes(source.read())
    return target


def rows_to_tsv(rows: Iterable[dict]) -> str:
    """The official TSV layout (header plus id, sentence1, sentence2, label) from row dicts."""
    lines = ["\t".join(COLUMNS)]
    for row in rows:
        fields = [str(row[column]) for column in COLUMNS]
        if any(c in field for field in fields for c in "\t\n\r"):
            raise ValueError(f"Row {row['id']} has a tab or line break and would break the TSV.")
        lines.append("\t".join(fields))
    return "\n".join(lines) + "\n"


def pair_record(pair: PawsPair, *, cos_v1: float, cos_v2: float) -> dict:
    """A row of ``pawsx/pairs.jsonl``."""
    return {
        "id": pair.id,
        "sentence1": pair.sentence1,
        "sentence2": pair.sentence2,
        "label": pair.label,
        "cos_nomic_v1": cos_v1,
        "cos_nomic_v2": cos_v2,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _download_official(dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive = dest_dir / "x-final.tar.gz"
    with httpx.stream("GET", OFFICIAL_URL, follow_redirects=True, timeout=120.0) as response:
        response.raise_for_status()
        with archive.open("wb") as handle:
            for chunk in response.iter_bytes():
                handle.write(chunk)
    return archive


def _download_mirror_rows() -> list[dict]:
    rows: list[dict] = []
    total: int | None = None
    while total is None or len(rows) < total:
        response = httpx.get(
            MIRROR_ROWS_URL,
            params={"dataset": MIRROR_DATASET, "config": "es", "split": "test",
                    "offset": len(rows), "length": MIRROR_PAGE},
            timeout=60.0,
        )
        response.raise_for_status()
        body = response.json()
        total = body["num_rows_total"]
        page = [item["row"] for item in body["rows"]]
        if not page:
            raise RuntimeError(f"The mirror returned no rows at offset {len(rows)} of {total}.")
        rows.extend(page)
    return rows


def fetch_test_tsv() -> tuple[Path, str]:
    """The Spanish test TSV and where it came from, downloaded once.

    The official archive is tried first. When Google's bucket refuses anonymous reads (it does
    at the time of writing: HTTP 403), the same split is taken from the Hugging Face dataset
    published by the same organization and written in the official TSV layout.
    """
    for directory, source in ((OFFICIAL_DIR, "official"), (MIRROR_DIR, "mirror")):
        if (directory / TEST_TSV_NAME).exists():
            return directory / TEST_TSV_NAME, source
    try:
        archive = _download_official(OFFICIAL_DIR)
    except httpx.HTTPStatusError as error:
        print(f"official archive unavailable ({error.response.status_code}); using the mirror")
        MIRROR_DIR.mkdir(parents=True, exist_ok=True)
        tsv = MIRROR_DIR / TEST_TSV_NAME
        tsv.write_text(rows_to_tsv(_download_mirror_rows()), encoding="utf-8")
        print(f"mirror {MIRROR_DATASET} es/test -> {tsv} sha256 {_sha256(tsv)}")
        return tsv, "mirror"
    print(f"official archive {OFFICIAL_URL} sha256 {_sha256(archive)}")
    return extract_test_tsv(archive, OFFICIAL_DIR), "official"


def main() -> int:
    tsv, source = fetch_test_tsv()
    loaded = read_pairs(tsv)
    print(f"{source}: {len(loaded.pairs)} valid pairs, {len(loaded.skipped)} dropped")
    for row in loaded.skipped:
        print(f"  dropped line {row.line} id {row.id}: {row.reason}")

    sentences = [p.sentence1 for p in loaded.pairs] + [p.sentence2 for p in loaded.pairs]
    half = len(loaded.pairs)
    cosines: dict[str, list[float]] = {}
    for model in (PRODUCTION_MODEL, SENSITIVITY_MODEL):
        vectors = embed.embed_texts(sentences, model=model)
        cosines[model] = [embed.cosine(a, b) for a, b in zip(vectors[:half], vectors[half:])]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for i, pair in enumerate(loaded.pairs):
            record = pair_record(pair, cos_v1=cosines[PRODUCTION_MODEL][i],
                                 cos_v2=cosines[SENSITIVITY_MODEL][i])
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"wrote {len(loaded.pairs)} rows -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
