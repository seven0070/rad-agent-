"""The trainer socket — where weight evolution happens.

Rad does NOT reinvent training: it detects mature open-source backends
(MLX-LM on Apple Silicon, Unsloth/PEFT on GPUs) and drives them with a
corpus mined from Rad's own sessions.

No backend on this machine? No blocker — Rad exports the corpus with exact
ready-to-run commands for each backend. Train anywhere (your Mac, a rented
GPU), then bring the adapter back: `rad brain add --adapter` → it gets
benchmark-fought before it may become the brain.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.home import RadHome
from rad.ui import col, ok, warn


def detect_backends() -> Dict[str, str]:
    out: Dict[str, str] = {}
    if importlib.util.find_spec("mlx_lm") or shutil.which("mlx_lm"):
        out["mlx"] = "mlx_lm (Apple Silicon)"
    if importlib.util.find_spec("unsloth") or shutil.which("unsloth"):
        out["unsloth"] = "unsloth (GPU)"
    if importlib.util.find_spec("peft") and importlib.util.find_spec("transformers"):
        out["peft"] = "peft + transformers (GPU/CPU)"
    return out


def export_corpus(home: RadHome) -> str:
    from rad.corpus import Corpus
    path = home.root / "corpus" / "rad-train.jsonl"
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        import json
        for p in Corpus(home).mine():
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    return str(path)


def build_command(backend: str, corpus: str, model_ref: str, out_dir: str) -> Optional[List[str]]:
    if backend == "mlx":
        return ["mlx_lm.lora", "--model", model_ref, "--train", "--data", corpus,
                "--lora-alpha", "16", "--num-epochs", "1", "--batch-size", "4",
                "--adapter-path", out_dir]
    if backend == "unsloth":
        return [sys.executable, "-c",
                f"from unsloth import FastLanguageModel; "
                f"model, tokenizer = FastLanguageModel.from_name('{model_ref}'); "
                f"model = FastLanguageModel.get_peft_model(model, r=16, target_modules=['q_proj','k_proj','v_proj','o_proj']); "
                f"# load {corpus}, SFT, then model.save_adapter('{out_dir}')"]
    if backend == "peft":
        return [sys.executable, "-c",
                f"# peft+trl SFTTrainer on '{corpus}' → save LoRA to '{out_dir}' "
                f"(see rad README: Training with PEFT)"]
    return None


def plan(home: RadHome, model_ref: str = "edge0-35b", out_dir: str = "") -> str:
    backends = detect_backends()
    lines = [col.bold("Trainer backends on this machine:")]
    if backends:
        for k, v in backends.items():
            lines.append(f"  {col.green('●')} {v}")
    else:
        lines.append(f"  {col.dim('○ none detected — that is fine, see the export route below')}")

    lines.append("")
    lines.append(col.bold("Route A — train here (needs a backend):"))
    if backends:
        best = next(iter(backends))
        cmd = build_command(best, str(home.root / "corpus" / "rad-train.jsonl"), model_ref,
                            out_dir or str(home.root / "adapters"))
        lines.append(f"  $ {' '.join(cmd)}")
        lines.append(col.dim("  (rad train --run executes this; it's a long job)"))
    else:
        lines.append(col.dim("  — no backend available —"))

    lines.append("")
    lines.append(col.bold("Route B — train anywhere, bring the adapter back (no blocker):"))
    corpus = export_corpus(home)
    from rad.corpus import Corpus
    stats = Corpus(home).stats()
    statline = f"({stats['total']} pairs: {stats.get('praised', 0)} praised, {stats.get('correction', 0)} corrections)"
    lines.append(f"  corpus: {corpus}  {col.dim(statline)}")
    lines.append("  on your Mac (Edge0 brain):")
    lines.append("      pip install mlx-lm")
    lines.append("      mlx_lm.lora --model <edge0-model> --train --data " + corpus + " --adapter-path ./rad-adapter")
    lines.append("  on a rented GPU:")
    lines.append("      pip install unsloth   # or peft + trl")
    lines.append(f"      (SFT on {Path(corpus).name}, r=16 LoRA, save adapter)")
    lines.append("")
    lines.append("  then bring it home:")
    lines.append("      rad brain add trained-1 --provider edge0 --model <edge0-model> --adapter ./rad-adapter/adapter.pt")
    lines.append("      rad brain promote trained-1    # must WIN the benchmark battle to go live")
    return "\n".join(lines)


def run_training(home: RadHome, model_ref: str, out_dir: str, backend: str = "auto") -> int:
    backends = detect_backends()
    if backend == "auto":
        backend = next(iter(backends), None)
    if backend is None or backend not in backends:
        warn("no trainer backend on this machine — use Route B (see `rad train --plan`)")
        return 1
    cmd = build_command(backend, export_corpus(home), model_ref, out_dir)
    if not cmd:
        warn(f"no command for backend {backend}")
        return 1
    print(col.bold(f"  starting: {' '.join(cmd)}"))
    try:
        proc = subprocess.run(cmd, text=True)
        return proc.returncode
    except Exception as e:
        warn(f"training failed to start: {e}")
        return 1
