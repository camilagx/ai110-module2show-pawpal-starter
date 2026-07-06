"""PawPal+ logic layer.

Core model: Task, Pet, Owner, Scheduler. The Scheduler is the "brain" — it
pulls every task across every one of an owner's pets and merges them into a
single time-ordered DailyPlan (ScheduledTask/DailyPlan are just the
Scheduler's output records, not separate user-facing concepts).
"""

from __future__ import annotations

import datetime
from collections import defaultdict
from enum import Enum
from typing import Optional
from uuid import uuid4


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


class Task:
    """A single pet-care activity: what to do, when, how often, and whether
    it's done.

    `time` is a zero-padded 24-hour "HH:MM" string (e.g. "08:00") so plain
    string comparison/sorting matches chronological order.
    """

    def __init__(
        self,
        description: str,
        time: str,
        frequency: Frequency = Frequency.ONCE,
        completed: bool = False,
        id: Optional[str] = None,
        recurs_on: Optional[list[int]] = None,
        due_date: Optional[datetime.date] = None,
    ):
        """Create a task with a description, scheduled time, frequency, and completion state."""
        self.id = id or str(uuid4())
        self.description = description
        self.time = time
        self.frequency = frequency
        self.completed = completed
        # Weekdays (0=Monday...6=Sunday) a WEEKLY task applies on. Empty means
        # "no specific day set" -> treated as due every day, same as DAILY.
        self.recurs_on = recurs_on if recurs_on is not None else []
        # The date this specific occurrence is due. Advances via next_occurrence()
        # each time a DAILY/WEEKLY task is completed.
        self.due_date = due_date if due_date is not None else datetime.date.today()
        # Set automatically by Pet.add_task so mark_complete() can register the
        # next occurrence on the same pet without the caller doing it manually.
        self.pet: Optional["Pet"] = None

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete, auto-creating the next occurrence for DAILY/WEEKLY tasks."""
        self.completed = True
        next_task = self.next_occurrence()
        if next_task is not None and self.pet is not None:
            self.pet.add_task(next_task)
        return next_task

    def mark_incomplete(self) -> None:
        """Mark this task as not completed."""
        self.completed = False

    def next_occurrence(self) -> Optional["Task"]:
        """Return a new Task for this task's next due date, or None for a one-off (ONCE) task.

        WEEKLY advances by exactly one week via timedelta, so a task with more
        than one day in recurs_on has all of those days shift together — good
        enough for a single weekly slot, not a true per-weekday tracker.
        """
        if self.frequency == Frequency.ONCE:
            return None
        step = datetime.timedelta(days=1) if self.frequency == Frequency.DAILY else datetime.timedelta(weeks=1)
        return Task(
            self.description,
            self.time,
            frequency=self.frequency,
            recurs_on=self.recurs_on,
            due_date=self.due_date + step,
        )

    def is_due(self, on_date: datetime.date) -> bool:
        """Return whether this task should appear on the schedule for on_date."""
        if self.completed:
            return False
        if self.frequency == Frequency.ONCE:
            return True
        if on_date < self.due_date:
            return False
        if self.frequency == Frequency.WEEKLY and self.recurs_on:
            return on_date.weekday() in self.recurs_on
        return True  # DAILY, or WEEKLY with no specific day set

    def __repr__(self) -> str:
        """Return a debug-friendly string representation of the task."""
        status = "done" if self.completed else "pending"
        return f"<Task {self.description!r} at {self.time} ({self.frequency.value}, {status})>"


class Pet:
    """Basic info for one pet plus the tasks that apply to it."""

    def __init__(
        self,
        name: str,
        species: str,
        owner: "Owner",
        breed: Optional[str] = None,
        age: Optional[int] = None,
    ):
        """Create a pet linked to an owner, registering it on that owner automatically."""
        self.name = name
        self.species = species
        self.breed = breed
        self.age = age
        self.owner = owner
        self.tasks: list[Task] = []
        owner.add_pet(self)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list if not already present."""
        if task not in self.tasks:
            self.tasks.append(task)
        task.pet = self

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id from this pet's task list."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)

    def __repr__(self) -> str:
        """Return a debug-friendly string representation of the pet."""
        return f"<Pet {self.name} ({self.species})>"


class Owner:
    """The pet owner: manages multiple pets and exposes all their tasks."""

    def __init__(self, name: str, preferences: Optional[dict] = None):
        """Create an owner with a name and optional scheduling preferences."""
        self.name = name
        self.preferences = preferences or {}
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list (idempotent) and set the pet's owner reference."""
        if pet not in self.pets:
            self.pets.append(pet)
        pet.owner = self

    def get_pets(self) -> list[Pet]:
        """Return a copy of this owner's pet list."""
        return list(self.pets)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all of this owner's pets."""
        return [(pet, task) for pet in self.pets for task in pet.get_tasks()]

    def __repr__(self) -> str:
        """Return a debug-friendly string representation of the owner."""
        return f"<Owner {self.name}>"


