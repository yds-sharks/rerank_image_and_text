# Data Files

This repository keeps only small sample data under git.

Required runtime inputs:

- `data/retrieval_export.jsonl`: JSONL exported by `rag_retrieval_export`, with `retrieval.text_top20` and `retrieval.image_top20`.
- `data/multimodal_samples.db`: SQLite database used to map text blocks and image samples.
- `--model-path`: local path or Hugging Face model id for `Qwen3-VL-Embedding-2B`.

Current machine paths are recorded in `input_manifest.json`.

The full current files were not copied here because:

- `retrieval_export.jsonl` is 117M, over GitHub's normal single-file limit.
- `multimodal_samples.db` is 390M.
- the embedding model directory is 4.3G.

If you need to version these files, use Git LFS or place them in external storage and document the download location.
