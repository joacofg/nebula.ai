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
    assert result.dropped[0].reason == "length ratio 0.1364 is below 0.5"


@pytest.mark.parametrize(
    ("original_length", "paraphrase_length", "shown"),
    [
        (725, 361, "length ratio 0.4979 is below 0.5"),  # 0.497931..., not "0.50 is below 0.5"
        (100_000, 49_999, "length ratio 0.4999 is below 0.5"),  # 0.49999 would round to 0.5000
        (100_000, 200_001, "length ratio 2.0001 is above 2.0"),  # 2.00001 would round to 2.0000
    ],
)
def test_a_drop_reason_never_prints_a_ratio_that_reads_as_the_bound(
    original_length, paraphrase_length, shown
):
    prompt = PromptRow("code-0000", "code", "src:0", "a" * original_length, "corpus")
    result = paraphrase.build(
        [prompt], generate=lambda text, seed: "b" * paraphrase_length, embed_texts=fake_embed
    )
    assert [d.reason for d in result.dropped] == [shown]


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


# --- Report: PAWS-X curve ------------------------------------------------------------------


def paws_rows():
    """Six hand-made pairs: three paraphrases (label 1) and three non-paraphrases."""
    cosines = [(0.95, 1), (0.92, 0), (0.91, 1), (0.85, 1), (0.80, 0), (0.70, 0)]
    v2 = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60]
    return [
        {"id": str(i), "label": label_, "cos_nomic_v1": cos, "cos_nomic_v2": v2[i]}
        for i, (cos, label_) in enumerate(cosines)
    ]


def test_pawsx_curve_counts_hits_precision_recall_and_f05_at_each_threshold():
    from scripts.cache_eval import report

    curve = report.pawsx_curve(paws_rows(), model_key="nomic_v1", grid=(0.80, 0.90, 0.93, 0.99))
    by_t = {row["t"]: row for row in curve}
    assert [row["t"] for row in curve] == [0.80, 0.90, 0.93, 0.99]
    # t = 0.80: five hits (cosine >= t, the bound included), three of them paraphrases.
    assert (by_t[0.80]["hits"], by_t[0.80]["tp"]) == (5, 3)
    assert by_t[0.80]["precision"] == pytest.approx(0.6)
    assert by_t[0.80]["recall"] == pytest.approx(1.0)
    assert by_t[0.80]["f05"] == pytest.approx(0.75 / 1.15)
    assert (by_t[0.90]["hits"], by_t[0.90]["tp"]) == (3, 2)
    assert by_t[0.90]["precision"] == pytest.approx(2 / 3)
    assert by_t[0.90]["recall"] == pytest.approx(2 / 3)
    assert by_t[0.93]["precision"] == pytest.approx(1.0)
    assert by_t[0.93]["recall"] == pytest.approx(1 / 3)
    assert by_t[0.93]["f05"] == pytest.approx(1.25 * (1 / 3) / (0.25 + 1 / 3))
    # No hit: precision and F0.5 are undefined, not zero.
    assert (by_t[0.99]["hits"], by_t[0.99]["precision"], by_t[0.99]["f05"]) == (0, None, None)
    assert by_t[0.99]["recall"] == 0.0


def test_pawsx_curve_reads_the_cosine_of_the_model_it_is_given():
    from scripts.cache_eval import report

    [row] = report.pawsx_curve(paws_rows(), model_key="nomic_v2", grid=(0.45,))
    # Under v2 only the last two pairs (0.50 and 0.60), both non-paraphrases, reach 0.45.
    assert (row["hits"], row["tp"]) == (2, 0)


def test_f05_is_zero_when_hits_exist_but_none_is_right():
    from scripts.cache_eval import report

    assert report.f05(0.0, 0.0) == 0.0
    assert report.f05(None, 0.0) is None


# --- Report: the pre-registered verdict ----------------------------------------------------


def grid_point(t, pa, pc, hits_a=100, hits_c=100):
    return {"t": t, "precision_a": pa, "precision_c": pc, "hits_a": hits_a, "hits_c": hits_c}


def test_the_verdict_passes_when_both_precisions_reach_0_95_at_0_90():
    from scripts.cache_eval import report

    points = [grid_point(0.89, 0.99, 0.99), grid_point(0.90, 0.95, 0.96), grid_point(0.91, 0.97, 0.97)]
    result = report.verdict(points)
    assert result["verdict"] == "pass"
    assert result["recommended_t"] is None
    assert result["product_default_t"] == 0.90


