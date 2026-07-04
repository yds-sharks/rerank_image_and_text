#!/usr/bin/env python3
"""源锚定合成 MCQ：从语料库造 agent 训练用 query，带视觉同质硬负例挖掘。

核心原则（务必守住）：
  正确答案来自语料【真值标签】(level1 部位 / level2 类型)，不由模型判断。
  API（强 VLM）只负责把题干【措辞】自然化，并被约束"答案须能从图+描述推出"。
  → 合成 MCQ 的正确答案是保证正确的，模型只可能把题干写歪（抽样审核即可）。

两套模板：
  A  部位识别：Q=图中是哪个部位？correct=level1，干扰项=其它 level1。
  B  病理判别（★P2 硬负例印钞机）：固定同一 level1（同部位），correct=源项 level2，
     干扰项=【同 level1、不同 level2】→ "视觉像但临床不同"，正是论文要解决的硬 case。
  优先出 B；同部位备选不足时回退 A。

输入语料 jsonl，每行需含：
  {image_id, image_path, text, level1, level2, doc_id}
  （全量语料在 multimodal_samples.db / retrieval_export，本机不可达；
    --corpus 也可直接喂 clean_queries.jsonl 的候选池导出，见 --from-pool）

三件套：时间统计 + os.replace 原子写 + --resume（按 qid 跳过）。
API：OpenAI 兼容 / dashscope，--dry-run 时不调 API（用模板措辞），可离线验证逻辑。
usage：每条输出内嵌 api_usage（prompt/completion/total tokens），符合项目规矩。
"""
import argparse
import hashlib
import json
import os
import random
import sys
import time
from collections import defaultdict, Counter

HARD_NEG_RATIO_DEFAULT = 0.4  # B 模板（硬负例）目标占比


def qid_of(*parts):
    return hashlib.sha1("::".join(map(str, parts)).encode()).hexdigest()[:16]


def load_corpus(path, from_pool):
    """读语料。from_pool：输入是 clean_queries.jsonl，抽 candidate_pool 当语料。"""
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            if from_pool:
                for c in o.get("candidate_pool", []):
                    if c.get("modality") != "image":
                        continue
                    if not (c.get("level1") and c.get("image_path")):
                        continue
                    items.append({
                        "image_id": c.get("image_id"),
                        "image_path": c.get("image_path"),
                        "text": c.get("text", ""),
                        "level1": c.get("level1"),
                        "level2": c.get("level2"),
                        "doc_id": c.get("doc_id"),
                    })
            else:
                if o.get("level1") and o.get("image_path"):
                    items.append(o)
    # 去重（同 image_id 只留一次）
    seen, uniq = set(), []
    for it in items:
        k = it.get("image_id") or it.get("image_path")
        if k in seen:
            continue
        seen.add(k)
        uniq.append(it)
    return uniq


def build_indices(corpus):
    by_l1 = defaultdict(list)                 # level1 -> items
    by_l1_l2 = defaultdict(lambda: defaultdict(list))  # level1 -> level2 -> items
    l2_by_l1 = defaultdict(set)               # level1 -> {level2}
    all_l1 = set()
    for it in corpus:
        l1, l2 = it["level1"], it.get("level2") or "未标注"
        by_l1[l1].append(it)
        by_l1_l2[l1][l2].append(it)
        l2_by_l1[l1].add(l2)
        all_l1.add(l1)
    return by_l1, by_l1_l2, l2_by_l1, sorted(all_l1)


def make_template_B(src, l2_by_l1, by_l1_l2, rng, n_opt=4):
    """病理判别硬负例：同 level1、不同 level2 做干扰项。"""
    l1 = src["level1"]
    l2 = src.get("level2") or "未标注"
    others = [x for x in l2_by_l1[l1] if x != l2 and x != "未标注"]
    if len(others) < n_opt - 1:
        return None
    distract_l2 = rng.sample(others, n_opt - 1)
    correct = l2
    opts_texts = [correct] + distract_l2
    return {
        "template": "B_pathology_discrimination",
        "hard_negative": True,
        "level1": l1, "level2": l2,
        "correct_text": correct,
        "option_texts": opts_texts,
        "distractor_level2": distract_l2,
        "stem_hint": f"根据内镜图像，该「{l1}」部位所见最符合以下哪一项？",
    }


