"""Recover a decision from the two fictional sessions bundled with this example."""
import argparse
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from capture import RolloutTurnAssembler
from ranking import rrf_fuse, token_overlap, tokenize_query

ROOT = Path(__file__).resolve().parent
EARLIER = Path("examples/01-print-shop.jsonl")
LATER = Path("examples/02-back-at-the-bench.jsonl")
STOP_WORDS = set("a an and are as at be by did do for how i in is it of on or "
                 "should so that the to we what why with".split())


@dataclass(frozen=True)
class Passage:
    path: Path
    final_line: int
    message_id: str
    prompt: str
    outcome: str


def capture(path, root=ROOT):
    assembler = RolloutTurnAssembler(path.stem)
    passages = []
    with (root / path).open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            count = len(assembler.turns)
            assembler.feed(json.loads(line))
            if len(assembler.turns) > count:
                turn = assembler.turns[-1]
                passages.append(Passage(path, number, turn.turn_id,
                                        "\n".join(turn.prompt_parts), turn.visible_outcome))
    return passages


def recall(passages, question):
    terms = set(tokenize_query(question)) - STOP_WORDS
    if not terms or not passages:
        return None

    # Each index row points back to an immutable passage in this replay.
    with closing(sqlite3.connect(":memory:")) as db:
        db.execute("CREATE VIRTUAL TABLE memory USING fts5(prompt, outcome, tokenize='porter')")
        db.executemany("INSERT INTO memory(rowid, prompt, outcome) VALUES (?, ?, ?)",
                       ((i, p.prompt, p.outcome) for i, p in enumerate(passages, 1)))
        query = " OR ".join(f'"{term}"' for term in sorted(terms))
        hits = db.execute("SELECT rowid FROM memory WHERE memory MATCH ? "
                          "ORDER BY bm25(memory), rowid", (query,))
        text_ranks = {row_id: rank for rank, (row_id,) in enumerate(hits, 1)}

    scores = [(i, token_overlap(terms, set(tokenize_query(p.outcome))))
              for i, p in enumerate(passages, 1)]
    ranked = sorted(((i, score) for i, score in scores if score > 0),
                    key=lambda pair: (-pair[1], pair[0]))
    outcome_ranks = {row_id: rank for rank, (row_id, _) in enumerate(ranked, 1)}
    fused = rrf_fuse(outcome_ranks, text_ranks, absent_rank=len(passages) + 1)
    return passages[fused[0][0] - 1] if fused else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ask", help="Search the earlier session with your own question.")
    args = parser.parse_args()
    earlier = capture(EARLIER)
    question = capture(LATER)[0].prompt if args.ask is None else args.ask
    print(f"Question\n{question}\n")
    result = recall(earlier, question)
    if result is None:
        print("No matching passage in the earlier session.")
    else:
        print(f"Closest earlier passage\n{result.outcome}\n")
        print(f"Source\n{result.path.as_posix()}:{result.final_line} (prompt ID {result.message_id})")


if __name__ == "__main__":
    main()