def test_a_fail_recommends_the_smallest_eligible_t_with_both_precisions_at_0_95():
    from scripts.cache_eval import report

    points = [
        grid_point(0.90, 0.97, 0.94),
        grid_point(0.91, 0.99, 0.99, hits_c=19),  # safe, but too few hits in (c): not eligible
        grid_point(0.92, 0.95, 0.951),
        grid_point(0.93, 0.99, 0.99),
    ]
    result = report.verdict(points)
    assert result["verdict"] == "fail"
    assert result["recommended_t"] == 0.92
    assert result["product_default_t"] == 0.92
    assert result["eligible_t"] == [0.90, 0.92, 0.93]


def test_eligibility_needs_20_hits_in_each_set():
    from scripts.cache_eval import report

    points = [
        grid_point(0.90, 0.80, 0.80),
        grid_point(0.91, 0.99, 0.99, hits_a=19),
        grid_point(0.92, 0.99, 0.99, hits_a=20, hits_c=20),
    ]
    assert report.verdict(points)["recommended_t"] == 0.92


def test_a_safe_0_90_without_enough_hits_does_not_pass():
    from scripts.cache_eval import report

    points = [grid_point(0.90, 1.0, 1.0, hits_c=5), grid_point(0.95, 0.96, 0.96)]
    result = report.verdict(points)
    assert (result["verdict"], result["recommended_t"]) == ("fail", 0.95)


def test_the_verdict_compares_unrounded_precisions():
    from scripts.cache_eval import report

    # 0.9499 rounds to 0.95 at two decimals; it is still below the criterion.
    points = [grid_point(0.90, 0.9499, 0.99), grid_point(0.91, 0.95, 0.95)]
    result = report.verdict(points)
    assert (result["verdict"], result["recommended_t"]) == ("fail", 0.91)


def test_with_no_safe_t_the_eligible_t_with_the_best_worse_precision_is_recommended():
    from scripts.cache_eval import report

    points = [
        grid_point(0.90, 0.90, 0.99),  # min 0.90
        grid_point(0.91, 0.93, 0.94),  # min 0.93 (tie, smallest t wins)
        grid_point(0.92, 0.94, 0.93),  # min 0.93
        grid_point(0.93, 0.99, 0.99, hits_a=3),  # not eligible
        grid_point(0.94, 0.929999, 0.99),  # min just under 0.93
    ]
    result = report.verdict(points)
    assert result["verdict"] == "no_safe_threshold"
    assert result["recommended_t"] == 0.91
    assert result["product_default_t"] == 0.91


def test_with_no_eligible_point_the_cache_is_not_measurable_and_the_default_stays():
    from scripts.cache_eval import report

    points = [grid_point(0.90, 1.0, 1.0, hits_a=19), grid_point(0.91, None, None, hits_a=0, hits_c=0)]
    result = report.verdict(points)
    assert result["verdict"] == "not_measurable"
    assert result["recommended_t"] is None
    assert result["product_default_t"] == 0.90


# --- Replay: the gateway's own cache over an in-memory Qdrant ------------------------------


def _unit(*xs):
    return embed.normalize(list(xs))


def replay_fixture():
    """Three originals and two paraphrases in three dimensions, cosines easy to read.

    pA is 0.96 from its own original A. pB is 0.80 from its original B but 0.947 from D, a
    different prompt 0.95 from B: a false hit. B and D are each other's leave-one-out hit.
    """
    from scripts.cache_eval import replay

    d = _unit(0.0, 0.95, (1 - 0.95**2) ** 0.5)
    originals = [
        replay.Original("A", "texto A", "local", {"nomic_v1": _unit(1.0, 0.0, 0.0)}),
        replay.Original("B", "texto B", "frontier", {"nomic_v1": _unit(0.0, 1.0, 0.0)}),
        replay.Original("D", "texto D", "frontier", {"nomic_v1": d}),
    ]
    paraphrases = [
        replay.Paraphrase("A", "paráfrasis A", "frontier", {"nomic_v1": _unit(0.96, 0.28, 0.0)}),
        replay.Paraphrase("B", "paráfrasis B", "local", {"nomic_v1": _unit(0.0, 0.8, 0.6)}),
    ]
    return originals, paraphrases


async def test_the_replay_uses_the_gateways_semantic_cache_service():
    from nebula.services.semantic_cache_service import SemanticCacheService
    from scripts.cache_eval import replay

    originals, _ = replay_fixture()
    cache = await replay.build_cache(originals, model_key="nomic_v1")
    assert replay.SemanticCacheService is SemanticCacheService
    assert type(cache) is SemanticCacheService
    assert cache.enabled


