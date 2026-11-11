# Second Brain

Second Brain began with a question that comes up when you return to a coding project: *Why did we decide to do it this way?* The code shows what changed. The reasoning might be three sessions back, in a message about an alternative someone tried and ruled out.

That problem grew beyond session history. A decision in one project can help with another, even when nobody thinks to search for it. Second Brain is a personal memory system for that work. It captures material from coding sessions, conversations, documents, and reading, keeps the source behind each memory, and gives you two ways back to it. You can ask a question and inspect the passages it retrieves. Or a briefing can bring you a connection, show the evidence on both sides, and suggest something to try.

This repository includes a runnable slice of the project. Two fictional coding sessions let you follow one decision from its original conversation to a later search result. The replay runs offline. The wider system also uses configured model providers for embeddings and reasoning.

## How a memory becomes useful

- **Capture and distillation.** Source adapters handle material such as Codex and Kiro sessions, Slack conversations, Outlook mail and calendar events, and bookmarked pages. For a Codex turn, the capture code pairs authored prompts with the visible final response. Where appropriate, a separate step extracts durable claims such as decisions and corrections. The stored source and its revision let a reader trace a claim back to the conversation.
- **Recall.** The full system stores memories and their relationships in PostgreSQL with pgvector. It searches by words and by meaning, combines and reranks the results, and makes retrieval available to agents through the Model Context Protocol (MCP). A source citation lets the reader check what was said, who said it, and whether it answers today's question.
- **Discovery.** A scheduled process skims incoming material. A read-only explorer gathers evidence, and a reasoning step proposes connections across projects. A grounding check compares a proposal with its sources. Four reviewers consider it, with three accepts required. Separate checks on the source revisions, proposed relationships, and permitted changes govern what can be written.
- **Delivery and feedback.** Accepted material can appear in a digest or briefing alongside questions and resurfaced work. A person can respond to a suggestion. The question for evaluation is what happened afterward: did someone use the connection, change a decision, or run a more useful test?

## A connection across projects

Consider two **fictional** pieces of evidence. In the print shop, a developer chooses to reuse a print job ID after a lost acknowledgment. In a separate ticket dispenser project, restarting the device erased the only record of which tickets came out. [Print-shop decision](examples/01-print-shop.jsonl#L5) · [Dispenser observation](examples/02-back-at-the-bench.jsonl#L3)

A briefing might suggest carrying the same request ID through a dispenser retry. The detail that changes the design is the restart: the dispenser also needs a durable way to tell that the physical action finished. A next experiment would be to interrupt power after a ticket comes out but before acknowledgment, replay the request, and count the tickets. This illustrates the kind of proposal discovery is designed to produce. The small replay below exercises recall. The dispenser experiment is open.

## Try the two-session replay

From this directory, run the following command with Python 3.9 or later and SQLite FTS5. It uses the Python standard library, reads the bundled examples, and builds an index in memory.

```sh
python3 -B demo.py
```

```text
Question
Why did we reuse the print job ID on retry, and what should we test next?

Closest earlier passage
The original print job ID lets the printer recognize a retry after a lost acknowledgment. A fresh ID makes the same label look like a new job. Next, drop the acknowledgment after printing and check that replay produces exactly one label.

Source
examples/01-print-shop.jsonl:6 (prompt ID message-retry)
```

The first session records two different contributions. The developer explicitly chooses the retry policy on line 5. The assistant explains the rationale and proposes the one-label test on line 6. The clock-based idea on line 4 appeared only in assistant commentary and stays out of the index. The return session supplies the question. [Developer's choice](examples/01-print-shop.jsonl#L5) · [Assistant's rationale and test](examples/01-print-shop.jsonl#L6) · [Return question](examples/02-back-at-the-bench.jsonl#L1)

Try three searches to see how to read a result:

```sh
python3 -B demo.py --ask "Where should the fold mark go?"
python3 -B demo.py --ask "clock"
python3 -B demo.py --ask "Which ink supplier did we choose?"
```

The first retrieves the fold-mark advice on line 2. The second finds no matching passage. The third retrieves the ink reminder on line 8. The word *ink* matches, but the session never names a supplier. The citation is accurate even when the passage leaves the question unanswered.

The replay indexes only the earlier session's three completed turns. SQLite full-text search ranks prompts and outcomes. A second ranking measures term overlap with each outcome, allowing prefix matches. Reciprocal rank fusion combines those lists and the program prints the highest-ranked passage verbatim. It reuses the project's turn assembler and ranking functions. The full system's vector search and discovery process are outside this executable example.

Run the regression tests with `python3 -B -m unittest -v`. They check the source of the decision, the exact cited passage, retrieval of another turn, and the exclusion of commentary and later-session material.

## Files

| File | Purpose |
|---|---|
| [README.md](README.md) | Project overview and walkthrough |
| [demo.py](demo.py) | Replays the two sessions and searches earlier turns |
| [capture.py](capture.py) | Assembles Codex-style events into turns with source identity |
| [ranking.py](ranking.py) | Tokenization, term overlap, and reciprocal rank fusion |
| [examples/01-print-shop.jsonl](examples/01-print-shop.jsonl) | Earlier print-shop conversation, including the developer's decision |
| [examples/02-back-at-the-bench.jsonl](examples/02-back-at-the-bench.jsonl) | Return question and a separate fictional dispenser observation |
| [test_demo.py](test_demo.py) | Checks retrieval, source attribution, and capture boundaries |