def make_template_A(src, all_l1, rng, n_opt=4):
    """部位识别：干扰项=其它部位。"""
    l1 = src["level1"]
    others = [x for x in all_l1 if x != l1]
    if len(others) < n_opt - 1:
        return None
    distract = rng.sample(others, n_opt - 1)
    opts_texts = [l1] + distract
    return {
        "template": "A_site_identification",
        "hard_negative": False,
        "level1": l1, "level2": src.get("level2"),
        "correct_text": l1,
        "option_texts": opts_texts,
        "distractor_level2": [],
        "stem_hint": "内镜图像中显示的是消化道的哪个部位？",
    }


def phrase_stem_via_api(client, model, spec, src):
    """用强 VLM 把题干措辞自然化；返回 (question, usage)。约束答案须可从图推出。"""
    sys_p = ("你是内镜医学出题专家。给定图像所见的真实标签，改写出一句自然、"
             "临床规范的单选题题干。只输出题干，不要输出选项/答案/解释。"
             "题干必须能仅凭图像(+简短描述)作答，不得泄露答案。")
    user_p = (f"部位: {spec['level1']}\n"
              f"病理/类型(真值): {spec.get('level2')}\n"
              f"图像描述: {src.get('text','')[:200]}\n"
              f"出题方向: {spec['stem_hint']}")
    resp = client.chat.completions.create(
        model=model, temperature=0.7,
        messages=[{"role": "system", "content": sys_p},
                  {"role": "user", "content": user_p}],
    )
    q = resp.choices[0].message.content.strip()
    u = resp.usage
    usage = {"prompt_tokens": u.prompt_tokens,
             "completion_tokens": u.completion_tokens,
             "total_tokens": u.total_tokens}
    return q, usage


def assemble(spec, src, question, usage, rng):
    letters = ["A", "B", "C", "D", "E", "F"][:len(spec["option_texts"])]
    order = spec["option_texts"][:]
    rng.shuffle(order)
    options = {letters[i]: order[i] for i in range(len(order))}
    answer = next(k for k, v in options.items() if v == spec["correct_text"])
    opt_str = "，".join(options[k] for k in letters)
    return {
        "qid": qid_of("synth", spec["template"], src.get("image_id"),
                      spec["correct_text"]),
        "source": "synthetic",
        "template": spec["template"],
        "hard_negative": spec["hard_negative"],
        "dataset": "synth_corpus",
        "category": ("Pathology Discrimination"
                     if spec["hard_negative"] else "Site Identification"),
        "question": question,
        "options": options,
        "answer": answer,
        "answer_text": spec["correct_text"],
        "query_text": f"{question} {opt_str}".strip(),
        "query_image_path": src.get("image_path"),
        "query_image_id": src.get("image_id"),
        "level1": spec["level1"],
        "level2": spec.get("level2"),
        "distractor_level2": spec.get("distractor_level2"),
        "api_usage": usage,
    }