async def test_paraphrase_replay_counts_correct_false_and_leave_one_out_hits():
    from scripts.cache_eval import replay

    originals, paraphrases = replay_fixture()
    cache = await replay.build_cache(originals, model_key="nomic_v1")
    at_090 = await replay.paraphrase_replay(cache, paraphrases, originals, t=0.90, model_key="nomic_v1")
    # pA hits A (correct); pB hits D (false); B and D hit each other leave-one-out (false).
    assert (at_090["correct_hits"], at_090["false_hits"]) == (1, 3)
    assert (at_090["paraphrase_hits"], at_090["loo_hits"], at_090["hits"]) == (2, 2, 4)
    assert at_090["precision"] == pytest.approx(0.25)
    assert at_090["recall"] == pytest.approx(0.5)
    assert at_090["tier_blocked"] == 0
    at_0955 = await replay.paraphrase_replay(cache, paraphrases, originals, t=0.955, model_key="nomic_v1")
    assert (at_0955["correct_hits"], at_0955["false_hits"], at_0955["precision"]) == (1, 0, 1.0)


async def test_leave_one_out_leaves_the_cache_as_it_was():
    from scripts.cache_eval import replay

    originals, paraphrases = replay_fixture()
    cache = await replay.build_cache(originals, model_key="nomic_v1")
    await replay.paraphrase_replay(cache, paraphrases, originals, t=0.90, model_key="nomic_v1")
    [own] = await replay.best_candidates(cache, [originals[0]], model_key="nomic_v1")
    assert own.prompt_id == "A" and own.score == pytest.approx(1.0)


class FailingQdrant:
    """An in-memory Qdrant whose writes or queries can be made to fail, as a broken server would.
    The gateway's cache swallows both (a failed store is logged, a failed lookup is a miss)."""

    def __new__(cls, *, fail_upsert=False, fail_query=False):
        from qdrant_client import AsyncQdrantClient

        class _Failing(AsyncQdrantClient):
            async def upsert(self, *args, **kwargs):
                if self.fail_upsert:
                    raise RuntimeError("qdrant upsert failed")
                return await super().upsert(*args, **kwargs)

            async def query_points(self, *args, **kwargs):
                if self.fail_query:
                    raise RuntimeError("qdrant query failed")
                return await super().query_points(*args, **kwargs)

        client = _Failing(location=":memory:")
        client.fail_upsert, client.fail_query = fail_upsert, fail_query
        return client


async def test_a_cache_that_fails_to_store_stops_the_replay():
    from scripts.cache_eval import replay

    originals, _ = replay_fixture()
    with pytest.raises(RuntimeError, match="stored"):
        await replay.build_cache(originals, model_key="nomic_v1", client=FailingQdrant(fail_upsert=True))


async def test_a_cache_that_fails_to_look_up_stops_the_replay_instead_of_counting_misses():
    from scripts.cache_eval import replay

    originals, paraphrases = replay_fixture()
    client = FailingQdrant()
    cache = await replay.build_cache(originals, model_key="nomic_v1", client=client)
    client.fail_query = True
    with pytest.raises(RuntimeError, match="lookup"):
        await replay.paraphrase_replay(cache, paraphrases, originals, t=0.90, model_key="nomic_v1")


async def test_a_failing_cache_stops_the_savings_trace():
    from scripts.cache_eval import replay

    originals, paraphrases, prices = savings_fixture()
    requests = [replay.Request("fresh", "A"), replay.Request("fresh", "B"), replay.Request("exact", "A")]
    for client in (FailingQdrant(fail_upsert=True), FailingQdrant(fail_query=True)):
        with pytest.raises(RuntimeError):
            await replay.simulate(
                requests, originals, paraphrases, prices, model_key="nomic_v1", t=0.90, client=client
            )


async def test_a_lookup_returns_the_best_candidate_even_at_a_negative_cosine():
    from scripts.cache_eval import replay

    [a] = replay_fixture()[0][:1]
    cache = await replay.build_cache([a], model_key="nomic_v1")
    away = replay.Paraphrase("X", "lejos", "local", {"nomic_v1": _unit(-0.6, 0.8, 0.0)})
    [best] = await replay.best_candidates(cache, [away], model_key="nomic_v1")
    assert best.prompt_id == "A" and best.score == pytest.approx(-0.6, abs=1e-6)


