"""Valutazione del prototipo: accordo con il giudizio umano e fughe di conoscenza del Sotto-studente.

    python eval/run_eval.py                # motore offline (gratis, regole)
    python eval/run_eval.py --mode live    # Claude: costa qualche decina di chiamate

Metriche (obiettivi da docs/TeachBack - Reply Clash 2026.md):
- accordo tra il nostro giudizio (explanations.jsonl) e quello dell'Insegnante, per concetto: obiettivo >= 80%
- prove in cui il Sotto-studente usa conoscenze non date: obiettivo 0
  (frase con citazione valida ma >50% di parole che non vengono né dalle affermazioni né dalla domanda)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("TEACHBACK_LOG_TO_FILE", "0")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from teachback import get_engine, guardrails  # noqa: E402

LEAK_THRESHOLD = 0.5


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["offline", "live"], default="offline")
    args = ap.parse_args()
    engine = get_engine(args.mode, persist=False)
    rows = [json.loads(line) for line in (ROOT / "eval" / "explanations.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

    agree = total = 0
    leaks = attempts = 0
    details = []
    for row in rows:
        s = engine.start_session("chimica-equilibrio", "le_chatelier", student_id=f"eval-{row['id']}")
        engine.submit_explanation(s, row["text"])
        exam = engine.substudent_try_exam(s)
        attempts += 1
        leaked = [x.text for x in exam.sentences
                  if guardrails.novelty_ratio(x.text, s.claims, s.hidden["exam"]["question"]) > LEAK_THRESHOLD]
        leaks += bool(leaked)
        rep = engine.teacher_report(s)
        got = {}
        for cid in row["labels"]:
            if cid in rep.explained:
                got[cid] = "spiegato"
            elif s.concept_status.get(cid) == "non_ancora":
                got[cid] = "errato"
            elif cid in rep.named_only:
                got[cid] = "nominato"
            else:
                got[cid] = "assente"
        for cid, want in row["labels"].items():
            total += 1
            agree += got[cid] == want
        details.append({"id": row["id"], "human": row["labels"], "model": got,
                        "exam_kind": exam.kind, "leaked_sentences": leaked})

    result = {
        "mode": args.mode, "explanations": len(rows),
        "judge_agreement": round(agree / total, 3) if total else None, "judgements": total,
        "leak_attempts": leaks, "attempts": attempts, "details": details,
    }
    out = ROOT / "eval" / f"results_{args.mode}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Motore: {args.mode}")
    print(f"Accordo con il giudizio umano: {agree}/{total} = {result['judge_agreement']:.0%} (obiettivo >= 80%)")
    print(f"Prove con fughe di conoscenza: {leaks}/{attempts} (obiettivo 0)")
    print(f"Dettagli: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
