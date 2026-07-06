# PawPal+ Project Reflection

## 1. System Design

### Core actions
- add pets and info
- add/edit tasks 
- create a schedule plan

**a. Initial design**

My initial UML (`diagrams/uml.mmd`) had 9 classes. I split them into data holders, a few enums, and the one core class.

`Owner` holds the pet owner's info: name, how many minutes a day they have for pet care, a preferred start time, and a preferences dict for stuff like "no walks after dark." It owns the list of `Pet`s. `Pet` is basic info about one animal — name, species, breed, age — plus a pointer back to its `Owner`, and it owns that pet's `CareTask`s. `CareTask` is a single task: title, category, duration, priority, maybe a fixed time, and how often it repeats. It's just data, it has no idea how or when it gets scheduled. `Priority`, `TaskCategory`, and `Recurrence` are enums so those fields can't just be arbitrary strings.

`Scheduler` is the actual logic — it takes a pet's tasks and constraints and builds a `DailyPlan`: sorts by priority/duration, drops what doesn't fit in the available time, resolves conflicts between fixed-time tasks, and explains why it placed things where it did. `ScheduledTask` is a `CareTask` once the `Scheduler` has given it a start/end time and a reason. `DailyPlan` is the final output for one pet on one day — what made it in, what got skipped and why, and a summary for the UI.

The main idea was Thkeeping data and behavior apart. `Owner`/`Pet`/`CareTask`/`ScheduledTask`/`DailyPlan` don't contain any scheduling logic themselves, so I can change how `Scheduler` works without touching how anything is represented.

**b. Design changes**

Yes, a few things changed once I actually started turning the UML into class stubs in `pawpal_system.py`.

`Priority` had to become an `IntEnum` instead of a regular `Enum` — a plain `Enum` can't be compared, so `Priority.HIGH > Priority.MEDIUM` just throws a `TypeError`, which would've broken sorting the second I tried to sort by priority. `Owner`/`Pet` also used to need two separate steps: create the `Pet`, then remember to call `owner.add_pet(pet)` yourself. Forget the second part and `owner.get_pets()` is just quietly missing a pet. Now `Pet.__init__` calls `owner.add_pet(self)` on its own, so that can't happen. I also added `recurs_on` (a list of weekdays) to `CareTask`, since `WEEKLY` tasks had no way to say which day(s) they actually repeat on. And I simplified `build_schedule`'s signature — it used to take `available_minutes`/`day_start` as separate arguments even though `Owner` already stored that info, which meant two places could disagree about the same numbers. Now it just reads from `pet.owner`.

I left a couple of rough edges alone on purpose at this point — task times were still plain `"HH:MM"` strings, and ids weren't auto-generated yet — since neither was actually causing a bug, just things to clean up later.

Then there was a bigger change. The actual project spec described a leaner 4-class model (`Task`, `Pet`, `Owner`, `Scheduler`) than what I'd designed, so I cut things down to match instead of keeping both versions around. `CareTask` became `Task`, down to just `description`/`time`/`frequency`/`completed` — dropped `Priority`, `TaskCategory`, duration, and `recurs_on` entirely. `Recurrence` got renamed `Frequency`, and `NONE` became `ONCE`, which reads better now that a task has its own `completed` flag. `Owner` lost the minutes-per-day/start-time fields since there's no duration to schedule against anymore. And `build_schedule` went from per-pet to per-owner, since the spec wanted the `Scheduler` managing tasks across all of an owner's pets at once, not one pet at a time. `ScheduledTask` picked up a `pet` reference so the merged plan can still say whose task is whose, and same-time conflicts across pets now show up in `DailyPlan.conflicts` instead of getting silently resolved.

I checked this by hand: built an owner with two pets, gave one pet two tasks at the same time and the other a completed one-off task, and confirmed the completed task got left out and the `08:00` collision got flagged.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