async def test_with_the_tier_rule_on_a_frontier_paraphrase_cannot_take_a_local_answer():
    from scripts.cache_eval import replay

    originals, paraphrases = replay_fixture()
    cache = await replay.build_cache(originals, model_key="nomic_v1")
    on = await replay.paraphrase_replay(
        cache, paraphrases, originals, t=0.90, model_key="nomic_v1", tier_rule=True
    )
    # pA is routed to frontier and A's answer is local: blocked. pB (local) still takes D's.
    assert (on["correct_hits"], on["tier_blocked"], on["false_hits"]) == (0, 1, 3)
    assert on["precision"] == 0.0


# --- Replay: savings over a trace with repeats ---------------------------------------------


def test_a_trace_without_repeats_sends_every_original_once():
    from scripts.cache_eval import replay

    ids = [f"p{i}" for i in range(50)]
    requests = replay.trace(ids, {"p1", "p2"}, rate=0.0, n=50)
    assert [r.kind for r in requests] == ["fresh"] * 50
    assert sorted(r.prompt_id for r in requests) == sorted(ids)
    assert [r.prompt_id for r in requests] != ids  # shuffled with the seed


def test_a_trace_repeats_only_what_was_already_asked_and_paraphrases_only_paraphrased_prompts():
    from scripts.cache_eval import replay

    ids = [f"p{i:03d}" for i in range(1000)]
    paraphrased = set(ids[::5])
    requests = replay.trace(ids, paraphrased, rate=0.3, n=1000)
    seen: set[str] = set()
    for request in requests:
        if request.kind == "fresh":
            assert request.prompt_id not in seen
            seen.add(request.prompt_id)
        else:
            assert request.prompt_id in seen
            if request.kind == "paraphrase":
                assert request.prompt_id in paraphrased
    kinds = Counter(r.kind for r in requests)
    assert (kinds["exact"], kinds["paraphrase"]) == (150, 150)


@pytest.mark.parametrize("rate", [0.037, 0.05, 0.121, 0.31, 0.4])
def test_a_trace_has_exactly_the_rate_of_repeats_half_of_them_exact(rate):
    from scripts.cache_eval import replay

    ids = [f"p{i:03d}" for i in range(1000)]
    kinds = Counter(r.kind for r in replay.trace(ids, set(ids[::6]), rate=rate, n=1000))
    repeats = kinds["exact"] + kinds["paraphrase"]
    assert repeats == round(rate * 1000)
    assert kinds["exact"] - kinds["paraphrase"] in (0, 1)


def test_the_repeats_of_a_lower_rate_are_among_those_of_a_higher_one():
    from scripts.cache_eval import replay

    ids = [f"p{i:03d}" for i in range(1000)]
    low = replay.trace(ids, set(ids[::6]), rate=0.05, n=1000)
    high = replay.trace(ids, set(ids[::6]), rate=0.2, n=1000)
    repeat_at = lambda trace: {i for i, r in enumerate(trace) if r.kind != "fresh"}  # noqa: E731
    assert repeat_at(low) <= repeat_at(high)


def test_a_trace_is_fixed_by_its_seed():
    from scripts.cache_eval import replay

    ids = [f"p{i}" for i in range(200)]
    first = replay.trace(ids, set(ids[:40]), rate=0.2, n=200)
    assert replay.trace(list(reversed(ids)), set(ids[:40]), rate=0.2, n=200) == first
    assert replay.trace(ids, set(ids[:40]), rate=0.2, n=200, seed=1) != first


def savings_fixture():
    """Four orthogonal originals (no two can collide) and one paraphrase of A."""
    from scripts.cache_eval import replay

    tiers = {"A": "local", "B": "economy", "C": "frontier", "D": "frontier"}
    originals = [
        replay.Original(pid, f"texto {pid}", tiers[pid], {"nomic_v1": [float(i == j) for j in range(4)]})
        for i, pid in enumerate("ABCD")
    ]
    paraphrases = [
        replay.Paraphrase("A", "paráfrasis A", "frontier", {"nomic_v1": _unit(0.97, 0.0, 0.0, 0.243)})
    ]
    prices = replay.Prices(
        cost={
            "A": {"local": 0.0, "economy": 0.0005, "frontier": 0.001},
            "B": {"local": 0.0, "economy": 0.002, "frontier": 0.003},
            "C": {"local": 0.0, "economy": 0.001, "frontier": 0.003},
            "D": {"local": 0.0, "economy": 0.002, "frontier": 0.004},
        },
        quality={
            "A": {"local": 1.0, "economy": 1.0, "frontier": 1.0},
            "B": {"local": 0.0, "economy": 1.0, "frontier": 1.0},
            "C": {"local": 0.0, "economy": 0.0, "frontier": 1.0},
            "D": {"local": 0.0, "economy": 0.0, "frontier": 1.0},
        },
    )
    return originals, paraphrases, prices


