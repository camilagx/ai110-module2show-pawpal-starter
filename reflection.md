# PawPal+ Project Reflection

## 1. System Design

### Core actions
- add pets and info
- add/edit tasks 
- create a schedule plan

**a. Initial design**

My initial UML (see `diagrams/uml.mmd`) has 9 classes, split between data-holders, enums, and the logic that acts on them:

- **`Owner`** — the pet owner. Holds their name, daily time budget (`available_minutes_per_day`), preferred start time, and a preferences dict (e.g. "no walks after dark"). Responsible for owning the list of `Pet`s it cares for.
- **`Pet`** — basic info about one animal (name, species, breed, age) plus a reference back to its `Owner`. Responsible for owning the list of `CareTask`s that apply to it.
- **`CareTask`** — a single task that needs to happen (title, category, duration, priority, optional fixed time, recurrence). Purely a data holder — it doesn't know how or when it gets scheduled.
- **`Priority`, `TaskCategory`, `Recurrence`** — three enums that constrain `CareTask` fields to valid values (e.g. priority can only be LOW/MEDIUM/HIGH) instead of free-form strings.
- **`Scheduler`** — the stateless logic engine. Responsible for taking a pet's tasks and constraints and producing a `DailyPlan`: sorting by priority/duration, filtering out tasks that don't fit in the available time, resolving conflicts between fixed-time tasks, and explaining each placement.
- **`ScheduledTask`** — a `CareTask` once the `Scheduler` has assigned it a start/end time and a reason, so the plan can explain itself.
- **`DailyPlan`** — the final output for one pet on one day: the list of `ScheduledTask`s that made the cut, the list of tasks that got skipped (with reasons), and a summary for display in the UI.

The core idea behind the split is separating **data** (`Owner`, `Pet`, `CareTask`, `ScheduledTask`, `DailyPlan`) from **behavior** (`Scheduler`) — the data classes don't contain scheduling logic themselves, so the scheduling algorithm can change without touching how tasks/pets/owners are represented.

**b. Design changes**

Yes — while turning the UML into `pawpal_system.py` class stubs, a self/AI review of the skeleton surfaced a few issues that would have caused real bugs once scheduling logic was added, so I fixed them before moving on:

- **`Priority` became an `IntEnum` instead of a plain `Enum`.** A plain `Enum`'s members aren't orderable — `Priority.HIGH > Priority.MEDIUM` raises `TypeError`, which would break `sort_tasks` the moment it tries to sort by priority. `IntEnum` (`LOW=1, MEDIUM=2, HIGH=3`) makes priorities directly comparable and sortable.
- **`Owner`/`Pet` are now wired automatically instead of manually.** Originally, creating `Pet(..., owner=owner)` did *not* add the pet to `owner.pets` — you had to separately remember to call `owner.add_pet(pet)`. Forgetting that step would silently leave `owner.get_pets()` incomplete. Now `Pet.__init__` calls `owner.add_pet(self)` itself, and `Owner.add_pet` is idempotent and bidirectional, so the relationship can't drift out of sync.
- **Added `CareTask.recurs_on` (list of weekdays).** `Recurrence.WEEKLY` originally had no way to say *which* day(s) of the week a task repeats on, so the scheduler would have no way to decide whether a weekly task applies on a given date. Added `recurs_on: list[int]` (0=Monday...6=Sunday) to close that gap.
- **Simplified `Scheduler.build_schedule`'s signature** from `build_schedule(pet, available_minutes, day_start)` to `build_schedule(pet, date)`. The old version took `available_minutes`/`day_start` as separate arguments even though `Owner` already stores `available_minutes_per_day`/`preferred_start_time` — two sources of truth that could disagree if a caller passed different values than what was on the owner. Now the scheduler always reads time budget/start time from `pet.owner`.

I deliberately left some other rough edges alone for now (e.g. task times are still plain `"HH:MM"` strings, and `CareTask.id` still has to be supplied by the caller rather than auto-generated) since they don't cause incorrect behavior yet — those are more "nice to have before writing the real scheduling algorithm" than "will break the app."

A second, bigger change came when I fleshed out the stubs into real logic: the project spec for this step described a leaner 4-class model (`Task`, `Pet`, `Owner`, `Scheduler`) than what I'd originally designed, so I simplified to match it rather than keep both models in parallel:

- **`CareTask` → `Task`, with fields cut down to `description`, `time`, `frequency`, `completed`.** Dropped `Priority`, `TaskCategory`, `duration_minutes`, `fixed_time`, and `recurs_on` — the simplified spec only calls for description/time/frequency/completion-status, and duration-based time-budget math wasn't part of it. `Recurrence` was renamed `Frequency` (`ONCE`/`DAILY`/`WEEKLY`, `NONE` → `ONCE` since a task now has an explicit `completed` flag it makes more sense to describe a non-repeating task as happening "once").
- **`Owner` dropped `available_minutes_per_day`/`preferred_start_time`.** Those existed to support duration-based scheduling, which no longer applies once `Task` has no duration field — keeping unused attributes around would've been misleading.
- **`Scheduler.build_schedule` changed from per-pet (`build_schedule(pet, date)`) to per-owner (`build_schedule(owner, date)`), merging every pet's due tasks into one shared `DailyPlan`.** The spec describes the Scheduler as managing tasks "across pets," which a single-pet method couldn't do. `ScheduledTask` now carries a `pet` reference so a merged plan can still show which pet each task belongs to, and without a priority field to break ties, same-time conflicts across pets are now surfaced in `DailyPlan.conflicts` rather than auto-resolved.

I verified this version by hand: built an owner with two pets, gave one pet two tasks at the same time and the other pet a completed one-off task, and confirmed `build_schedule` excluded the completed `ONCE` task and correctly flagged the `08:00` collision between the two same-pet tasks.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
