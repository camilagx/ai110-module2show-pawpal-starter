from datetime import date, time as time_of_day

import streamlit as st

from pawpal_system import Frequency, Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

scheduler = Scheduler()

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Camila")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(owner_name)
owner = st.session_state.owner
owner.name = owner_name

st.divider()

st.subheader("Add a Pet")
col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Kumo")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if pet_name:
        Pet(pet_name, species, owner)  # Pet.__init__ registers itself on owner.pets
        st.success(f"Added {pet_name} to {owner.name}'s pets.")
    else:
        st.warning("Enter a pet name first.")

if owner.get_pets():
    st.write("Pets:")
    st.table([{"name": p.name, "species": p.species} for p in owner.get_pets()])
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.subheader("Schedule a Task")

if owner.get_pets():
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_pet_name = st.selectbox("Pet", [p.name for p in owner.get_pets()])
    with col2:
        description = st.text_input("Task description", value="Morning walk")
    with col3:
        task_time = st.time_input("Time", value=time_of_day(8, 0))

    frequency = st.selectbox("Frequency", [f.value for f in Frequency], index=1)

    if st.button("Add task"):
        new_time = task_time.strftime("%H:%M")
        clashes = scheduler.tasks_at_time(owner.get_all_tasks(), new_time)
        if clashes:
            clash_list = ", ".join(f"{pet.name}'s {task.description!r}" for pet, task in clashes)
            st.warning(
                f"⏰ {new_time} conflicts with {clash_list}. Please enter a different time."
            )
        else:
            selected_pet = next(p for p in owner.get_pets() if p.name == selected_pet_name)
            selected_pet.add_task(Task(description, new_time, Frequency(frequency)))
            st.success(f"Added '{description}' at {new_time} for {selected_pet_name}.")
else:
    st.info("Add a pet before scheduling tasks.")

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "pet": pet.name,
                "description": t.description,
                "time": t.time,
                "frequency": t.frequency.value,
                "completed": t.completed,
            }
            for pet, t in all_tasks
        ]
    )

st.divider()

st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    plan = scheduler.build_schedule(owner, date.today().isoformat())
    st.text(plan.summary())