async def test_without_repeats_the_cache_costs_exactly_what_the_router_alone_costs():
    from scripts.cache_eval import replay

    originals, paraphrases, prices = savings_fixture()
    [row] = await replay.savings_curve(
        originals, paraphrases, prices, model_key="nomic_v1", rates=[0.0], t=0.90, n=4
    )
    # Router alone: 0 + 0.002 + 0.003 + 0.004 over 4 requests = USD 2.25 per 1000.
    assert row["cost_per_1000"] == pytest.approx(2.25)
    assert row["router_only_cost_per_1000"] == pytest.approx(2.25)
    assert row["frontier_cost_per_1000"] == pytest.approx(2.75)
    assert row["extra_saving_vs_router"] == pytest.approx(0.0)
    assert row["saving_vs_frontier"] == pytest.approx(1 - 2.25 / 2.75)
    assert (row["hits"], row["false_hits"], row["quality"]) == (0, 0, 1.0)


async def test_a_repeat_hits_for_free_and_a_frontier_paraphrase_is_blocked_from_a_local_answer():
    from scripts.cache_eval import replay

    originals, paraphrases, prices = savings_fixture()
    requests = [
        replay.Request("fresh", "A"),
        replay.Request("fresh", "B"),
        replay.Request("exact", "B"),  # hits B's economy answer: free, quality kept (1)
        replay.Request("paraphrase", "A"),  # frontier-routed; A's answer is local: blocked
        replay.Request("paraphrase", "A"),  # now hits the frontier answer the block stored
    ]
    row = await replay.simulate(
        requests, originals, paraphrases, prices, model_key="nomic_v1", t=0.90
    )
    assert (row["hits"], row["correct_hits"], row["false_hits"], row["tier_blocked"]) == (2, 2, 0, 1)
    # Paid: B economy 0.002 and the blocked paraphrase at frontier 0.001, over 5 requests.
    assert row["cost_per_1000"] == pytest.approx(0.003 * 1000 / 5)
    # Router alone pays every request: 0 + 0.002 + 0.002 + 0.001 + 0.001.
    assert row["router_only_cost_per_1000"] == pytest.approx(0.006 * 1000 / 5)
    assert row["extra_saving_vs_router"] == pytest.approx(0.5)
    assert row["quality"] == pytest.approx(1.0)
    assert row["hit_rate"] == pytest.approx(0.4)


async def test_a_false_hit_is_free_but_worth_nothing():
    from scripts.cache_eval import replay

    _, _, prices = savings_fixture()
    near = [
        replay.Original("B", "texto B", "economy", {"nomic_v1": [1.0, 0.0]}),
        replay.Original("C", "texto C", "economy", {"nomic_v1": _unit(0.99, 0.141)}),
    ]
    row = await replay.simulate(
        [replay.Request("fresh", "B"), replay.Request("fresh", "C")], near, [], prices,
        model_key="nomic_v1", t=0.90,
    )
    assert (row["hits"], row["false_hits"], row["false_hit_rate"]) == (1, 1, 0.5)
    assert row["cost_per_1000"] == pytest.approx(0.002 * 1000 / 2)
    assert row["quality"] == pytest.approx(0.5)  # B served (1), C got B's answer (0)


# --- Report: human labels --------------------------------------------------------------------


def neighbor_pairs_for_report():
    cosines = [0.99, 0.96, 0.93, 0.91, 0.88, 0.86]
    return [
        {"pair_id": f"es:a-{i}|es:b-{i}", "a_id": f"es:a-{i}", "b_id": f"es:b-{i}", "a": "A", "b": "B",
         "cos_nomic_v1": cos}
        for i, cos in enumerate(cosines)
    ]


def label_row(pair_id, value):
    return {"pair_id": pair_id, "label": value, "rater_id": "human-es-1",
            "recorded_at": "2026-10-23T10:00:00+00:00"}


def test_missing_label_files_read_as_pendiente(tmp_path):
    from scripts.cache_eval import report

    labels = report.read_labels(tmp_path / "labels" / "human-es-1.jsonl")
    assert labels is None
    section = report.neighbors_section(neighbor_pairs_for_report(), labels, thresholds=(0.90,))
    assert section["human_labels"] == "pendiente"
    assert [band["pairs"] for band in section["bands"]] == [2, 2, 2]
    assert report.paraphrase_validation(sample_rows(4), None) == "pendiente"


