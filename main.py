"""Demo script for the PawPal+ backend classes."""

from datetime import date

from pawpal_system import Frequency, Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner("Jordan")

    mochi = Pet("Mochi", "dog", owner)
    biscuit = Pet("Biscuit", "cat", owner)

    mochi.add_task(Task("Morning walk", "08:00", Frequency.DAILY))
    mochi.add_task(Task("Evening walk", "18:00", Frequency.DAILY))
    biscuit.add_task(Task("Feeding", "08:30", Frequency.DAILY))
    biscuit.add_task(Task("Litter box cleaning", "12:00", Frequency.WEEKLY))

    scheduler = Scheduler()
    today = date.today().isoformat()
    plan = scheduler.build_schedule(owner, today)

    print("Today's Schedule")
    print("=" * 40)
    print(plan.summary())


if __name__ == "__main__":
    main()
