"""PawPal+ logic layer.

Core model: Task, Pet, Owner, Scheduler. The Scheduler is the "brain" — it
pulls every task across every one of an owner's pets and merges them into a
single time-ordered DailyPlan (ScheduledTask/DailyPlan are just the
Scheduler's output records, not separate user-facing concepts).
"""

from __future__ import annotations

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
    ):
        """Create a task with a description, scheduled time, frequency, and completion state."""
        self.id = id or str(uuid4())
        self.description = description
        self.time = time
        self.frequency = frequency
        self.completed = completed

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not completed."""
        self.completed = False

    def is_due(self) -> bool:
        """Return whether this task should appear in today's schedule."""
        if self.frequency == Frequency.ONCE:
            return not self.completed
        return True

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
        self.conflicts: list[tuple[ScheduledTask, ScheduledTask]] = []

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
            for a, b in self.conflicts:
                lines.append(
                    f"  {a.task.time}: {a.pet.name}'s {a.task.description!r} "
                    f"overlaps {b.pet.name}'s {b.task.description!r}"
                )
        return "\n".join(lines)


class Scheduler:
    """The "brain": retrieves, organizes, and manages tasks across all of an
    owner's pets, merging them into one DailyPlan."""

    def build_schedule(self, owner: Owner, date: str) -> DailyPlan:
        """Build a merged daily plan across all of an owner's pets."""
        plan = DailyPlan(owner, date)
        due_tasks = self.get_due_tasks(owner)
        ordered = self.sort_by_time(due_tasks)
        for pet, task in ordered:
            plan.add_scheduled_task(ScheduledTask(pet, task, self.explain(task)))
        plan.conflicts = self.find_conflicts(plan.scheduled_tasks)
        return plan

    def get_due_tasks(self, owner: Owner) -> list[tuple[Pet, Task]]:
        """Return the (pet, task) pairs that are due for scheduling."""
        return [(pet, task) for pet, task in owner.get_all_tasks() if task.is_due()]

    def sort_by_time(self, pet_tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Return the given (pet, task) pairs sorted chronologically by task time."""
        return sorted(pet_tasks, key=lambda pair: pair[1].time)

    def find_conflicts(
        self, scheduled_tasks: list[ScheduledTask]
    ) -> list[tuple[ScheduledTask, ScheduledTask]]:
        """Return pairs of scheduled tasks that land on the same time slot."""
        conflicts = []
        for a, b in zip(scheduled_tasks, scheduled_tasks[1:]):
            if a.task.time == b.task.time:
                conflicts.append((a, b))
        return conflicts

    def explain(self, task: Task) -> str:
        """Return a short explanation of when and how often a task recurs."""
        return f"Scheduled at {task.time} ({task.frequency.value})"