def test_the_last_label_of_a_pair_wins(tmp_path):
    from scripts.cache_eval import report

    path = tmp_path / "human-es-1.jsonl"
    write_jsonl(path, [label_row("p1", "no"), label_row("p2", "sí"), label_row("p1", "sí")])
    assert report.read_labels(path) == {"p1": "sí", "p2": "sí"}


def test_neighbor_labels_give_acceptable_shares_by_band_and_agreement_with_the_cache():
    from scripts.cache_eval import report

    pairs = neighbor_pairs_for_report()
    labels = {pairs[0]["pair_id"]: "sí", pairs[1]["pair_id"]: "no", pairs[2]["pair_id"]: "no",
              pairs[3]["pair_id"]: "?", pairs[4]["pair_id"]: "no"}
    section = report.neighbors_section(pairs, labels, thresholds=(0.90, 0.95))
    human = section["human_labels"]
    assert human["labeled"] == 5 and human["pairs"] == 6
    top, middle, low = section["bands"]
    assert (top["si"], top["no"], top["acceptable_share"]) == (1, 1, 0.5)
    assert (middle["si"], middle["no"], middle["unsure"]) == (0, 1, 1)
    # At 0.90 the cache serves pairs 0-3; of the four sí/no labels it agrees on 0 (sí, served)
    # and 4 (no, not served): 2 of 4. At 0.95 it serves 0 and 1: agrees on 0, 2 and 4: 3 of 4.
    assert human["agreement"] == {"0.90": 0.5, "0.95": 0.75}


def test_neighbor_bands_read_the_cosine_column_they_are_given():
    from scripts.cache_eval import report

    pairs = [{"pair_id": f"p{i}", "cos_nomic_v2": cos} for i, cos in enumerate([0.97, 0.91, 0.86])]
    section = report.neighbors_section(pairs, None, thresholds=(), column="cos_nomic_v2")
    assert [band["pairs"] for band in section["bands"]] == [1, 1, 1]


def test_the_paraphrase_check_reports_the_faithful_share_of_the_labeled_sample():
    from scripts.cache_eval import report

    sample = sample_rows(5)
    labels = {"code-0000": "sí", "code-0001": "sí", "code-0002": "no", "code-0003": "?"}
    result = report.paraphrase_validation(sample, labels)
    assert (result["sample"], result["labeled"], result["si"], result["no"], result["unsure"]) == (5, 4, 2, 1, 1)
    assert result["faithful_rate"] == pytest.approx(2 / 3)


# --- Report: real data ----------------------------------------------------------------------

PRODUCTION_VECTORS = Path("artifacts/router-embeddings/none.json")
needs_vectors = pytest.mark.skipif(
    not PRODUCTION_VECTORS.exists(),
    reason="needs the corpus production vectors (python -m scripts.router.embed)",
)


@needs_vectors
def test_the_deployed_router_reproduces_the_cited_router_only_cost_within_a_cent():
    from nebula.services.learned_router import LearnedRouterModel
    from scripts.cache_eval import report

    check = report.router_only_check(
        router=LearnedRouterModel.from_file(report.ROUTER_PATH),
        replay_payload=json.loads(report.ROUTER_REPLAY_PATH.read_text()),
        vectors=json.loads(PRODUCTION_VECTORS.read_text()),
    )
    # The thesis cites USD 1.70 per 1000 prompts at quality target 0.95 (nested estimate).
    assert check["cited_cost_per_1000"] == pytest.approx(1.70, abs=0.01)
    assert check["corpus_prompts"] == 1250 and check["spanish_prompts"] == 1000
    assert abs(check["corpus_cost_per_1000"] - check["cited_cost_per_1000"]) <= 0.01


def test_prices_come_from_the_router_replay_costs_and_the_ground_truth_labels():
    from scripts.cache_eval import report

    rows = [{"key": "es:code-0001", "cost_economy": 0.002, "cost_frontier": 0.003},
            {"key": "en:code-0001", "cost_economy": 9.0, "cost_frontier": 9.0}]
    labels = [{"lang": "es", "prompt_id": "code-0001", "local_substitutable": False,
               "economy_substitutable": True},
              {"lang": "en", "prompt_id": "code-0001", "local_substitutable": True,
               "economy_substitutable": True}]
    prices = report.load_prices(rows, labels)
    assert prices.cost == {"code-0001": {"local": 0.0, "economy": 0.002, "frontier": 0.003}}
    assert prices.quality == {"code-0001": {"local": 0.0, "economy": 1.0, "frontier": 1.0}}