def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["qid"])
                except Exception:
                    pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="语料 jsonl")
    ap.add_argument("--from-pool", action="store_true",
                    help="corpus 是 clean_queries.jsonl，从候选池抽语料")
    ap.add_argument("--output",
                    default="/mnt/workspace/yds/论文撰写/design_docs/data/tmp/"
                            "synth_mcq.jsonl")
    ap.add_argument("--n", type=int, default=1000, help="目标生成条数")
    ap.add_argument("--hard-ratio", type=float, default=HARD_NEG_RATIO_DEFAULT)
    ap.add_argument("--n-opt", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true",
                    help="不调 API，用模板措辞（离线验证逻辑）")
    ap.add_argument("--model", default="qwen-max")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--log-every", type=int, default=200)
    args = ap.parse_args()

    if not os.path.exists(args.corpus):
        sys.exit(f"[FATAL] 语料不存在: {args.corpus}\n"
                 f"        全量语料(multimodal_samples.db / retrieval_export)"
                 f"在另一台机器，请挂载或导出后再跑；或用 --from-pool 喂 "
                 f"clean_queries.jsonl 做小规模验证。")

    client = None
    if not args.dry_run:
        try:
            from openai import OpenAI
        except ImportError:
            sys.exit("[FATAL] 需要 openai 包，或用 --dry-run。")
        base = os.environ.get("OPENAI_BASE_URL") or os.environ.get(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1")
        key = os.environ.get("OPENAI_API_KEY") or os.environ.get(
            "DASHSCOPE_API_KEY")
        if not key:
            sys.exit("[FATAL] 未设置 API key（OPENAI_API_KEY/DASHSCOPE_API_KEY）")
        client = OpenAI(base_url=base, api_key=key)

    t0 = time.time()
    rng = random.Random(args.seed)
    corpus = load_corpus(args.corpus, args.from_pool)
    by_l1, by_l1_l2, l2_by_l1, all_l1 = build_indices(corpus)
    print(f"[语料] {len(corpus)} 项，部位 {len(all_l1)} 类：{all_l1[:8]}...")

    done = load_done(args.output) if args.resume else set()
    tmp = args.output + ".tmp"
    if args.resume and os.path.exists(args.output):
        os.replace(args.output, tmp)
        fout = open(tmp, "a", encoding="utf-8")
    else:
        fout = open(tmp, "w", encoding="utf-8")

    order = corpus[:]
    rng.shuffle(order)
    n_out = 0
    tally = Counter()
    total_usage = Counter()
    i = 0
    while n_out < args.n and i < len(order) * 3:
        src = order[i % len(order)]
        i += 1
        want_hard = rng.random() < args.hard_ratio
        spec = None
        if want_hard:
            spec = make_template_B(src, l2_by_l1, by_l1_l2, rng, args.n_opt)
        if spec is None:
            spec = make_template_A(src, all_l1, rng, args.n_opt)
        if spec is None:
            continue

        if args.dry_run:
            question, usage = spec["stem_hint"], {"prompt_tokens": 0,
                                                  "completion_tokens": 0,
                                                  "total_tokens": 0}
        else:
            try:
                question, usage = phrase_stem_via_api(
                    client, args.model, spec, src)
            except Exception as e:
                tally["api_error"] += 1
                continue

        rec = assemble(spec, src, question, usage, rng)
        if rec["qid"] in done:
            continue
        done.add(rec["qid"])
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_out += 1
        tally[spec["template"]] += 1
        for k, v in usage.items():
            total_usage[k] += v

        if n_out % args.log_every == 0:
            fout.flush()
            os.fsync(fout.fileno())
            el = time.time() - t0
            print(f"  [{n_out}/{args.n}] 用时{el:.1f}s "
                  f"tokens={total_usage['total_tokens']}", flush=True)

    fout.flush()
    os.fsync(fout.fileno())
    fout.close()
    os.replace(tmp, args.output)

    sidecar = args.output.replace(".jsonl", ".stats.json")
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump({
            "corpus": args.corpus, "n_corpus": len(corpus),
            "n_out": n_out, "by_template": dict(tally),
            "hard_ratio_actual":
                tally["B_pathology_discrimination"] / max(n_out, 1),
            "total_api_usage": dict(total_usage),
            "dry_run": args.dry_run, "model": args.model,
            "elapsed_sec": round(time.time() - t0, 2),
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] 生成 {n_out} 条  模板分布={dict(tally)}")
    print(f"     硬负例(B)占比 "
          f"{tally['B_pathology_discrimination']/max(n_out,1):.0%}")
    print(f"     API usage={dict(total_usage)}")
    print(f"     输出: {args.output}\n     统计: {sidecar}")
    print(f"     总耗时 {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
