# How to submit your model to the community leaderboard

> **Status: prototype.** Submissions open when announced (a human decision). This guide
> documents the flow so you can be ready on day one.

The community track is a **self-reported (honor system)** race on a **seasonal public exam
set**. You run your model locally (your compute, your cost), produce a small JSON, and open a
PR — the site ranks it per season. Verified, contamination-proof results are the **sealed
track** (signed certificates); this track is for fun, bragging rights, and honest signal.

## The 5-minute flow

1. **Get the season's exam set** (openly derived — everyone gets the same worlds):

   ```python
   from critter_gym.community import season_seeds, season_spec
   seeds = season_seeds(1, 16)   # season 1, 16 public held-out worlds
   spec = season_spec()          # the pinned benchmark config — do not change it
   ```

2. **Run your agent** on those seeds with the pinned spec and record the **mean gym-clears**
   (the community metric — RLVR-clean, bounded by `num_gyms`). For a scripted/learned policy,
   mirror `scripts/community_submit.py --demo` (it scores the free baseline end-to-end). For an
   **LLM agent**, see `docs/how-to/evaluate-an-llm-agent.md` and score the same seeds.

3. **Write the submission JSON** (copy `community/submissions/season1-scripted-baseline.json`
   and edit):

   ```json
   {
     "schema_version": 1,
     "season": 1,
     "model": "your-model-name",
     "submitter": "your-github-handle",
     "heldout_mean": 1.25,
     "n_worlds": 16,
     "spec": { "...": "output of season_spec() — verbatim" },
     "reproduce": "the one-line command that reproduces your number",
     "date": "YYYY-MM-DD",
     "self_reported": true
   }
   ```

4. **Validate locally** (the same check CI will run):

   ```bash
   python scripts/community_submit.py --validate your-file.json
   ```

5. **Open a PR** adding your file to `community/submissions/`. Once merged and the site is
   rebuilt, you're on the board.

## Rules (honor system)

- **Score only on the season's seeds** with the **pinned spec** — the validator rejects any
  other config.
- **`reproduce` is mandatory**: one command that regenerates your number. Others may run it.
- **`self_reported: true` is forced by the schema** — this track never pretends to be verified.
- Seasons rotate: a new season issues a fresh public block (procedural generation — the exam
  can always be re-issued), resetting the race and bounding the value of memorization.
- Want a **verified** result? That's the sealed track: a private, regenerable eval with a
  signed contamination-proof certificate (see `docs/reference/sealed-eval-packaging.md`).
