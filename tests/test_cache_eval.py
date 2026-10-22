"""Pure-function seams of the cache-eval data stage: vectors, PAWS-X pairs, corpus neighbors."""

from __future__ import annotations

import io
import json
import tarfile

import pytest

from scripts.cache_eval import embed, neighbors, pawsx


def test_normalize_scales_a_vector_to_unit_length():
    assert embed.normalize([3.0, 4.0]) == pytest.approx([0.6, 0.8])


def test_normalize_rejects_a_zero_vector():
    with pytest.raises(ValueError):
        embed.normalize([0.0, 0.0])


def test_cosine_of_identical_orthogonal_and_diagonal_vectors():
    assert embed.cosine([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert embed.cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert embed.cosine([1.0, 1.0], [1.0, 0.0]) == pytest.approx(0.7071067811865476)


def test_cosine_ignores_vector_length():
    assert embed.cosine([3.0, 0.0], [0.5, 0.0]) == pytest.approx(1.0)


def approx_vectors(vectors):
    return [pytest.approx(v) for v in vectors]


class RecordingFetch:
    """Stands in for Ollama: maps known texts to raw (unnormalized) vectors, records calls."""

    VECTORS = {"a": [3.0, 4.0], "bb": [0.0, 2.0], "ccc": [5.0, 0.0]}

    def __init__(self):
        self.calls: list[tuple[str, list[str]]] = []

    def __call__(self, model: str, texts: list[str]) -> list[list[float]]:
        self.calls.append((model, list(texts)))
        return [list(self.VECTORS[t]) for t in texts]


def test_embed_texts_returns_unit_vectors_in_input_order(tmp_path):
    fetch = RecordingFetch()
    vectors = embed.embed_texts(["bb", "a"], model="m", cache_dir=tmp_path, fetch=fetch)
    assert vectors == approx_vectors([[0.0, 1.0], [0.6, 0.8]])


def test_embed_texts_serves_repeats_from_the_cache_and_fetches_only_new_texts(tmp_path):
    fetch = RecordingFetch()
    embed.embed_texts(["a", "bb"], model="m", cache_dir=tmp_path, fetch=fetch)
    again = embed.embed_texts(["bb", "ccc", "a"], model="m", cache_dir=tmp_path, fetch=fetch)
    assert again == approx_vectors([[0.0, 1.0], [1.0, 0.0], [0.6, 0.8]])
    assert fetch.calls == [("m", ["a", "bb"]), ("m", ["ccc"])]


def test_embed_texts_fetches_a_duplicated_text_once(tmp_path):
    fetch = RecordingFetch()
    vectors = embed.embed_texts(["a", "a", "bb"], model="m", cache_dir=tmp_path, fetch=fetch)
    assert vectors[0] == vectors[1]
    assert fetch.calls == [("m", ["a", "bb"])]


def test_embed_texts_keeps_one_cache_per_model(tmp_path):
    fetch = RecordingFetch()
    embed.embed_texts(["a"], model="m1", cache_dir=tmp_path, fetch=fetch)
    embed.embed_texts(["a"], model="m2", cache_dir=tmp_path, fetch=fetch)
    assert [model for model, _ in fetch.calls] == ["m1", "m2"]


def test_embed_texts_keys_the_cache_by_text_sha256(tmp_path):
    embed.embed_texts(["a"], model="m", cache_dir=tmp_path, fetch=RecordingFetch())
    stored = json.loads((tmp_path / "m.json").read_text())
    # sha256("a")
    assert list(stored) == ["ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"]


def test_embed_texts_batches_the_fetches(tmp_path):
    fetch = RecordingFetch()
    embed.embed_texts(["a", "bb", "ccc"], model="m", cache_dir=tmp_path, fetch=fetch, batch=2)
    assert fetch.calls == [("m", ["a", "bb"]), ("m", ["ccc"])]


PAWS_HEADER = "id\tsentence1\tsentence2\tlabel\n"


def _tsv(tmp_path, *rows, header=PAWS_HEADER):
    path = tmp_path / "test_2k.tsv"
    path.write_text(header + "".join(row + "\n" for row in rows), encoding="utf-8")
    return path


def test_load_pairs_reads_the_four_columns_and_skips_the_header(tmp_path):
    path = _tsv(tmp_path, "10\tEl río es largo.\tEl río es extenso.\t1", "12\tA bebe.\tB bebe.\t0")
    assert pawsx.load_pairs(path) == [
        pawsx.PawsPair(id="10", sentence1="El río es largo.", sentence2="El río es extenso.", label=1),
        pawsx.PawsPair(id="12", sentence1="A bebe.", sentence2="B bebe.", label=0),
    ]


def test_load_pairs_accepts_a_file_without_header(tmp_path):
    path = _tsv(tmp_path, "10\tUno.\tDos.\t1", header="")
    assert [p.id for p in pawsx.load_pairs(path)] == ["10"]


def test_load_pairs_does_not_treat_quotes_as_csv_quoting(tmp_path):
    path = _tsv(tmp_path, '7\t"Hola dijo ella"\t"Chao\t0')
    [pair] = pawsx.load_pairs(path)
    assert (pair.sentence1, pair.sentence2) == ('"Hola dijo ella"', '"Chao')


def test_read_pairs_drops_ns_placeholders_and_reports_why(tmp_path):
    path = _tsv(
        tmp_path,
        "10\tUno.\tDos.\t1",
        "5815\tNS\tLa lista posterior.\t0",
        "6000\tTres.\tNS\t1",
    )
    loaded = pawsx.read_pairs(path)
    assert [p.id for p in loaded.pairs] == ["10"]
    assert [(s.id, s.reason) for s in loaded.skipped] == [
        ("5815", "placeholder sentence NS"),
        ("6000", "placeholder sentence NS"),
    ]


def test_read_pairs_drops_empty_sentences_bad_labels_and_short_rows(tmp_path):
    path = _tsv(
        tmp_path,
        "1\t\tDos.\t1",
        "2\tUno.\tDos.\t2",
        "3\tUno.\tDos.\tx",
        "4\tUno.\tDos",
        "5\tUno.\tDos.\t0",
    )
    loaded = pawsx.read_pairs(path)
    assert [p.id for p in loaded.pairs] == ["5"]
    assert {s.id: s.reason for s in loaded.skipped} == {
        "1": "empty sentence",
        "2": "label is not 0 or 1",
        "3": "label is not 0 or 1",
        "4": "expected 4 columns, found 3",
    }


def test_read_pairs_ignores_blank_lines_and_windows_line_endings(tmp_path):
    path = tmp_path / "test_2k.tsv"
    path.write_bytes(b"id\tsentence1\tsentence2\tlabel\r\n10\tUno.\tDos.\t1\r\n\r\n")
    loaded = pawsx.read_pairs(path)
    assert [p.sentence2 for p in loaded.pairs] == ["Dos."]
    assert loaded.skipped == []


def _archive(tmp_path, members):
    """A tiny x-final.tar.gz: (name, bytes) are regular files, (name, ("link", target)) symlinks."""
    path = tmp_path / "x-final.tar.gz"
    with tarfile.open(path, "w:gz") as tar:
        for name, content in members:
            info = tarfile.TarInfo(name)
            if isinstance(content, tuple):
                info.type = tarfile.SYMTYPE
                info.linkname = content[1]
                tar.addfile(info)
            else:
                info.size = len(content)
                tar.addfile(info, io.BytesIO(content))
    return path


def test_extract_test_tsv_writes_only_the_spanish_test_file(tmp_path):
    archive = _archive(tmp_path, [
        ("x-final/es/dev_2k.tsv", b"dev"),
        ("x-final/fr/test_2k.tsv", b"fr"),
        ("x-final/es/test_2k.tsv", b"es-test"),
        ("../evil.txt", b"evil"),
    ])
    dest = tmp_path / "out"
    written = pawsx.extract_test_tsv(archive, dest)
    assert written.read_bytes() == b"es-test"
    assert sorted(p.name for p in dest.rglob("*") if p.is_file()) == [written.name]
    assert not (tmp_path / "evil.txt").exists()


def test_extract_test_tsv_fails_when_the_member_is_missing(tmp_path):
    archive = _archive(tmp_path, [("x-final/fr/test_2k.tsv", b"fr")])
    with pytest.raises(FileNotFoundError):
        pawsx.extract_test_tsv(archive, tmp_path / "out")


def test_extract_test_tsv_refuses_a_member_that_is_a_symlink(tmp_path):
    archive = _archive(tmp_path, [("x-final/es/test_2k.tsv", ("link", "/etc/passwd"))])
    with pytest.raises(ValueError):
        pawsx.extract_test_tsv(archive, tmp_path / "out")


# Two-dimensional fixtures with exact cosines: x and y are identical (1.0), z and w are
# 3-4-5 triangles (cos(z, w) = 0.96, cos(x, w) = cos(y, w) = 0.8, cos(x, z) = 0.6).
NEIGHBOR_VECTORS = {
    "es:y": [2.0, 0.0],
    "es:z": [3.0, 4.0],
    "es:x": [1.0, 0.0],
    "es:w": [4.0, 3.0],
}


def test_find_pairs_lists_each_pair_once_with_ids_in_order_sorted_by_cosine():
    pairs = neighbors.find_pairs(NEIGHBOR_VECTORS, min_cos=0.75)
    assert [(p.a_id, p.b_id) for p in pairs] == [
        ("es:x", "es:y"),
        ("es:w", "es:z"),
        ("es:w", "es:x"),
        ("es:w", "es:y"),
    ]
    assert [p.cosine for p in pairs] == pytest.approx([1.0, 0.96, 0.8, 0.8])


def test_find_pairs_keeps_only_pairs_at_or_above_the_threshold():
    pairs = neighbors.find_pairs(NEIGHBOR_VECTORS, min_cos=0.9)
    assert [(p.a_id, p.b_id) for p in pairs] == [("es:x", "es:y"), ("es:w", "es:z")]


def test_find_pairs_returns_nothing_for_one_vector_or_a_high_threshold():
    assert neighbors.find_pairs({"es:x": [1.0, 0.0]}, min_cos=0.0) == []
    assert neighbors.find_pairs(NEIGHBOR_VECTORS, min_cos=1.01) == []


def test_find_pairs_does_not_require_unit_vectors():
    pairs = neighbors.find_pairs({"es:a": [10.0, 0.0], "es:b": [0.1, 0.0]}, min_cos=0.99)
    assert [p.cosine for p in pairs] == pytest.approx([1.0])


def test_pair_records_carry_the_ids_texts_and_cosine_of_each_pair():
    pairs = neighbors.find_pairs(NEIGHBOR_VECTORS, min_cos=0.9)
    texts = {"es:x": "Texto X", "es:y": "Texto Y", "es:w": "Texto W", "es:z": "Texto Z"}
    records = neighbors.pair_records(pairs, texts)
    assert records[0] == {
        "pair_id": "es:x|es:y",
        "a_id": "es:x",
        "b_id": "es:y",
        "a": "Texto X",
        "b": "Texto Y",
        "cos_nomic_v1": pytest.approx(1.0),
    }
    assert [r["pair_id"] for r in records] == ["es:x|es:y", "es:w|es:z"]


def test_rows_to_tsv_round_trips_through_load_pairs(tmp_path):
    rows = [
        {"id": 10, "sentence1": "Uno.", "sentence2": "Dos.", "label": 1},
        {"id": 12, "sentence1": "Tres.", "sentence2": "Cuatro.", "label": 0},
    ]
    path = tmp_path / "test_2k.tsv"
    path.write_text(pawsx.rows_to_tsv(rows), encoding="utf-8")
    assert pawsx.load_pairs(path) == [
        pawsx.PawsPair("10", "Uno.", "Dos.", 1),
        pawsx.PawsPair("12", "Tres.", "Cuatro.", 0),
    ]


@pytest.mark.parametrize("bad", ["con\ttab", "con\nsalto"])
def test_rows_to_tsv_refuses_sentences_that_would_break_the_format(bad):
    with pytest.raises(ValueError):
        pawsx.rows_to_tsv([{"id": 1, "sentence1": bad, "sentence2": "ok", "label": 0}])


def test_pair_record_adds_both_models_cosines_to_the_pair():
    pair = pawsx.PawsPair("10", "Uno.", "Dos.", 1)
    assert pawsx.pair_record(pair, cos_v1=0.91, cos_v2=0.84) == {
        "id": "10",
        "sentence1": "Uno.",
        "sentence2": "Dos.",
        "label": 1,
        "cos_nomic_v1": 0.91,
        "cos_nomic_v2": 0.84,
    }
