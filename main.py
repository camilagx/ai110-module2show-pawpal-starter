"""Demo script for the PawPal+ backend classes."""

from datetime import date

from pawpal_system import Frequency, Owner, Pet, Scheduler, Task


def print_pairs(pet_tasks: list[tuple[Pet, Task]]) -> None:
    for pet, task in pet_tasks:
        status = "done" if task.completed else "pending"
        print(f"  {task.time} — {task.description} ({pet.name}, {status})")


def main() -> None:
    owner = Owner("Camila")

    kumo = Pet("Kumo", "dog", owner)
    whiskers = Pet("Whiskers", "cat", owner)

    # Added deliberately out of chronological order to prove sort_by_time
    # actually sorts, rather than just preserving insertion order.
    kumo.add_task(Task("Evening walk", "18:00", Frequency.DAILY))
    whiskers.add_task(Task("Litter box cleaning", "12:00", Frequency.WEEKLY))
    kumo.add_task(Task("Morning walk", "08:00", Frequency.DAILY))
    whiskers.add_task(Task("Vet checkup", "10:00", Frequency.ONCE, completed=True))
    whiskers.add_task(Task("Feeding", "08:30", Frequency.DAILY))

    # Same time as Kumo's "Morning walk" but for a different pet, to verify
    # the Scheduler flags cross-pet conflicts, not just same-pet ones.
    whiskers.add_task(Task("Morning cuddles", "08:00", Frequency.DAILY))

    scheduler = Scheduler()
    all_pairs = owner.get_all_tasks()

    print("Tasks as added (unsorted):")
    print_pairs(all_pairs)

    print("\nSorted by time:")
    print_pairs(scheduler.sort_by_time(all_pairs))

    print("\nFiltered to Kumo's tasks:")
    print_pairs(scheduler.filter_tasks(all_pairs, pet_name="Kumo"))

    print("\nFiltered to incomplete tasks:")
    print_pairs(scheduler.filter_tasks(all_pairs, completed=False))

    print("\nToday's Schedule")
    print("=" * 40)
    today = date.today().isoformat()
    plan = scheduler.build_schedule(owner, today)
    print(plan.summary())

    print("\nConflict warnings:")
    warnings = scheduler.conflict_warnings(plan.scheduled_tasks)
    if warnings:
        for warning in warnings:
            print(f"  {warning}")
    else:
        print("  None")


if __name__ == "__main__":
    main()
