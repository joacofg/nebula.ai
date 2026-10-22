# PAWS-X (Spanish test split): dataset notice

`pairs.jsonl` is derived from the Spanish test split of PAWS-X, set (a) of
`../preregistration.md`. The sentences and labels belong to the dataset; this repository adds
the two cosine columns.

## Citation

> Yinfei Yang, Yuan Zhang, Chris Tar and Jason Baldridge. "PAWS-X: A Cross-lingual Adversarial
> Dataset for Paraphrase Identification". Proceedings of EMNLP, 2019.

```bibtex
@InProceedings{pawsx2019emnlp,
  title = {{PAWS-X: A Cross-lingual Adversarial Dataset for Paraphrase Identification}},
  author = {Yang, Yinfei and Zhang, Yuan and Tar, Chris and Baldridge, Jason},
  booktitle = {Proc. of EMNLP},
  year = {2019}
}
```

Dataset page: <https://github.com/google-research-datasets/paws/tree/master/pawsx>

## License notice

Verbatim from <https://github.com/google-research-datasets/paws/blob/master/LICENSE>:

> The dataset may be freely used for any purpose, although acknowledgement of
> Google LLC ("Google") as the data source would be appreciated. The dataset is
> provided "AS IS" without any warranty, express or implied. Google disclaims all
> liability for any damages, direct or indirect, resulting from the use of the
> dataset.

Google LLC is acknowledged as the data source.

## Provenance

The pre-registration first named the official archive as the source (the change is recorded in its
"Amendment (data acquisition, 2026-10-22, before any precision was computed)", `../preregistration.md`):
`https://storage.googleapis.com/paws/pawsx/x-final.tar.gz`, member `x-final/es/test_2k.tsv`.
The URL is the one in the dataset README, but on 2026-10-22 Google's bucket answered every
anonymous request with HTTP 403 (`Anonymous caller does not have storage.objects.get access`),
so the archive could not be downloaded and **no SHA-256 of the official archive exists in this
repository**. `scripts/cache_eval/pawsx.py` still tries it first and records its SHA-256 if it
is ever served.

The same split was taken instead from the Hugging Face dataset
[`google-research-datasets/paws-x`](https://huggingface.co/datasets/google-research-datasets/paws-x),
published by the same organization (Hugging Face repository revision
`4cd8187c404bda33cb1f62b49b001115862acf37`, config `es`, split `test`):

| Item | SHA-256 |
| --- | --- |
| `es/test-00000-of-00001.parquet` (Hugging Face LFS object id) | `5ba872e113a79c783616e59d3d28ec0e922b6db745d797e5eb95010a32928bee` |
| `es_test_2k.tsv` (the same 2000 rows written in the official `id, sentence1, sentence2, label` layout by the datasets-server rows API) | `2ad948ee2549c06c3c8d3d1b5b7e6cbd32fef96d11a37c799f74a8b36f107f45` |

The parquet file was also downloaded and its SHA-256 matches the Hugging Face object id above;
its 2000 rows (ids, sentences, labels) are identical to the TSV that the pipeline wrote.
Whether this copy is byte-identical to `x-final/es/test_2k.tsv` could not be checked.

## Cleaning

The dataset README asks users to remove the `NS` placeholder (a sentence that failed to
translate) from the translated dev and test files. The split has 2000 rows and exactly one
such row: id `5815`, `sentence1` = `NS`, label 0 (line 1464 of the TSV). It is dropped, so
`pairs.jsonl` has **1999** rows. Its label is 0, so removing it can only remove a true negative
or a false positive from set (a), never a hit that counts toward recall.

## Columns of `pairs.jsonl`

`id`, `sentence1`, `sentence2`, `label` (1 = paraphrase), `cos_nomic_v1` (production embedding:
Ollama `nomic-embed-text`, digest `0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f`)
and `cos_nomic_v2` (sensitivity model: Ollama `nomic-embed-text-v2-moe`, digest
`ff9c2f10ef5e3722623a1b396e1e04efc27a93112c83e9b7b7b9ca1d05620965`). Both embed each sentence with
no prefix, unit-normalize it, and take the dot product.
