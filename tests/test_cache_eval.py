"""Pure-function seams of the cache-eval data stage: vectors, PAWS-X pairs, corpus neighbors."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest

from scripts.cache_eval import embed, label, neighbors, paraphrase, pawsx
from scripts.ground_truth.records import PromptRow, read_rows


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


def test_find_pairs_includes_a_pair_exactly_at_the_threshold():
    # cos([1, 0], [3, 4]) is exactly 0.6 in floating point, so this pins ">=" against ">"
    vectors = {"es:x": [1.0, 0.0], "es:z": [3.0, 4.0]}
    assert [(p.a_id, p.b_id) for p in neighbors.find_pairs(vectors, min_cos=0.6)] == [("es:x", "es:z")]
    assert neighbors.find_pairs(vectors, min_cos=0.6000001) == []


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


def _sha256_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_verify_test_tsv_accepts_the_file_with_the_expected_hash_and_row_count(tmp_path):
    # the NS placeholder row counts: it is dropped later, not here
    path = _tsv(tmp_path, "10\tUno.\tDos.\t1", "5815\tNS\tTres.\t0", "12\tCuatro.\tCinco.\t0")
    pawsx.verify_test_tsv(path, sha256=_sha256_of(path), rows=3)


def test_verify_test_tsv_refuses_a_file_whose_hash_differs_from_the_recorded_one(tmp_path):
    path = _tsv(tmp_path, "10\tUno.\tDos.\t1")
    with pytest.raises(ValueError, match="SHA-256"):
        pawsx.verify_test_tsv(path, sha256="0" * 64, rows=1)


def test_verify_test_tsv_refuses_a_file_with_another_number_of_rows(tmp_path):
    path = _tsv(tmp_path, "10\tUno.\tDos.\t1", "12\tTres.\tCuatro.\t0")
    with pytest.raises(ValueError, match="rows"):
        pawsx.verify_test_tsv(path, sha256=_sha256_of(path), rows=2000)


def test_the_expected_hash_and_row_count_are_the_ones_recorded_in_the_license_notice():
    notice = Path("benchmarks/cache/v1/pawsx/LICENSE.md").read_text(encoding="utf-8")
    assert pawsx.EXPECTED_TSV_SHA256 in notice
    assert pawsx.EXPECTED_RAW_ROWS == 2000
    assert "2000 rows" in notice


def test_fetch_test_tsv_verifies_a_file_it_finds_in_the_downloads(tmp_path, monkeypatch):
    monkeypatch.setattr(pawsx, "OFFICIAL_DIR", tmp_path / "official")
    monkeypatch.setattr(pawsx, "MIRROR_DIR", tmp_path / "mirror")
    (tmp_path / "mirror").mkdir()
    (tmp_path / "mirror" / pawsx.TEST_TSV_NAME).write_text(PAWS_HEADER + "10\tUno.\tDos.\t1\n")
    with pytest.raises(ValueError, match="SHA-256"):
        pawsx.fetch_test_tsv()


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


# --- Paraphrases (set c) ------------------------------------------------------------------


def corpus_rows(tasks=("code", "factual_qa", "open_writing"), size=10):
    return [
        PromptRow(
            prompt_id=f"{task}-{i:04d}",
            task_type=task,
            source=f"src:{i}",
            prompt=f"Pregunta {task} número {i}",
            role="corpus",
        )
        for task in tasks
        for i in range(size)
    ]


def test_select_prompts_takes_the_same_number_of_prompts_from_every_task():
    picked = paraphrase.select_prompts(corpus_rows(), per_task=4)
    assert Counter(row.task_type for row in picked) == {"code": 4, "factual_qa": 4, "open_writing": 4}


def test_select_prompts_is_deterministic_and_ignores_the_order_of_the_input():
    rows = corpus_rows()
    first = paraphrase.select_prompts(rows, per_task=4, seed=7)
    assert paraphrase.select_prompts(list(reversed(rows)), per_task=4, seed=7) == first
    assert paraphrase.select_prompts(rows, per_task=4, seed=8) != first


def test_select_prompts_lists_the_prompts_in_id_order():
    picked = paraphrase.select_prompts(corpus_rows(), per_task=4)
    assert [row.prompt_id for row in picked] == sorted(row.prompt_id for row in picked)


def test_select_prompts_defaults_to_the_registered_sample():
    assert paraphrase.PER_TASK == 40
    assert paraphrase.SEED == 20261022


def test_select_prompts_fails_loudly_when_a_task_has_too_few_prompts():
    with pytest.raises(ValueError, match="code"):
        paraphrase.select_prompts(corpus_rows(size=3), per_task=4)


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("¿Qué tan grande es la Luna?", "¿Qué tan grande es la Luna?"),
        ("  ¿Qué tan grande es la Luna?\n", "¿Qué tan grande es la Luna?"),
        ('"¿Qué tan grande es la Luna?"', "¿Qué tan grande es la Luna?"),
        ("'Explica la fotosíntesis.'", "Explica la fotosíntesis."),
        ("«Explica la fotosíntesis.»", "Explica la fotosíntesis."),
        ("“Explica la fotosíntesis.”", "Explica la fotosíntesis."),
        ("Consulta reescrita: Explica la fotosíntesis.", "Explica la fotosíntesis."),
        ("Reescritura: \"Explica la fotosíntesis.\"", "Explica la fotosíntesis."),
        ("Aquí tienes la consulta reescrita:\n\nExplica la fotosíntesis.", "Explica la fotosíntesis."),
        ("**Consulta reescrita:** Explica la fotosíntesis.", "Explica la fotosíntesis."),
    ],
)
def test_clean_strips_whitespace_quotes_and_announcing_prefixes(reply, expected):
    assert paraphrase.clean(reply) == expected


@pytest.mark.parametrize(
    "reply",
    [
        'Escribe una función que devuelva "hola" y "chao".',
        'Qué significa "hola" en inglés',
        "Dime la hora: ahora mismo.",
        "Pregunta de «ejemplo» y de «prueba»",
        "",
    ],
)
def test_clean_keeps_quotes_and_colons_that_belong_to_the_text(reply):
    assert paraphrase.clean(reply) == reply


def test_clean_does_not_strip_quotes_that_only_look_like_a_pair():
    assert paraphrase.clean('"hola" y "chao"') == '"hola" y "chao"'


def test_chat_request_sends_the_instruction_as_the_system_message_and_the_prompt_as_the_user_message():
    request = paraphrase.chat_request("¿Qué es un átomo?", seed=20261022)
    assert request == {
        "model": "qwen2.5:7b",
        "stream": False,
        "options": {"temperature": 0, "seed": 20261022},
        "messages": [
            {
                "role": "system",
                "content": "Reescribe la siguiente consulta con otras palabras, sin cambiar lo que "
                "pide ni agregar información. Devuelve solo la consulta reescrita.",
            },
            {"role": "user", "content": "¿Qué es un átomo?"},
        ],
    }


class ScriptedGenerate:
    """Stands in for the model: replies are given per seed, calls are recorded."""

    def __init__(self, replies):
        self.replies = replies
        self.calls: list[tuple[str, int]] = []

    def __call__(self, prompt: str, seed: int) -> str:
        self.calls.append((prompt, seed))
        return self.replies[seed]


def test_rewrite_accepts_a_good_first_reply_without_retrying():
    generate = ScriptedGenerate({20261022: '"¿Qué es un átomo en realidad?"'})
    result = paraphrase.rewrite("¿Qué es un átomo?", generate)
    assert result == paraphrase.Rewritten(text="¿Qué es un átomo en realidad?", seed=20261022)
    assert generate.calls == [("¿Qué es un átomo?", 20261022)]


@pytest.mark.parametrize(
    "bad_reply",
    ["", "   \n", '"¿Qué es un átomo?"', "¿qué es   un átomo?", "Reescritura: ¿Qué es un átomo?"],
)
def test_rewrite_retries_once_with_the_next_seed_when_the_reply_is_empty_or_identical(bad_reply):
    generate = ScriptedGenerate({20261022: bad_reply, 20261023: "Dime qué es un átomo."})
    result = paraphrase.rewrite("¿Qué es un átomo?", generate)
    assert result == paraphrase.Rewritten(text="Dime qué es un átomo.", seed=20261023)
    assert [seed for _, seed in generate.calls] == [20261022, 20261023]


def test_cached_generate_never_asks_the_model_twice_for_the_same_prompt_and_seed(tmp_path):
    path = tmp_path / "generations.jsonl"
    generate = ScriptedGenerate({1: "uno", 2: "dos"})
    cached = paraphrase.cached_generate(generate, path)
    assert [cached("p", 1), cached("p", 1), cached("p", 2)] == ["uno", "uno", "dos"]
    assert generate.calls == [("p", 1), ("p", 2)]


def test_cached_generate_survives_a_restart_and_keeps_the_raw_reply(tmp_path):
    path = tmp_path / "generations.jsonl"
    paraphrase.cached_generate(ScriptedGenerate({1: '"uno"\n'}), path)("p", 1)
    again = ScriptedGenerate({1: "otra cosa"})
    assert paraphrase.cached_generate(again, path)("p", 1) == '"uno"\n'
    assert again.calls == []


def test_cached_generate_keys_the_cache_by_prompt_text_and_model(tmp_path):
    path = tmp_path / "generations.jsonl"
    paraphrase.cached_generate(ScriptedGenerate({1: "uno"}), path)("p", 1)
    other = ScriptedGenerate({1: "otro"})
    assert paraphrase.cached_generate(other, path)("q", 1) == "otro"
    [row, _] = [json.loads(line) for line in path.read_text().splitlines()]
    assert row == {
        "model": "qwen2.5:7b",
        "seed": 1,
        # sha256 of the messages sent for "p" (system instruction, then user prompt), as JSON
        # with sorted keys: [{"content": "<instruction>", "role": "system"}, {"content": "p", ...
        "messages_sha256": "24fe1debb53e4a3159fa7419d984cee09df53112ec325732381827f500e91dfe",
        "reply": "uno",
    }
    path.write_text(path.read_text().replace("qwen2.5:7b", "otro-modelo"))
    refetch = ScriptedGenerate({1: "nuevo"})
    assert paraphrase.cached_generate(refetch, path)("p", 1) == "nuevo"


def test_cached_generate_does_not_reuse_replies_made_with_another_instruction(tmp_path, monkeypatch):
    path = tmp_path / "generations.jsonl"
    paraphrase.cached_generate(ScriptedGenerate({1: "viejo"}), path)("p", 1)
    monkeypatch.setattr(paraphrase, "INSTRUCTION", "Otra instrucción.")
    assert paraphrase.cached_generate(ScriptedGenerate({1: "nuevo"}), path)("p", 1) == "nuevo"


def test_cached_generate_does_not_reuse_replies_made_with_another_message_layout(tmp_path):
    path = tmp_path / "generations.jsonl"
    paraphrase.cached_generate(ScriptedGenerate({1: "viejo"}), path)("p", 1)
    # the first version sent one user message: the instruction, a blank line, then the prompt
    old_messages = [{"role": "user", "content": f"{paraphrase.INSTRUCTION}\n\np"}]
    old_hash = hashlib.sha256(
        json.dumps(old_messages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    [row] = [json.loads(line) for line in path.read_text().splitlines()]
    assert row["messages_sha256"] != old_hash
    row["messages_sha256"] = old_hash
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n")
    assert paraphrase.cached_generate(ScriptedGenerate({1: "nuevo"}), path)("p", 1) == "nuevo"


def fake_embed(texts, *, model):
    """Two-dimensional vectors: the first axis counts the words, so cosines are easy to predict."""
    scale = 1.0 if model == "nomic-embed-text" else 2.0
    return [[scale * len(t.split()), 1.0] for t in texts]


def test_build_pairs_every_original_with_its_paraphrase_and_both_cosines():
    prompts = corpus_rows(tasks=("code",), size=2)
    replies = {
        "Pregunta code número 0": "Pregunta distinta code número cero",
        "Pregunta code número 1": "Pregunta code número 1 ",
    }
    result = paraphrase.build(
        prompts,
        generate=lambda prompt, seed: replies[prompt] if seed == 20261022 else "Otra cosa, uno",
        embed_texts=fake_embed,
    )
    [first, second] = result.records
    assert first == {
        "prompt_id": "code-0000",
        "task_type": "code",
        "original": "Pregunta code número 0",
        "paraphrase": "Pregunta distinta code número cero",
        "model": "qwen2.5:7b",
        "seed": 20261022,
        "cos_nomic_v1": pytest.approx(embed.cosine([4.0, 1.0], [5.0, 1.0])),
        "cos_nomic_v2": pytest.approx(embed.cosine([8.0, 1.0], [10.0, 1.0])),
    }
    # the second reply is identical to its original, so the retry seed produced the paraphrase
    assert (second["paraphrase"], second["seed"]) == ("Otra cosa, uno", 20261023)
    assert result.dropped == []


def test_build_reports_dropped_prompts_and_keeps_the_rest():
    prompts = corpus_rows(tasks=("code",), size=2)
    result = paraphrase.build(
        prompts,
        generate=lambda prompt, seed: "" if prompt.endswith("0") else f"Reformulado: {prompt}.",
        embed_texts=fake_embed,
    )
    assert [r["prompt_id"] for r in result.records] == ["code-0001"]
    assert [(d.prompt_id, d.kind, d.length_ratio) for d in result.dropped] == [
        ("code-0000", "empty_or_identical", 0.0)
    ]
    assert "empty" in result.dropped[0].reason


@pytest.mark.parametrize(
    ("paraphrase_length", "problem"),
    [(4, "too_short"), (5, None), (10, None), (20, None), (21, "too_long")],
)
def test_a_paraphrase_is_valid_from_half_to_twice_the_original_length_both_included(
    paraphrase_length, problem
):
    assert paraphrase.length_problem("a" * 10, "b" * paraphrase_length) == problem


def test_build_drops_paraphrases_outside_the_length_range_and_reports_their_ratio():
    prompts = corpus_rows(tasks=("code",), size=4)  # originals of 22 characters
    replies = {
        "Pregunta code número 0": "Sí.",  # an answer, 3 characters
        "Pregunta code número 1": "Pregunta distinta code número uno",  # 33 characters
        "Pregunta code número 2": " ".join(["Pregunta"] * 6),  # 53 characters, past twice 22
        "Pregunta code número 3": "x" * 11,  # exactly half
    }
    result = paraphrase.build(
        prompts, generate=lambda prompt, seed: replies[prompt], embed_texts=fake_embed
    )
    assert [r["prompt_id"] for r in result.records] == ["code-0001", "code-0003"]
    assert [(d.prompt_id, d.kind) for d in result.dropped] == [
        ("code-0000", "too_short"),
        ("code-0002", "too_long"),
    ]
    assert [d.length_ratio for d in result.dropped] == pytest.approx([3 / 22, 53 / 22])
    assert "0.14" in result.dropped[0].reason


def test_dropped_records_carry_the_prompt_id_the_reason_and_the_length_ratio():
    dropped = paraphrase.DroppedPrompt("code-0000", "length ratio 0.14 is below 0.5", "too_short", 3 / 22)
    assert paraphrase.dropped_record(dropped) == {
        "prompt_id": "code-0000",
        "reason": "length ratio 0.14 is below 0.5",
        "length_ratio": pytest.approx(3 / 22),
    }


def build_result(valid, dropped=0):
    records = paraphrase_records(valid)
    gone = [paraphrase.DroppedPrompt(f"x-{i}", "r", "too_short", 0.1) for i in range(dropped)]
    return paraphrase.BuildResult(records, gone)


def test_summary_counts_valid_paraphrases_and_drop_kinds():
    result = build_result(3)
    result.dropped.extend(
        [
            paraphrase.DroppedPrompt("a", "r", "too_long", 3.0),
            paraphrase.DroppedPrompt("b", "r", "too_short", 0.1),
            paraphrase.DroppedPrompt("c", "r", "too_short", 0.2),
        ]
    )
    text = "\n".join(paraphrase.summary(6, result))
    assert "6 prompts selected: 3 valid paraphrases, 3 dropped" in text
    assert "too_short: 2" in text and "too_long: 1" in text


def test_summary_says_so_when_fewer_than_150_paraphrases_are_valid():
    assert "fewer than 150" in "\n".join(paraphrase.summary(200, build_result(149, 51)))
    assert "fewer than 150" not in "\n".join(paraphrase.summary(200, build_result(150, 50)))


def paraphrase_records(n=100):
    return [
        {"prompt_id": f"code-{i:04d}", "task_type": "code", "original": f"O{i}",
         "paraphrase": f"P{i}", "model": "qwen2.5:7b", "seed": 20261022,
         "cos_nomic_v1": 0.9, "cos_nomic_v2": 0.8}
        for i in range(n)
    ]


def test_select_sample_has_only_the_blind_columns_with_a_as_the_original():
    [first, *_] = paraphrase.select_sample(paraphrase_records(), size=5)
    assert set(first) == {"pair_id", "a", "b"}
    assert first["a"].startswith("O") and first["b"] == first["a"].replace("O", "P")
    assert first["pair_id"].startswith("code-")


def test_select_sample_is_deterministic_without_repeats_and_ignores_input_order():
    records = paraphrase_records()
    sample = paraphrase.select_sample(records, size=40)
    assert len({row["pair_id"] for row in sample}) == 40
    assert paraphrase.select_sample(list(reversed(records)), size=40) == sample
    assert paraphrase.select_sample(records, size=40, seed=1) != sample


def test_select_sample_defaults_to_40_pairs_and_never_exceeds_what_exists():
    assert len(paraphrase.select_sample(paraphrase_records())) == 40
    assert len(paraphrase.select_sample(paraphrase_records(7))) == 7


def test_rewrite_drops_the_prompt_when_the_retry_also_fails():
    generate = ScriptedGenerate({20261022: "", 20261023: "¿Qué es un átomo?"})
    result = paraphrase.rewrite("¿Qué es un átomo?", generate)
    assert isinstance(result, paraphrase.Dropped)
    assert "identical" in result.reason
    assert len(generate.calls) == 2


def test_the_committed_paraphrases_and_dropped_rows_cover_the_registered_selection_exactly():
    root = Path("benchmarks/cache/v1/paraphrases")
    corpus = read_rows(Path("benchmarks/ground-truth/v1/prompts.es.jsonl"), PromptRow)
    selected = paraphrase.select_prompts(corpus)
    assert len(selected) == 200
    assert Counter(p.task_type for p in selected) == dict.fromkeys(sorted({p.task_type for p in selected}), 40)
    rows = [json.loads(line) for line in (root / "paraphrases.jsonl").read_text("utf-8").splitlines()]
    dropped = [json.loads(line) for line in (root / "dropped.jsonl").read_text("utf-8").splitlines()]
    assert sorted([r["prompt_id"] for r in rows] + [d["prompt_id"] for d in dropped]) == [
        p.prompt_id for p in selected
    ]
    originals = {p.prompt_id: p.prompt for p in selected}
    assert all(r["original"] == originals[r["prompt_id"]] for r in rows)
    assert {r["model"] for r in rows} == {"qwen2.5:7b"}
    assert {r["seed"] for r in rows} <= {20261022, 20261023}
    assert all(r["paraphrase"].strip() and r["paraphrase"] != r["original"] for r in rows)
    assert all(-1.0 <= r["cos_nomic_v1"] <= 1.0 and -1.0 <= r["cos_nomic_v2"] <= 1.0 for r in rows)


def test_every_committed_paraphrase_is_valid_and_every_dropped_row_is_not():
    root = Path("benchmarks/cache/v1/paraphrases")
    rows = [json.loads(line) for line in (root / "paraphrases.jsonl").read_text("utf-8").splitlines()]
    dropped = [json.loads(line) for line in (root / "dropped.jsonl").read_text("utf-8").splitlines()]
    assert rows
    assert all(0.5 <= len(r["paraphrase"]) / len(r["original"]) <= 2.0 for r in rows)
    assert all(set(d) == {"prompt_id", "reason", "length_ratio"} for d in dropped)

    def explained(d):
        return not 0.5 <= d["length_ratio"] <= 2.0 or "empty" in d["reason"] or "identical" in d["reason"]

    assert all(explained(d) for d in dropped)


def test_the_committed_sample_is_the_registered_blind_draw_of_40_pairs():
    root = Path("benchmarks/cache/v1/paraphrases")
    rows = [json.loads(line) for line in (root / "paraphrases.jsonl").read_text("utf-8").splitlines()]
    sample = [json.loads(line) for line in (root / "sample.jsonl").read_text("utf-8").splitlines()]
    assert len(sample) == 40
    assert all(set(row) == {"pair_id", "a", "b"} for row in sample)
    assert sample == paraphrase.select_sample(rows)
    by_id = {r["prompt_id"]: r for r in rows}
    assert all((by_id[s["pair_id"]]["original"], by_id[s["pair_id"]]["paraphrase"]) == (s["a"], s["b"]) for s in sample)


# --- Labeling CLI -------------------------------------------------------------------------


def neighbor_rows(n=30):
    """Rows as ``neighbors/pairs.jsonl`` has them: sorted by cosine, with ids and the cosine."""
    return [
        {
            "pair_id": f"es:code-{i:04d}|es:code-{i + 100:04d}",
            "a_id": f"es:code-{i:04d}",
            "b_id": f"es:code-{i + 100:04d}",
            "a": f"Texto A número {i}",
            "b": f"Texto B número {i}",
            "cos_nomic_v1": 0.9137 - i * 0.001,
        }
        for i in range(n)
    ]


def sample_rows(n=6):
    return [{"pair_id": f"code-{i:04d}", "a": f"Original {i}", "b": f"Paráfrasis {i}"} for i in range(n)]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class Session:
    """Drives ``label.main`` without a terminal: scripted answers in, captured output out."""

    def __init__(self, root, set_name, answers):
        self.outputs: list[str] = []
        self.prompts: list[str] = []
        pending = iter(answers)

        def input_fn(prompt=""):
            self.prompts.append(prompt)
            try:
                return next(pending)
            except StopIteration:
                raise EOFError from None

        self.code = label.main(
            [set_name, "--root", str(root)], input_fn=input_fn, output_fn=self.outputs.append
        )

    @property
    def text(self):
        return "\n".join(self.outputs)


def test_the_labeler_asks_the_registered_spanish_questions():
    assert label.SETS["neighbors"].question == "¿Una respuesta a A sirve para B?"
    assert label.SETS["paraphrases"].question == "¿B pide lo mismo que A?"
    assert label.RATER_ID == "human-es-1"
    assert label.SEED == 20261022


def test_presentation_is_a_fixed_shuffle_that_ignores_the_order_of_the_pairs_file():
    rows = neighbor_rows()
    shown = label.presentation(rows)
    assert label.presentation(list(reversed(rows))) == shown
    assert [p.pair_id for p in shown] != [r["pair_id"] for r in rows]
    assert [p.pair_id for p in shown] != sorted(r["pair_id"] for r in rows)
    assert sorted(p.pair_id for p in shown) == sorted(r["pair_id"] for r in rows)


def test_presentation_swaps_a_and_b_at_random_and_keeps_every_text():
    rows = neighbor_rows()
    shown = label.presentation(rows)
    by_id = {r["pair_id"]: r for r in rows}
    swapped = [p for p in shown if p.a == by_id[p.pair_id]["b"]]
    straight = [p for p in shown if p.a == by_id[p.pair_id]["a"]]
    assert len(swapped) + len(straight) == len(rows)
    assert swapped and straight
    for p in shown:
        assert {p.a, p.b} == {by_id[p.pair_id]["a"], by_id[p.pair_id]["b"]}


def test_presentation_depends_on_the_seed():
    rows = neighbor_rows()
    assert label.presentation(rows, seed=1) != label.presentation(rows)


def test_the_labeler_appends_one_row_per_answer_with_the_spanish_label(tmp_path):
    write_jsonl(tmp_path / "neighbors" / "pairs.jsonl", neighbor_rows(3))
    session = Session(tmp_path, "neighbors", ["s", "n", "?"])
    assert session.code == 0
    rows = read_jsonl(tmp_path / "neighbors" / "labels" / "human-es-1.jsonl")
    assert [r["label"] for r in rows] == ["sí", "no", "?"]
    order = [p.pair_id for p in label.presentation(neighbor_rows(3))]
    assert [r["pair_id"] for r in rows] == order
    for row in rows:
        assert set(row) == {"pair_id", "label", "rater_id", "recorded_at"}
        assert row["rater_id"] == "human-es-1"
        assert datetime.fromisoformat(row["recorded_at"]).tzinfo is not None


def test_the_labeler_accepts_only_s_n_and_question_mark_and_asks_again(tmp_path):
    write_jsonl(tmp_path / "neighbors" / "pairs.jsonl", neighbor_rows(1))
    session = Session(tmp_path, "neighbors", ["x", "", "sí", "yes", "1", "S "])
    rows = read_jsonl(tmp_path / "neighbors" / "labels" / "human-es-1.jsonl")
    assert [r["label"] for r in rows] == ["sí"]
    assert session.text.count("Respuesta no válida") == 5


def test_q_quits_and_the_next_run_resumes_with_the_pairs_not_yet_labeled(tmp_path):
    write_jsonl(tmp_path / "neighbors" / "pairs.jsonl", neighbor_rows(5))
    labels = tmp_path / "neighbors" / "labels" / "human-es-1.jsonl"
    first = Session(tmp_path, "neighbors", ["s", "n", "q", "s"])
    assert first.code == 0
    assert len(read_jsonl(labels)) == 2
    second = Session(tmp_path, "neighbors", ["?", "?", "?", "?"])
    rows = read_jsonl(labels)
    assert [r["label"] for r in rows] == ["sí", "no", "?", "?", "?"]
    assert [r["pair_id"] for r in rows] == [p.pair_id for p in label.presentation(neighbor_rows(5))]
    assert "Par 3 de 5" in second.text
    assert "Par 2 de 5" not in second.text


def test_the_labeler_stops_cleanly_when_the_input_ends(tmp_path):
    write_jsonl(tmp_path / "neighbors" / "pairs.jsonl", neighbor_rows(3))
    session = Session(tmp_path, "neighbors", ["s"])
    assert session.code == 0
    assert len(read_jsonl(tmp_path / "neighbors" / "labels" / "human-es-1.jsonl")) == 1


def test_the_labeler_does_nothing_when_every_pair_is_labeled(tmp_path):
    write_jsonl(tmp_path / "neighbors" / "pairs.jsonl", neighbor_rows(2))
    Session(tmp_path, "neighbors", ["s", "s"])
    again = Session(tmp_path, "neighbors", ["n"])
    assert again.prompts == []
    assert "No quedan pares" in again.text
    assert len(read_jsonl(tmp_path / "neighbors" / "labels" / "human-es-1.jsonl")) == 2


def test_the_labeler_shows_only_a_b_and_the_question_never_cosines_ids_or_tiers(tmp_path):
    write_jsonl(tmp_path / "neighbors" / "pairs.jsonl", neighbor_rows(4))
    session = Session(tmp_path, "neighbors", ["s", "s", "s", "s"])
    assert "¿Una respuesta a A sirve para B?" in session.text
    assert session.text.count("Texto A número") + session.text.count("Texto B número") == 8
    for secret in ("0.91", "0.9", "cos", "es:code", "|", "tier", "premium", "local", "economy"):
        assert secret not in session.text, secret
    for secret in ("0.91", "es:code", "cos"):
        assert all(secret not in prompt for prompt in session.prompts)


def test_the_labeler_presents_paraphrase_pairs_with_the_paraphrase_question(tmp_path):
    write_jsonl(tmp_path / "paraphrases" / "sample.jsonl", sample_rows(3))
    session = Session(tmp_path, "paraphrases", ["s", "n", "s"])
    assert "¿B pide lo mismo que A?" in session.text
    assert "¿Una respuesta a A" not in session.text
    rows = read_jsonl(tmp_path / "paraphrases" / "labels" / "human-es-1.jsonl")
    assert sorted(r["pair_id"] for r in rows) == ["code-0000", "code-0001", "code-0002"]
    assert "code-000" not in session.text


def test_the_labeler_reports_a_missing_pairs_file_and_writes_nothing(tmp_path):
    session = Session(tmp_path, "paraphrases", ["s"])
    assert session.code == 1
    assert "make cache-paraphrases" in session.text
    assert not (tmp_path / "paraphrases" / "labels").exists()