# --- Report: assembly -------------------------------------------------------------------------


def test_the_report_json_has_sorted_keys_and_six_decimal_floats():
    from scripts.cache_eval import report

    text = report.dumps({"b": 1 / 3, "a": [0.1 + 0.2, None, "sí"], "c": {"z": 2, "y": 1.0}})
    assert text == (
        '{\n  "a": [\n    0.3,\n    null,\n    "sí"\n  ],\n  "b": 0.333333,\n'
        '  "c": {\n    "y": 1.0,\n    "z": 2\n  }\n}\n'
    )
    with pytest.raises(ValueError):
        report.dumps({"x": float("nan")})


def tiny_inputs(**overrides):
    from scripts.cache_eval import report

    originals, paraphrases, prices = savings_fixture()
    # Router alone over the four fixture prompts at their tiers: USD 2.25 per 1000.
    router_check = {"spanish_cost_per_1000": 2.25, "corpus_cost_per_1000": 1.705,
                    "cited_cost_per_1000": 1.701}
    paraphrase_rows = [{"prompt_id": "A", "task_type": "code", "original": "texto A",
                        "paraphrase": "paráfrasis A", "cos_nomic_v1": 0.97, "cos_nomic_v2": 0.9}]
    fields = dict(
        originals=originals,
        paraphrases=paraphrases,
        paraphrase_rows=paraphrase_rows,
        dropped=[{"prompt_id": "B", "reason": "length ratio 0.1000 is below 0.5", "length_ratio": 0.1}],
        pawsx=paws_rows(),
        neighbors=neighbor_pairs_for_report(),
        sample=sample_rows(2),
        neighbor_labels=None,
        paraphrase_labels=None,
        prices=prices,
        router_check=router_check,
        model_keys=("nomic_v1",),
        rates=(0.0, 0.5),
        trace_length=4,
        provenance={"git_sha": "abc"},
    )
    fields.update(overrides)
    return report.Inputs(**fields)


async def test_the_report_is_byte_identical_for_the_same_inputs_and_says_pendiente():
    from scripts.cache_eval import report

    first = report.dumps(await report.build(tiny_inputs()))
    second = report.dumps(await report.build(tiny_inputs()))
    assert first == second
    data = json.loads(first)
    assert set(data) >= {"preregistration", "pawsx", "paraphrases", "neighbors",
                         "paraphrase_validation", "savings", "models", "provenance"}
    assert data["neighbors"]["human_labels"] == "pendiente"
    assert data["paraphrase_validation"] == "pendiente"
    # Four originals cannot give 20 hits in (c): nothing is eligible.
    assert data["preregistration"]["verdict"] == "not_measurable"
    assert data["savings"]["nomic_v1"]["0.90"]["curve"][0]["r"] == 0.0
    assert "pendiente" in report.render_markdown(data)


async def test_the_sensitivity_model_gets_the_rules_outcome_but_never_sets_the_product_default():
    from dataclasses import replace

    from scripts.cache_eval import report

    base = tiny_inputs()
    both = lambda items: [replace(i, vectors={**i.vectors, "nomic_v2": i.vectors["nomic_v1"]}) for i in items]  # noqa: E731
    inputs = replace(base, originals=both(base.originals), paraphrases=both(base.paraphrases),
                     model_keys=("nomic_v1", "nomic_v2"))
    data = json.loads(report.dumps(await report.build(inputs)))
    [sensitivity] = data["models"]["sensitivity"]
    assert sensitivity["name"] == "nomic-embed-text-v2-moe"
    assert "product_default_t" not in sensitivity["verdict"]
    assert "product_default_t" in data["preregistration"]
    section = report.render_markdown(data).split("## Sensitivity")[1].split("## Limitations")[0]
    assert "product default" not in section and "changes nothing in the product" in section


async def test_the_report_refuses_a_savings_baseline_that_is_not_the_routers():
    from scripts.cache_eval import report

    wrong = {"spanish_cost_per_1000": 2.30, "corpus_cost_per_1000": 1.705, "cited_cost_per_1000": 1.701}
    with pytest.raises(ValueError, match="router-only"):
        await report.build(tiny_inputs(router_check=wrong))


# --- The committed report -----------------------------------------------------------------------