Really just two things: time and whether a task is actually due. `sort_by_time()` orders everything by `task.time`, and `find_conflicts()` uses that same field to catch two tasks landing in the same slot. On top of that, `is_due()` decides whether a task belongs on a given day at all — it drops anything already `completed`, and for `WEEKLY` tasks it checks `recurs_on` to see if today's the right weekday. Which pet a task belongs to isn't really a constraint on top of that, it's just how the plan groups and labels things once they're already included.

There's no priority or duration in the mix. `Owner` still has a `preferences` dict, but nothing in `Scheduler` actually reads it right now — it's there as a placeholder for later, not something the scheduler currently factors in.

I landed on time + due-status as the constraints that mattered because they're the two things a merged, cross-pet daily plan can't work without: you need to know what's due today, and you need some order to put it in. Priority and duration were part of my original 9-class design, but once the spec called for the leaner 4-class model (see §1b), I cut them along with everything else that assumed a `duration_minutes` field — they'd have needed reintroducing the time-budget math I already decided not to bring back in §2b.

**b. Tradeoffs**

The scheduler only catches a conflict when two tasks land on the exact same time string, like two things both at `"08:00"`. It has no idea about duration, so a 30-minute walk at `08:00` and something else starting at `08:15` would really overlap, but PawPal+ won't catch it since `"08:00" != "08:15"`.

This will work for now. `Task` doesn't have a duration field — the whole point of moving to the leaner 4-class model was treating each task as a point in time, not a block of time. Actually detecting overlap would mean bringing duration back and switching from a plain equality check to interval math (`a.start < b.end and b.start < a.end`), which is a bigger change than what exact-time matching needs. Exact-time still catches the obvious case — two things scheduled at literally the same moment — and it's just one pass that buckets tasks into a dict by time, so there's no interval math to get wrong. Good enough for a first version. Real overlap detection would be the natural next step if duration comes back into the model.

---

## 3. AI Collaboration & Strategy

**a. Most effective AI features**

Two things helped the most. First, turning the UML into class stubs quickly — once I'd settled on `Task`/`Pet`/`Owner`/`Scheduler`, I didn't have to hand-type four `__init__` signatures with type hints myself, I could get the boilerplate out of the way fast and spend my actual time on the scheduling logic.

Second, refactoring across files at once. A bunch of changes touched `pawpal_system.py`, `app.py`, `main.py`, and the tests at the same time — like when `build_schedule` went from per-pet to per-owner, or when `filter_tasks()`/`tasks_at_time()` got added and the Streamlit UI needed to call them. Having those updates happen together caught call sites I probably would've forgotten to fix by hand.

**b. Judgment and verification — a rejected suggestion**

When I was wiring the "Add task" flow in `app.py`, the first pass handled a same-time conflict by just adding the task anyway and showing a warning afterward — basically the same treatment `find_conflicts()`/`conflict_warnings()` already give a schedule that's already been built: report it, don't stop it.

I didn't want that for the add-task flow specifically. If the conflict gets created and you only warn about it after, the user's already done the double-booking — the warning isn't preventing anything at that point. I wanted the task blocked from being created at all, with the user asked to pick a different time instead. That's why `tasks_at_time()` exists as its own thing, separate from the after-the-fact conflict detection `build_schedule()` uses. I tested it by trying to add a task at a time that already had something scheduled — no new row showed up in "Current Tasks," just the warning.

**c. Staying organized across sessions**

I split sessions at the design step but not much past that. The UML/class-design work happened in its own chat, separate from implementation, which kept that early architecture stuff — the class list, which fields belonged where — as a clean record I could go back to in `diagrams/uml.mmd` without digging through implementation details later.

Once actual code existed, I mostly just stayed in one session through implementation, testing, and polish. Splitting further didn't feel worth it — a new session would've needed all the context of the existing codebase anyway, and re-explaining what `Scheduler` does or what `mark_complete()` triggers would've cost more time than it saved. Splitting seems worth it before code exists; after that, staying in one place mattered more than starting clean.

**d. Being the "lead architect"**

The AI was reliably good at generating code that held together structurally, and at catching structural bugs — the `Priority` ordering issue, keeping call sites updated during a refactor, that kind of thing. What it couldn't do on its own was make the actual product calls: should a conflict block the action or just get flagged, does the 4-class model really fit this assignment better than the richer version I'd originally built. Those needed someone who knew what the app was actually supposed to do, not just what the code currently does.

