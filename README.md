# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## ✨ Features

- **Multi-pet task tracking** — one `Owner` manages any number of `Pet`s, each with its own list of care tasks (walks, feeding, meds, grooming, enrichment, etc.).
- **Sorting by time** — `Scheduler.sort_by_time()` merges every pet's due tasks into one chronological daily plan, regardless of the order tasks were added in.
- **Filtering** — `Scheduler.filter_tasks()` narrows the task list by pet name and/or completion status (e.g. "just Kumo's tasks" or "just what's still pending").
- **Conflict detection & warnings** — `Scheduler.find_conflicts()` groups same-time tasks (same pet or different pets), and `conflict_warnings()` turns each group into a readable `⚠️ Conflict at HH:MM: ...` message instead of crashing or silently double-booking.
- **Pre-add conflict check** — `Scheduler.tasks_at_time()` checks a candidate time *before* a task is created, so the UI can prompt the user for a different time instead of creating the conflict at all.
- **Daily & weekly recurrence** — `Task.mark_complete()` auto-generates the task's next occurrence via `Task.next_occurrence()`: `+1 day` for `DAILY`, `+1 week` for `WEEKLY` (respecting specific weekdays via `recurs_on`), and registers it on the same pet automatically.
- **Plan explanations** — `Scheduler.explain()` attaches a short human-readable reason (e.g. "Scheduled at 08:00 (daily)") to every entry in the generated `DailyPlan`.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Today's Schedule
========================================
Daily plan for Camila — 2026-07-05:
  08:00 — Morning walk (Kumo)
  08:30 — Feeding (Whiskers)
  12:00 — Litter box cleaning (Whiskers)
  18:00 — Evening walk (Kumo)

```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest tests/test_pawpal.py -v

# Run with coverage:
pytest --cov
```

`tests/test_pawpal.py` covers the core scheduling behaviors:

