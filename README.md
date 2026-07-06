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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
