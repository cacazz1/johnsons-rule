import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Johnson's Rule | Flow Shop Scheduling", layout="wide")

st.title("Johnson's Rule - Minimize Makespan")

# Input jumlah task
num_tasks = st.number_input("Number of Tasks", min_value=1, max_value=20, value=10, step=1, key="num_tasks_input")

# Default data
default_p1 = [3,6,2,7,6,5,5,3,6,10]
default_p2 = [5,2,8,6,6,9,4,2,8,4]

if num_tasks == 10:
    p1 = default_p1
    p2 = default_p2
else:
    p1 = [0]*num_tasks
    p2 = [0]*num_tasks

# DataFrame dengan kolom nomor (readonly)
df = pd.DataFrame({
    "Task": [f"Task {i+1}" for i in range(num_tasks)],
    "Processor 1 (hours)": p1[:num_tasks],
    "Processor 2 (hours)": p2[:num_tasks]
})

st.write("### Task Processing Times")
edited_df = st.data_editor(
    df,
    column_config={
        "Task": st.column_config.Column(width="medium", disabled=True),
        "Processor 1 (hours)": st.column_config.Column(width="medium"),
        "Processor 2 (hours)": st.column_config.Column(width="medium"),
    },
    use_container_width=False,
    hide_index=True,
    num_rows="dynamic"
)

# ---------- Fungsi Johnson's Rule ----------
def johnsons_rule(processing_times):
    tasks = list(enumerate(processing_times))
    left = []
    right = []
    while tasks:
        idx, (p1, p2) = min(tasks, key=lambda x: min(x[1]))
        if p1 <= p2:
            left.append(idx)
        else:
            right.insert(0, idx)
        tasks.remove((idx, (p1, p2)))
    return left + right

# ---------- Fungsi Penjadwalan ----------
def calculate_schedule(processing_times, sequence):
    n = len(sequence)
    start_m1 = [0]*n
    finish_m1 = [0]*n
    start_m2 = [0]*n
    finish_m2 = [0]*n
    for i, idx in enumerate(sequence):
        p1, p2 = processing_times[idx]
        start_m1[i] = finish_m1[i-1] if i > 0 else 0
        finish_m1[i] = start_m1[i] + p1
        start_m2[i] = max(finish_m2[i-1] if i > 0 else 0, finish_m1[i])
        finish_m2[i] = start_m2[i] + p2
    return start_m1, finish_m1, start_m2, finish_m2

# ---------- Fungsi Hitung Delay & Metrik ----------
def calculate_delays(start_m1, finish_m1, start_m2, finish_m2, makespan):
    delay_m1 = makespan - finish_m1[-1]
    delay_m2 = start_m2[0]
    for i in range(1, len(start_m2)):
        idle = start_m2[i] - finish_m2[i-1]
        if idle > 0:
            delay_m2 += idle
    return delay_m1, delay_m2

def calculate_metrics(finish_m1, finish_m2, start_m1, start_m2):
    makespan = finish_m2[-1]
    delay_m1, delay_m2 = calculate_delays(start_m1, finish_m1, start_m2, finish_m2, makespan)
    average_delay = ((delay_m1/makespan) + (delay_m2/makespan)) / 2
    utilization = 1 - average_delay
    return makespan, delay_m1, delay_m2, average_delay, utilization

# ---------- Fungsi Plot Gantt Chart ----------
def plot_gantt(processing_times, sequence, start_m1, finish_m1, start_m2, finish_m2):
    fig, ax = plt.subplots(figsize=(12, 4))
    colors = plt.cm.Paired.colors
    n = len(sequence)
    for i, idx in enumerate(sequence):
        color = colors[i % len(colors)]
        # Processor 1
        ax.barh(1, finish_m1[i] - start_m1[i], left=start_m1[i], height=0.4, color=color, edgecolor='black')
        ax.text(start_m1[i] + (finish_m1[i] - start_m1[i])/2, 1, f'T{idx+1}', ha='center', va='center', fontsize=10, weight='bold')
        # Processor 2
        ax.barh(0, finish_m2[i] - start_m2[i], left=start_m2[i], height=0.4, color=color, edgecolor='black')
        ax.text(start_m2[i] + (finish_m2[i] - start_m2[i])/2, 0, f'T{idx+1}', ha='center', va='center', fontsize=10, weight='bold')
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['Processor 2', 'Processor 1'])
    ax.set_xlabel('Time (hours)')
    ax.set_title('Gantt Chart - Johnson\'s Rule Optimal Schedule')
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    return fig

# ---------- STREAMLIT APP ----------
processing_times = list(zip(edited_df["Processor 1 (hours)"], edited_df["Processor 2 (hours)"]))

if st.button("Calculate Optimal Sequence"):
    # Validasi input
    if any(p1 < 0 or p2 < 0 for p1, p2 in processing_times):
        st.error("Processing times must be non-negative!")
    else:
        # Johnson's Rule
        sequence = johnsons_rule(processing_times)
        # Jadwal
        start_m1, finish_m1, start_m2, finish_m2 = calculate_schedule(processing_times, sequence)
        # Metrik
        makespan, delay_m1, delay_m2, average_delay, utilization = calculate_metrics(
            finish_m1, finish_m2, start_m1, start_m2
        )
        # Tampilkan hasil
        st.subheader("Results")
        st.markdown("**Optimal Task Sequence:**")
        st.write(" → ".join([f"T{idx+1}" for idx in sequence]))
        st.markdown("**Performance Metrics:**")
        st.write(f"Makespan: **{makespan}** hours")
        st.write(f"Delay of M1: **{delay_m1}**")
        st.write(f"Delay of M2: **{delay_m2}**")
        st.write(f"Average Delay: **{average_delay:.4f}**")
        st.write(f"Utilization: **{utilization:.4%}**")
        # Gantt Chart
        st.subheader("Gantt Chart")
        fig = plot_gantt(processing_times, sequence, start_m1, finish_m1, start_m2, finish_m2)
        st.pyplot(fig)