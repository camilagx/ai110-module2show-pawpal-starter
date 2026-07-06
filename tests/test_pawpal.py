import datetime

from pawpal_system import Frequency, Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", "08:00")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    owner = Owner("Camila")
    pet = Pet("Kumo", "dog", owner)
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Morning walk", "08:00"))

    assert len(pet.get_tasks()) == 1


def test_sort_by_time_returns_chronological_order():
    owner = Owner("Camila")
    pet = Pet("Kumo", "dog", owner)
    pet.add_task(Task("Dinner", "18:00"))
    pet.add_task(Task("Breakfast", "08:00"))
    pet.add_task(Task("Walk", "12:30"))

    scheduler = Scheduler()
    ordered = scheduler.sort_by_time(owner.get_all_tasks())

    assert [task.time for _, task in ordered] == ["08:00", "12:30", "18:00"]


def test_mark_complete_daily_task_creates_next_day_task():
    owner = Owner("Camila")
    pet = Pet("Kumo", "dog", owner)
    today = datetime.date(2026, 7, 5)
    task = Task("Feed", "08:00", frequency=Frequency.DAILY, due_date=today)
    pet.add_task(task)

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + datetime.timedelta(days=1)
    assert next_task.completed is False
    assert next_task in pet.get_tasks()


def test_build_schedule_flags_duplicate_times_as_conflict():
    owner = Owner("Camila")
    pet1 = Pet("Kumo", "dog", owner)
    pet2 = Pet("Miso", "cat", owner)
    pet1.add_task(Task("Walk", "08:00"))
    pet2.add_task(Task("Feed", "08:00"))

    scheduler = Scheduler()
    plan = scheduler.build_schedule(owner, "2026-07-05")

    assert len(plan.conflicts) == 1
    assert len(plan.conflicts[0]) == 2