class ScheduledTask:
    """A Task placed into a DailyPlan, tagged with which pet it's for."""

    def __init__(self, pet: Pet, task: Task, reason: str = ""):
        """Create a scheduled task pairing a task with the pet it belongs to."""
        self.pet = pet
        self.task = task
        self.reason = reason

    def __repr__(self) -> str:
        """Return a debug-friendly string representation of the scheduled task."""
        return f"<ScheduledTask {self.task.description!r} for {self.pet.name} at {self.task.time}>"


class DailyPlan:
    """The Scheduler's output: one owner's due tasks across all of their
    pets, merged into a single time-ordered schedule."""

    def __init__(self, owner: Owner, date: str):
        """Create an empty daily plan for an owner on a given date."""
        self.owner = owner
        self.date = date
        self.scheduled_tasks: list[ScheduledTask] = []
        self.conflicts: list[list[ScheduledTask]] = []

    def add_scheduled_task(self, scheduled_task: ScheduledTask) -> None:
        """Append a scheduled task to this plan."""
        self.scheduled_tasks.append(scheduled_task)

    def summary(self) -> str:
        """Return a human-readable summary of the plan and any conflicts."""
        if not self.scheduled_tasks:
            return f"No tasks scheduled for {self.owner.name} on {self.date}."
        lines = [f"Daily plan for {self.owner.name} — {self.date}:"]
        for st in self.scheduled_tasks:
            lines.append(f"  {st.task.time} — {st.task.description} ({st.pet.name})")
        if self.conflicts:
            lines.append("Conflicts:")
            for group in self.conflicts:
                who = ", ".join(f"{st.pet.name}'s {st.task.description!r}" for st in group)
                lines.append(f"  {group[0].task.time}: {who}")
        return "\n".join(lines)


class Scheduler:
    """The "brain": retrieves, organizes, and manages tasks across all of an
    owner's pets, merging them into one DailyPlan."""

    def build_schedule(self, owner: Owner, date: str) -> DailyPlan:
        """Build a merged daily plan across all of an owner's pets."""
        plan = DailyPlan(owner, date)
        on_date = datetime.date.fromisoformat(date)
        due_tasks = self.get_due_tasks(owner, on_date)
        ordered = self.sort_by_time(due_tasks)
        for pet, task in ordered:
            plan.add_scheduled_task(ScheduledTask(pet, task, self.explain(task)))
        plan.conflicts = self.find_conflicts(plan.scheduled_tasks)
        return plan

    def get_due_tasks(self, owner: Owner, on_date: datetime.date) -> list[tuple[Pet, Task]]:
        """Return the (pet, task) pairs that are due for scheduling on on_date."""
        return [(pet, task) for pet, task in owner.get_all_tasks() if task.is_due(on_date)]

    def filter_tasks(
        self,
        pet_tasks: list[tuple[Pet, Task]],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[tuple[Pet, Task]]:
        """Return the (pet, task) pairs matching the given pet name and/or completion status."""
        return [
            (pet, task)
            for pet, task in pet_tasks
            if (pet_name is None or pet.name == pet_name)
            and (completed is None or task.completed == completed)
        ]

    def sort_by_time(self, pet_tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Return the given (pet, task) pairs sorted chronologically by task time."""
        return sorted(pet_tasks, key=lambda pair: pair[1].time)

    def find_conflicts(self, scheduled_tasks: list[ScheduledTask]) -> list[list[ScheduledTask]]:
        """Return groups of 2+ scheduled tasks that land on the same time slot."""
        by_time: dict[str, list[ScheduledTask]] = defaultdict(list)
        for scheduled_task in scheduled_tasks:
            by_time[scheduled_task.task.time].append(scheduled_task)
        return [group for group in by_time.values() if len(group) > 1]

    def tasks_at_time(self, pet_tasks: list[tuple[Pet, Task]], time: str) -> list[tuple[Pet, Task]]:
        """Return the (pet, task) pairs already scheduled at the given time, for pre-add conflict checks."""
        return [(pet, task) for pet, task in pet_tasks if task.time == time]

    def conflict_warnings(self, scheduled_tasks: list[ScheduledTask]) -> list[str]:
        """Return a human-readable warning for each same-time conflict group (same pet or different pets), instead of raising."""
        warnings = []
        for group in self.find_conflicts(scheduled_tasks):
            who = ", ".join(f"{st.pet.name}'s {st.task.description!r}" for st in group)
            warnings.append(f"⚠️ Conflict at {group[0].task.time}: {who}")
        return warnings

    def explain(self, task: Task) -> str:
        """Return a short explanation of when and how often a task recurs."""
        return f"Scheduled at {task.time} ({task.frequency.value})"