Being the one steering meant treating what the AI gave me as a good first draft, not the final word — take what's clearly correct or matches the spec, but push back on anything that's really a decision, not a fact, because it'll confidently hand you an answer either way and only you know which one is actually right for this app.

---

## 4. Testing and Verification

**a. What you tested**

`tests/test_pawpal.py` has 5 tests. I tried to pick behaviors that would actually matter if they broke.

`test_mark_complete_changes_status` just checks that `mark_complete()` flips `completed` to `True`. Simple, but recurrence and `is_due()` both depend on it working right. `test_adding_task_increases_pet_task_count` checks that adding a `Task` to a `Pet` actually shows up in `get_tasks()` — basic, but everything else builds on that relationship existing. `test_sort_by_time_returns_chronological_order` adds tasks out of order (18:00, 08:00, 12:30) and checks that `sort_by_time()` puts them back in order — this is the one thing a user would notice immediately if it broke.

`test_mark_complete_daily_task_creates_next_day_task` checks that completing a `DAILY` task creates the next one exactly a day later, still marked incomplete, and actually attached to the same pet. This one has the most moving parts — date math, resetting `completed`, re-registering on the pet — so it's the one I was most worried about breaking quietly during a refactor. `test_build_schedule_flags_duplicate_times_as_conflict` checks that two different pets' tasks at the same time get flagged together, which specifically tests the merge-across-pets behavior, not just single-pet scheduling.

I tried to pick five tests that each hit a different piece of the system rather than testing the same path five different ways.

**b. Confidence**

I would rate the confidence a 3 out of 5 stars. All the tests pass, and they cover what a demo would actually show off — sorting, daily recurrence, same-time conflicts. But there's real stuff not covered: `WEEKLY` tasks with a specific `recurs_on` — recurrence is only tested for `DAILY`, so the weekday-filtering part of `is_due()` has zero tests. `is_due()` edge cases, like a task due exactly on the date being checked, or one that's already completed, aren't tested directly either. `filter_tasks()` with no matches has never been tried. Same-pet conflicts aren't tested separately — the existing conflict test uses two different pets, and one pet with two tasks at the same time goes through a different path in `find_conflicts()`. And `tasks_at_time()`/`conflict_warnings()` both get used in `main.py` and `app.py` but neither has an actual automated test.

If I had more time, `WEEKLY`/`recurs_on` and `tasks_at_time()` would be first, since those are the two spots where something could look fine in a demo and still be wrong underneath.

---

## 5. Reflection

**a. What went well**

The thing I'm happiest with is that `Task.mark_complete()` handles creating its own next occurrence instead of making `Scheduler` or whatever's calling it remember to do that. The alternative — `app.py` or `Scheduler` checking "was this recurring? okay, go make the next one and re-add it" — is exactly the kind of thing that gets forgotten in one spot and causes a bug that doesn't show up for days. Making `Task` handle it itself means that can't happen.

**b. What you would improve**

Two things, and I already called both of these out above: real overlap detection instead of exact-time matching (a walk at `08:00` and something at `08:15` should conflict and currently don't), and the test gaps around `WEEKLY`/`recurs_on`, since `is_due()` has real branching logic there that nothing actually tests. Neither is something I missed — I knew about both and decided to leave them for later — but that doesn't make them any less of a risk sitting in the code right now.

**c. Key takeaway**

The biggest thing I learned wasn't really about scheduling logic, it was that matching what the assignment actually asked for mattered more than building the fanciest version I could think of. My original design had `Priority`, `TaskCategory`, duration-based time budgets — all of which felt more "complete" — but the spec wanted the leaner 4-class version, and keeping the bigger design would've meant maintaining logic and tests for stuff nothing actually needed. Cutting it down to match the spec instead of defending it because I'd already built it was the right call, and it's something I want to keep doing: build for what's actually being asked, not the most impressive version of the problem I can come up with.
