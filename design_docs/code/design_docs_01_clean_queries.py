#!/usr/bin/env python3
"""EndoBench retrieval_export -> 清洗后的标准 query 集（用于评测 / RL 环境）。

输入：retrieval_export.jsonl（每行 = {sample, adaptive_fusion, retrieval}）
    - 全量在另一台机器：/mnt/data_10/.../retrieval_export.jsonl（6832 行, 117M）
    - 本项目样本：rerank_repo/重排序/data/persistent/retrieval_export.sample.jsonl（3 行）
输出：每行一个规范化 query 记录（见 clean_record），外加 sidecar 统计 json。

做的事：字段抽取 -> 校验（答案在选项内 / 选项非空 / 题干非空）-> 去重（题干+选项集）
        -> 派生（query_text、路由、候选池统计、分层键）-> 流式落盘。

三件套：
  时间统计：总耗时 + 每 N 条 ETA
  流式落盘：tmp 文件 + os.replace 原子替换 + 每 N 条 flush
  断点续传：--resume 时读已有输出的 qid 集合，跳过

注意（数据缺口，见 README 报告）：
  - export 的 sample 里没有【查询图路径】。RL 需要 I_q，必须从 EndoBench 源按
    (dataset, index) 回连补进来。本脚本把 query_image_path 置 null 并计数，供后续 join。
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter

SAMPLE_DEFAULT = (
    "/mnt/workspace/yds/论文撰写/rerank_repo/重排序/data/persistent/"
    "retrieval_export.sample.jsonl"
)


def norm_text(s):
    """归一化用于去重：去空白、统一标点、小写。"""
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[，,。.？?！!、；;：:（）()\[\]【】\"'`]", "", s)
    return s


def dedup_key(question, options):
    opts = "|".join(sorted(norm_text(v) for v in options.values()))
    return norm_text(question) + "##" + opts


def stable_qid(dataset, index, question):
    raw = f"{dataset}::{index}::{norm_text(question)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def flatten_query_text(question, options):
    """题干 + 选项拼成检索/生成用的 query 串（与 ppr debug 里的格式一致）。"""
    opt_str = "，".join(options[k] for k in sorted(options))
    return f"{question} {opt_str}".strip()


def compact_candidates(retrieval, keep=20):
    """候选池压缩存档（供 RL 环境复用初排池），只留必要字段。"""
    out = []
    for src in ("text_top20", "image_top20"):
        modality = "text" if src == "text_top20" else "image"
        for c in retrieval.get(src, [])[:keep]:
            out.append({
                "modality": modality,
                "rank": c.get("rank"),
                "raw_score": c.get("raw_score"),
                "weighted_score": c.get("weighted_score"),
                "doc_id": c.get("doc_id"),
                "level1": c.get("level1"),   # 部位
                "level2": c.get("level2"),   # 知识类型
                "image_id": c.get("image_id"),
                "image_path": c.get("image_path"),
                "text": (c.get("text") or "")[:300],
            })
    return out


def clean_record(row, keep_pool):
    s = row.get("sample", {})
    question = (s.get("question") or "").strip()
    options = s.get("options") or {}
    answer = s.get("answer")

    # ---- 校验 ----
    if not question:
        return None, "empty_question"
    if not isinstance(options, dict) or len(options) < 2:
        return None, "bad_options"
    if any(not str(v).strip() for v in options.values()):
        return None, "empty_option"
    if answer not in options:
        return None, "answer_not_in_options"

    af = row.get("adaptive_fusion", {}) or {}
    r = row.get("retrieval", {}) or {}
    n_text = len(r.get("text_top20", []))
    n_img = len(r.get("image_top20", []))

    rec = {
        "qid": stable_qid(s.get("dataset"), s.get("index"), question),
        "dataset": s.get("dataset"),
        "scene": s.get("scene"),
        "category": s.get("category"),
        "task": s.get("task"),
        "subtask": s.get("subtask"),
        "question": question,
        "options": {k: str(v).strip() for k, v in options.items()},
        "answer": answer,
        "answer_text": str(options[answer]).strip(),
        "query_text": flatten_query_text(question, options),
        # 查询图：export 里缺，置 null 待回连
        "query_image_path": s.get("image_path") or s.get("image") or None,
        "routing": {
            "density_level": af.get("density_level"),
            "image_dependency_level": af.get("image_dependency_level"),
            "text_retrieval_enabled": af.get("text_retrieval_enabled"),
            "fusion_weights": af.get("fusion_weights"),
        },
        "pool_stats": {"n_text_cand": n_text, "n_image_cand": n_img},
        # 分层键：题型 + 图依赖，用于 train/test 分层或按题型汇报
        "stratify_key": f"{s.get('category')}|{s.get('task')}|"
                        f"{af.get('image_dependency_level')}",
    }
    if keep_pool:
        rec["candidate_pool"] = compact_candidates(r)
    return rec, None


def load_done_qids(path):
    done = set()
    if not os.path.exists(path):
        return done
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                done.add(json.loads(line)["qid"])
            except Exception:
                continue
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=SAMPLE_DEFAULT)
    ap.add_argument("--output",
                    default="/mnt/workspace/yds/论文撰写/design_docs/data/tmp/"
                            "clean_queries.jsonl")
    ap.add_argument("--keep-pool", action="store_true",
                    help="存档压缩后的候选池（供 RL 环境复用初排池）")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--log-every", type=int, default=500)
    args = ap.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"[FATAL] 输入不存在: {args.input}\n"
                 f"        全量在另一台机器(见 input_manifest.json)，"
                 f"请挂载 /mnt/data_10 或把 retrieval_export.jsonl 拷进项目。")

    t0 = time.time()
    done = load_done_qids(args.output) if args.resume else set()
    mode = "a" if (args.resume and done) else "w"
    tmp = args.output + ".tmp"

    # resume：先把已有输出拷到 tmp，再续写；非 resume 直接新写 tmp
    if mode == "a":
        os.replace(args.output, tmp) if os.path.exists(args.output) else None
    fout = open(tmp, mode, encoding="utf-8")

    seen_dedup, n_in, n_out = set(), 0, 0
    reasons = Counter()
    stat = {"category": Counter(), "task": Counter(),
            "density": Counter(), "image_dep": Counter(),
            "has_query_image": Counter()}

    with open(args.input, encoding="utf-8") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            n_in += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                reasons["json_error"] += 1
                continue

            rec, err = clean_record(row, args.keep_pool)
            if err:
                reasons[err] += 1
                continue
            if rec["qid"] in done:
                continue
            dk = dedup_key(rec["question"], rec["options"])
            if dk in seen_dedup:
                reasons["duplicate"] += 1
                continue
            seen_dedup.add(dk)

            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_out += 1
            stat["category"][rec["category"]] += 1
            stat["task"][rec["task"]] += 1
            stat["density"][rec["routing"]["density_level"]] += 1
            stat["image_dep"][rec["routing"]["image_dependency_level"]] += 1
            stat["has_query_image"][bool(rec["query_image_path"])] += 1

            if n_out % args.log_every == 0:
                fout.flush()
                os.fsync(fout.fileno())
                el = time.time() - t0
                print(f"  [{n_out}] in={n_in} 用时{el:.1f}s "
                      f"速率{n_out/el:.0f}/s", flush=True)

    fout.flush()
    os.fsync(fout.fileno())
    fout.close()
    os.replace(tmp, args.output)

    sidecar = args.output.replace(".jsonl", ".stats.json")
    stats = {
        "input": args.input, "output": args.output,
        "n_in": n_in, "n_out": n_out,
        "dropped": dict(reasons),
        "by_category": dict(stat["category"]),
        "by_task": dict(stat["task"]),
        "by_density": dict(stat["density"]),
        "by_image_dependency": dict(stat["image_dep"]),
        "has_query_image": {str(k): v for k, v in stat["has_query_image"].items()},
        "elapsed_sec": round(time.time() - t0, 2),
    }
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] in={n_in} -> out={n_out}  丢弃={dict(reasons)}")
    print(f"     输出: {args.output}")
    print(f"     统计: {sidecar}")
    print(f"     总耗时 {time.time()-t0:.2f}s")
    if stat["has_query_image"].get(False, 0):
        print(f"[WARN] {stat['has_query_image'][False]} 条无查询图路径 "
              f"—— RL 需 I_q，须从 EndoBench 源按 (dataset,index) 回连补齐。")


if __name__ == "__main__":
    main()
