"""PawPal+ logic layer.

Class skeletons only (attributes + method signatures), matching the UML
draft in diagrams/uml.mmd. No scheduling logic yet — that comes next.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskCategory(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    OTHER = "other"


class Recurrence(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


class Owner:
    def __init__(
        self,
        name: str,
        available_minutes_per_day: int,
        preferred_start_time: str,
        preferences: Optional[dict] = None,
    ):
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferred_start_time = preferred_start_time
        self.preferences = preferences or {}
        self.pets: list[Pet] = []

    def add_pet(self, pet: "Pet") -> None:
        raise NotImplementedError

    def get_pets(self) -> list["Pet"]:
        raise NotImplementedError


class Pet:
    def __init__(
        self,
        name: str,
        species: str,
        owner: Owner,
        breed: Optional[str] = None,
        age: Optional[int] = None,
    ):
        self.name = name
        self.species = species
        self.breed = breed
        self.age = age
        self.owner = owner
        self.tasks: list[CareTask] = []

    def add_task(self, task: "CareTask") -> None:
        raise NotImplementedError

    def remove_task(self, task_id: str) -> None:
        raise NotImplementedError

    def get_tasks(self) -> list["CareTask"]:
        raise NotImplementedError


class CareTask:
    def __init__(
        self,
        id: str,
        title: str,
        category: TaskCategory,
        duration_minutes: int,
        priority: Priority,
        fixed_time: Optional[str] = None,
        recurrence: Recurrence = Recurrence.NONE,
    ):
        self.id = id
        self.title = title
        self.category = category
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.fixed_time = fixed_time
        self.recurrence = recurrence

    def __repr__(self) -> str:
        raise NotImplementedError


class ScheduledTask:
    def __init__(
        self,
        task: CareTask,
        start_time: str,
        end_time: str,
        reason: str = "",
    ):
        self.task = task
        self.start_time = start_time
        self.end_time = end_time
        self.reason = reason


class DailyPlan:
    def __init__(self, pet: Pet, date: str):
        self.pet = pet
        self.date = date
        self.scheduled_tasks: list[ScheduledTask] = []
        self.skipped_tasks: list[tuple[CareTask, str]] = []

    def total_time_used(self) -> int:
        raise NotImplementedError

    def summary(self) -> str:
        raise NotImplementedError


class Scheduler:
    def build_schedule(
        self, pet: Pet, available_minutes: int, day_start: str
    ) -> DailyPlan:
        raise NotImplementedError

    def sort_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        raise NotImplementedError

    def filter_by_time(
        self, sorted_tasks: list[CareTask], available_minutes: int
    ) -> list[CareTask]:
        raise NotImplementedError

    def resolve_conflicts(self, tasks: list[CareTask]) -> list[CareTask]:
        raise NotImplementedError

    def explain(self, scheduled_task: ScheduledTask) -> str:
        raise NotImplementedError