REPORT_JSON = Path("benchmarks/cache/v1/report.json")


def committed_report():
    return json.loads(REPORT_JSON.read_text(encoding="utf-8"))


def test_the_committed_verdict_follows_from_its_own_grid():
    from scripts.cache_eval import report

    data = committed_report()
    pre = data["preregistration"]
    assert pre["verdict"] in {"pass", "fail", "no_safe_threshold", "not_measurable"}
    recomputed = report.verdict(pre["grid"])
    assert (recomputed["verdict"], recomputed["recommended_t"]) == (pre["verdict"], pre["recommended_t"])
    assert [p["t"] for p in pre["grid"]] == list(report.GRID)
    assert pre["at_default"]["t"] == 0.9
    assert pre["valid_paraphrases"] == 173 and pre["leave_one_out_originals"] == 1000
    for key in ("precision_a", "precision_c", "recall_a", "recall_c", "hits_a", "hits_c"):
        assert key in pre["at_default"]
    if pre["recommended_t"] is not None:
        assert pre["at_recommended"]["t"] == pre["recommended_t"]


def test_the_committed_savings_start_from_the_routers_own_cost():
    data = committed_report()
    consistency = data["savings"]["consistency"]
    # The thesis cites USD 1.70 per 1000 for the router alone at target 0.95; the shipped
    # router reproduces it on the corpus within a cent.
    assert consistency["cited_cost_per_1000"] == pytest.approx(1.70, abs=0.01)
    assert consistency["corpus_cost_per_1000"] == pytest.approx(consistency["cited_cost_per_1000"], abs=0.01)
    for block in data["savings"]["nomic_v1"].values():
        [r0] = [row for row in block["curve"] if row["r"] == 0.0]
        assert r0["router_only_cost_per_1000"] == pytest.approx(consistency["spanish_cost_per_1000"], abs=1e-6)
        assert r0["requests"] == 1000 and r0["fresh"] == 1000
        assert set(block["cited"]) == {"wildchat", "lmsys_exact_duplicates", "meancache"}


def test_the_committed_report_matches_the_committed_data_and_code():
    data = committed_report()
    files = data["provenance"]["files"]
    data_files = (
        "benchmarks/cache/v1/preregistration.md", "benchmarks/cache/v1/pawsx/pairs.jsonl",
        "benchmarks/cache/v1/neighbors/pairs.jsonl", "benchmarks/cache/v1/paraphrases/paraphrases.jsonl",
        "benchmarks/cache/v1/paraphrases/dropped.jsonl", "benchmarks/cache/v1/paraphrases/sample.jsonl",
        "benchmarks/ground-truth/v1/prompts.es.jsonl", "benchmarks/ground-truth/v1/tiers.jsonl",
        "src/nebula/data/learned_router_v1.json", "src/nebula/data/router_replay_v1.json",
    )
    # A later edit of the code that computed the report makes this stale report fail loudly.
    code_files = (
        "scripts/cache_eval/replay.py", "scripts/cache_eval/report.py", "scripts/cache_eval/embed.py",
        "src/nebula/services/semantic_cache_service.py", "src/nebula/services/learned_router.py",
    )
    for path in data_files + code_files:
        assert files[path] == hashlib.sha256(Path(path).read_bytes()).hexdigest(), path


def test_the_committed_report_says_which_inputs_differed_from_its_commit():
    provenance = committed_report()["provenance"]
    assert isinstance(provenance["files_differing_from_git_sha"], list)
    assert set(provenance["files_differing_from_git_sha"]) <= set(provenance["files"])
    markdown = Path("benchmarks/cache/v1/report.md").read_text(encoding="utf-8")
    assert "SHA-256 of each file in report.json is the authority" in markdown


def test_the_committed_report_says_pendiente_until_labels_exist():
    data = committed_report()
    markdown = Path("benchmarks/cache/v1/report.md").read_text(encoding="utf-8")
    for set_name, section in (("neighbors", data["neighbors"]["human_labels"]),
                              ("paraphrases", data["paraphrase_validation"])):
        if not Path(f"benchmarks/cache/v1/{set_name}/labels/human-es-1.jsonl").exists():
            assert section == "pendiente"
            assert "pendiente" in markdown
    assert "blind spot" in markdown


def test_the_grid_is_0_80_to_0_99_in_hundredths():
    from scripts.cache_eval import report

    assert report.GRID[0] == 0.8 and report.GRID[-1] == 0.99 and len(report.GRID) == 20
    assert 0.9 in report.GRID
