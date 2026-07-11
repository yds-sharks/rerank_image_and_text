#!/usr/bin/env python3
"""Qwen3-VL embedding / PPR rerank adapter.

The implementation reuses the validated PPR code in
`核心代码梳理/rerank_multimodal_ppr.py` through dynamic import. This keeps the
agentic runtime thin while preserving identical rerank behavior.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

CODE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = CODE_DIR / "agentic_runtime_config.json"


def load_config(path: str | Path = DEFAULT_CONFIG) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_legacy_rerank_module(script_path: str):
    path = Path(script_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing rerank script: {path}")
    spec = importlib.util.spec_from_file_location("agentic_legacy_ppr_rerank", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load rerank script: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PPRReranker:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config()
        paths = self.config.get("paths", {})
        rerank_cfg = self.config.get("rerank", {})
        self.module = load_legacy_rerank_module(paths["legacy_rerank_script"])
        self.encoder = self.module.Qwen3VLEncoder(
            model_path=rerank_cfg.get("model_path"),
            device=rerank_cfg.get("device", "cuda:0"),
            batch_size=int(rerank_cfg.get("batch_size", 4)),
        )
        self.rerank_cfg = rerank_cfg

    def _to_candidate(self, item: Dict[str, Any]):
        return self.module.Candidate(
            source=str(item.get("source") or item.get("retrieval_db") or "text"),
            rank=int(item.get("rank") or 0),
            first_stage_score=float(item.get("score") or item.get("first_stage_score") or 0.0),
            text=str(item.get("text") or item.get("content") or ""),
            doc_name=str(item.get("doc_name") or ""),
            page_idx=item.get("page_idx"),
            doc_id=str(item.get("doc_id") or ""),
            block_id=item.get("block_id"),
            sample_id=str(item.get("sample_id") or ""),
            group_id=str(item.get("group_id") or ""),
            image_path=str(item.get("image_path") or ""),
            image_id=str(item.get("image_id") or ""),
        )

    def rerank(self, query: str, candidates: List[Dict[str, Any]], *, select_k: Optional[int] = None) -> List[Dict[str, Any]]:
        if not candidates:
            return []
        text_candidates = [self._to_candidate(item) for item in candidates if (item.get("source") or item.get("retrieval_db")) != "image"]
        image_candidates = [self._to_candidate(item) for item in candidates if (item.get("source") or item.get("retrieval_db")) == "image"]
        bundle = self.module.QueryBundle(
            index=0,
            query=str(query or ""),
            text_candidates=text_candidates,
            image_candidates=image_candidates,
        )
        cfg = self.rerank_cfg
        export_record, debug_record = self.module.process_bundle(
            bundle,
            self.encoder,
            top_m_neighbors=int(cfg.get("top_m_neighbors", 8)),
            pair_boost=float(cfg.get("pair_boost", 0.2)),
            pair_min_weight=float(cfg.get("pair_min_weight", 0.4)),
            alpha=float(cfg.get("alpha", 0.35)),
            ppr_iters=int(cfg.get("ppr_iters", 20)),
            select_k=int(select_k or cfg.get("select_k", 5)),
            redundancy_weight=float(cfg.get("redundancy_weight", 0.15)),
            pair_complete_bonus=float(cfg.get("pair_complete_bonus", 0.05)),
            min_gain=float(cfg.get("min_gain", -1.0)),
        )
        selected = set(debug_record.get("selected_candidate_indices") or [])
        by_key = []
        for detail in debug_record.get("candidates", []):
            if detail.get("candidate_index") not in selected:
                continue
            by_key.append(detail)
        by_key.sort(key=lambda x: float(x.get("ppr_score", 0.0)), reverse=True)
        out: List[Dict[str, Any]] = []
        for rank, item in enumerate(by_key[: int(select_k or cfg.get("select_k", 5))], start=1):
            out.append(
                {
                    "rank": rank,
                    "source": item.get("source", ""),
                    "score": float(item.get("ppr_score", 0.0)),
                    "ppr_score": float(item.get("ppr_score", 0.0)),
                    "query_score": float(item.get("query_score", 0.0)),
                    "first_stage_score": float(item.get("first_stage_score", 0.0)),
                    "text": item.get("text", ""),
                    "content": item.get("text", ""),
                    "doc_id": item.get("doc_id", ""),
                    "doc_name": item.get("doc_name", ""),
                    "page_idx": item.get("page_idx"),
                    "block_id": item.get("block_id"),
                    "sample_id": item.get("sample_id", ""),
                    "group_id": item.get("group_id", ""),
                    "image_path": item.get("image_path", ""),
                }
            )
        return out


class NoOpReranker:
    def __init__(self, select_k: int = 5):
        self.select_k = int(select_k)

    def rerank(self, query: str, candidates: List[Dict[str, Any]], *, select_k: Optional[int] = None) -> List[Dict[str, Any]]:
        rows = sorted(candidates, key=lambda x: float(x.get("score") or 0.0), reverse=True)
        out = []
        for rank, item in enumerate(rows[: int(select_k or self.select_k)], start=1):
            copied = dict(item)
            copied["rank"] = rank
            out.append(copied)
        return out
