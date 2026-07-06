from pawpal_system import Owner, Pet, Task


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