- **Task completion** — marking a task complete flips its `completed` status.
- **Pet task management** — adding a task to a `Pet` updates its task list.
- **Sorting correctness** — `Scheduler.sort_by_time()` returns tasks added out of order (18:00, 08:00, 12:30) back in chronological order.
- **Recurrence logic** — completing a `DAILY` task auto-creates the next occurrence due exactly one day later, still incomplete, and registered on the same pet.
- **Conflict detection** — `Scheduler.build_schedule()` flags two different pets' tasks scheduled at the same time as a conflict group.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.0, pytest-9.0.3, pluggy-1.6.0 -- /Library/Frameworks/Python.framework/Versions/3.13/bin/python3
cachedir: .pytest_cache
rootdir: /Users/camila/Desktop/CodePath/ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collecting ... collected 5 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [ 20%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [ 40%]
tests/test_pawpal.py::test_sort_by_time_returns_chronological_order PASSED [ 60%]
tests/test_pawpal.py::test_mark_complete_daily_task_creates_next_day_task PASSED [ 80%]
tests/test_pawpal.py::test_build_schedule_flags_duplicate_times_as_conflict PASSED [100%]

============================== 5 passed in 0.01s ===============================
```

**Confidence Level:** ⭐⭐⭐☆☆ (3/5)

All 5 tests pass and the core behaviors — sorting, daily recurrence, and same-time conflict detection — are verified. Confidence isn't higher yet because several edge cases still lack coverage: `WEEKLY` tasks with specific `recurs_on` weekdays, `is_due()` boundary conditions (exactly on `due_date`, already-completed tasks), `filter_tasks()` with no matches, and conflicts involving the same pet at the same time.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Sorts `(pet, task)` pairs chronologically with `sorted(..., key=lambda pair: pair[1].time)`. `time` is a zero-padded `"HH:MM"` string, so plain string comparison already matches chronological order — O(n log n), stable. |
| Filtering | `Scheduler.filter_tasks()` | Filters `(pet, task)` pairs by optional `pet_name` and/or `completed` status (combined with AND when both are given) — e.g. "just Kumo's tasks" or "just what's still pending." |
| Conflict handling | `Scheduler.find_conflicts()`, `Scheduler.conflict_warnings()`, `Scheduler.tasks_at_time()` | `find_conflicts()` buckets scheduled tasks by exact `time` match (O(n)) and returns any group of 2+ tasks sharing a slot, whether it's the same pet or different pets. `conflict_warnings()` turns those groups into readable `⚠️ Conflict at HH:MM: ...` messages — a conflict is reported, never raised, so it can't crash the app. `tasks_at_time()` runs the same check *before* a task is added (used by the "Add task" button in `app.py`), so the user is prompted to pick a different time instead of the conflict being created at all. Note: conflicts are detected by exact time match only, not overlapping durations — see `reflection.md` §2b for that tradeoff. |
| Recurring tasks | `Task.is_due()`, `Task.next_occurrence()`, `Task.mark_complete()` | Each `Task` has a `frequency` (`ONCE`/`DAILY`/`WEEKLY`) and a `due_date`. `is_due(on_date)` decides whether a task belongs on a given day's plan, respecting `recurs_on` (specific weekdays) for `WEEKLY` tasks. Marking a `DAILY`/`WEEKLY` task complete via `mark_complete()` automatically calls `next_occurrence()`, which uses `datetime.timedelta` to compute the next due date (+1 day for `DAILY`, +1 week for `WEEKLY`) and registers the new instance on the same pet — no manual step needed. |

## 📸 Demo Walkthrough

### Streamlit UI

`app.py` exposes four main actions:

- **Add a pet** — enter a name and species, click "Add pet." Pets show up in a table below (backed by `Owner.get_pets()`).
- **Schedule a task** — pick a pet, description, time, and frequency (`ONCE`/`DAILY`/`WEEKLY`), then click "Add task." Before the task is created, `Scheduler.tasks_at_time()` checks for a same-time clash and warns the user to pick a different time instead of silently creating a conflict.
- **Browse current tasks** — filter the full task list by pet and/or completion status (`filter_tasks()`), always shown in chronological order (`sort_by_time()`).
- **Generate today's schedule** — click "Generate schedule" to build the merged `DailyPlan` across every pet for the current date; any remaining same-time conflicts are flagged inline with `⚠️`.

### Example workflow

1. Add owner "Camila," then add two pets: **Kumo** (dog) and **Whiskers** (cat).
2. Schedule tasks: Kumo's "Morning walk" at 08:00 (daily), Whiskers' "Feeding" at 08:30 (daily), Whiskers' "Litter box cleaning" at 12:00 (weekly) — and, deliberately, Whiskers' "Morning cuddles" also at 08:00 (daily).
3. Click "Generate schedule." The `Scheduler` pulls every due task across both pets, sorts them by time, and flags the 08:00 double-booking as a conflict rather than silently listing both back to back.
4. Mark a task complete. If it's `DAILY` or `WEEKLY`, PawPal+ automatically creates the next occurrence (tomorrow, or next week) so it reappears on the next relevant day with no manual re-entry.

### Key Scheduler behaviors shown

- **Sorting** — tasks always render in chronological order, regardless of the order they were added in.
- **Filtering** — the task table can be narrowed to one pet and/or pending-only tasks.
- **Conflict warnings** — same-time tasks (same pet or across different pets) produce a `⚠️ Conflict at HH:MM: ...` warning instead of a crash or a silently double-booked slot.
- **Recurrence** — completing a `DAILY`/`WEEKLY` task advances it to its next due date automatically via `next_occurrence()`.

### Sample CLI output (`python main.py`)

`main.py` exercises the same backend classes from the command line — useful for seeing the raw `Scheduler` behaviors without the UI:

```
Tasks as added (unsorted):
  18:00 — Evening walk (Kumo, pending)
  08:00 — Morning walk (Kumo, pending)
  12:00 — Litter box cleaning (Whiskers, pending)
  10:00 — Vet checkup (Whiskers, done)
  08:30 — Feeding (Whiskers, pending)
  08:00 — Morning cuddles (Whiskers, pending)

Sorted by time:
  08:00 — Morning walk (Kumo, pending)
  08:00 — Morning cuddles (Whiskers, pending)
  08:30 — Feeding (Whiskers, pending)
  10:00 — Vet checkup (Whiskers, done)
  12:00 — Litter box cleaning (Whiskers, pending)
  18:00 — Evening walk (Kumo, pending)

Filtered to Kumo's tasks:
  18:00 — Evening walk (Kumo, pending)
  08:00 — Morning walk (Kumo, pending)

Filtered to incomplete tasks:
  18:00 — Evening walk (Kumo, pending)
  08:00 — Morning walk (Kumo, pending)
  12:00 — Litter box cleaning (Whiskers, pending)
  08:30 — Feeding (Whiskers, pending)
  08:00 — Morning cuddles (Whiskers, pending)

Today's Schedule
========================================
Daily plan for Camila — 2026-07-05:
  08:00 — Morning walk (Kumo)
  08:00 — Morning cuddles (Whiskers)
  08:30 — Feeding (Whiskers)
  12:00 — Litter box cleaning (Whiskers)
  18:00 — Evening walk (Kumo)
Conflicts:
  08:00: Kumo's 'Morning walk', Whiskers's 'Morning cuddles'

Conflict warnings:
  ⚠️ Conflict at 08:00: Kumo's 'Morning walk', Whiskers's 'Morning cuddles'
```

Note the completed "Vet checkup" (`ONCE`, already done) is excluded from "Today's Schedule" — `Task.is_due()` skips completed tasks — but still appears in the earlier "unsorted"/"incomplete filter" listings, which read directly from `Owner.get_all_tasks()`.
