import logging
from pulp import LpProblem, LpMinimize, LpVariable, value, LpStatus

# Set up logging for easier visualization of results.
logging.basicConfig(
    filename='project_schedule.log',
    filemode='w',  # Overwrite on each run
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# Task dependencies and durations for each scenario
tasks_expected = {
    "A": 20, "B": 30, "C": 16, "D1": 40, "D2": 60, "D3": 50,
    "D4": 160, "D5": 40, "D6": 60, "D7": 80, "D8": 20,
    "E": 24, "F": 40, "G": 50, "H": 30
}

tasks_best = {
    "A": 10, "B": 15, "C": 8, "D1": 20, "D2": 30, "D3": 25,
    "D4": 80, "D5": 20, "D6": 30, "D7": 40, "D8": 10,
    "E": 12, "F": 20, "G": 25, "H": 15
}

tasks_worst = {
    "A": 30, "B": 45, "C": 24, "D1": 60, "D2": 90, "D3": 75,
    "D4": 240, "D5": 60, "D6": 90, "D7": 120, "D8": 30,
    "E": 36, "F": 60, "G": 75, "H": 45
}

dependencies = {
    "C": ["A"],
    "D1": ["A"],
    "D2": ["D1"],
    "D3": ["D1"],
    "D4": ["D2", "D3"],
    "D5": ["D4"],
    "D6": ["D4"],
    "D7": ["D6"],
    "D8": ["D5", "D7"],
    "E": ["B", "C"],
    "F": ["D8", "E"],
    "G": ["A", "D8"],
    "H": ["F", "G"]
}

# Worker requirement for each task
worker_requirements = {
    "A": {"projectManager": 1},
    "B": {"projectManager": 1},
    "C": {"frontendDeveloper": 1},
    "D1": {"projectManager": 1, "backendDeveloper": 1},
    "D2": {"backendDeveloper": 1},
    "D3": {"backendDeveloper": 1, "dataEngineer": 1},
    "D4": {"frontendDeveloper": 1, "backendDeveloper": 1},
    "D5": {"projectManager": 1},
    "D6": {"dataScientist": 1},
    "D7": {"dataScientist": 1},
    "D8": {"projectManager": 1},
    "E": {"projectManager": 1, "dataEngineer": 1},
    "F": {"projectManager": 1, "dataEngineer": 1},
    "G": {"projectManager": 1, "dataEngineer": 1},
    "H": {"projectManager": 1}
}

# Hourly rate for workers (same for all positions for simplicity)
hourly_rate = 100

# Function to calculate the total costs for each scenario.
# The calculation is based on the total workers allocated for each task and the duration of the task multiplied by the hourly rate.
def compute_total_cost(tasks, worker_requirements, uniform_rate):
    total_cost = 0.0
    cost_by_task = {}
    for task, duration in tasks.items():
        total_workers = sum(worker_requirements.get(task, {}).values())
        cost_for_task = duration * total_workers * uniform_rate
        cost_by_task[task] = cost_for_task
        total_cost += cost_for_task
    return total_cost, cost_by_task

# Function to calculate the worker requirements for each scenario.
# This function takes into account the possibility that multiple tasks may require the same worker role at the same time.
def compute_peak_concurrency(schedule, worker_requirements):
    # Gather all unique time instants when any task starts or finishes.
    times = sorted({time for times in schedule.values() for time in times})
    peak = {}
    
    # For each time, compute the total number of workers required per role.
    for t in times:
        current = {}
        for task, (start, finish) in schedule.items():
            # A task is active if it has started but not yet finished at time t.
            if start <= t < finish:
                for role, count in worker_requirements.get(task, {}).items():
                    current[role] = current.get(role, 0) + count
        # Update peak values.
        for role, count in current.items():
            peak[role] = max(peak.get(role, 0), count)
    return peak

# Function to calculate the schedule, critical path, total cost, and worker requirements for each scenario.
# The function also includes logging for visualization of the results.
def compute_schedule_and_critical_path(tasks, dependencies, scenario_name):
    logger.info(f"\n--- {scenario_name} Scenario ---")
    # Create the LP model.
    model = LpProblem(f"Project_Scheduling_{scenario_name}", LpMinimize)
    
    # Set the start and completion times
    S = {task: LpVariable(f"Start_{task}", lowBound=0) for task in tasks}
    C = {task: LpVariable(f"Completion_{task}", lowBound=0) for task in tasks}
    
    # Define the objective function of minimizing the completion time of the project.
    model += C["H"], "Minimize_Project_Completion_Time"
    
    # Add the duration constraints.
    for task, duration in tasks.items():
        model += C[task] == S[task] + duration, f"Duration_{task}"
    
    # Add the dependency constraints.
    for task, prereqs in dependencies.items():
        for prereq in prereqs:
            model += S[task] >= C[prereq], f"Dep_{prereq}_to_{task}"
    
    # Solve the model.
    model.solve()
    logger.info("LP Status: " + LpStatus[model.status])
    
    # --- Calculate the Critical Path ---
    # Extract earliest start (ES) and finish (EF) times.
    schedule = {task: (S[task].varValue, C[task].varValue) for task in tasks}
    project_completion = schedule["H"][1]
    
    logger.info("Earliest Schedule (Start, Finish):")
    for task in sorted(tasks):
        es, ef = schedule[task]
        logger.info(f"  {task}: Start = {es}, Finish = {ef}")
    logger.info("Project Completion Time: " + str(project_completion))
    
    # Map the successors of each task.
    successors = {task: [] for task in tasks}
    for task, prereqs in dependencies.items():
        for p in prereqs:
            successors[p].append(task)
    
    # Perform Topological sort
    in_degree = {task: 0 for task in tasks}
    for task, prereqs in dependencies.items():
        in_degree[task] += len(prereqs)

    queue = [t for t in tasks if in_degree[t] == 0]
    topo_order = []
    while queue:
        t = queue.pop(0)  # Remove the first element of the list.
        topo_order.append(t)
        for succ in successors[t]:
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)
    
    # Perform backward pass to calculate latest start(LS) and latest finish(LF)
    LF = {}
    LS = {}
    for task in tasks:
        if not successors[task]:
            LF[task] = project_completion
    for task in reversed(topo_order):
        if task not in LF:  # For tasks with successors.
            LF[task] = min(LS[succ] for succ in successors[task])
        LS[task] = LF[task] - tasks[task]
    
    # Calculate the slack for each task.
    # Slack = LS - ES
    slack = {task: LS[task] - schedule[task][0] for task in tasks}
    
    logger.info("\nLatest Start (LS), Latest Finish (LF), and Slack:")
    for task in sorted(tasks):
        logger.info(f"  {task}: LS = {LS[task]}, LF = {LF[task]}, Slack = {slack[task]}")
    
    tol = 1e-5
    critical_tasks = [task for task in tasks if abs(slack[task]) < tol]
    logger.info("\nCritical Path:")
    logger.info("  " + " -> ".join(critical_tasks))
    
    # Calculate the total cost using hourly rate.
    total_cost, cost_by_task = compute_total_cost(tasks, worker_requirements, hourly_rate)
    logger.info("\nCost Details (per task):")
    for task in sorted(tasks):
        logger.info(f"  {task}: Cost = ${cost_by_task[task]:.2f}")
    logger.info("Total Project Cost: $" + str(total_cost))
    
    # Calculate the worker requirements for each role.
    peak_concurrency = compute_peak_concurrency(schedule, worker_requirements)
    logger.info("\nPeak Worker Requirements (by Role):")
    for role, count in peak_concurrency.items():
        logger.info(f"  {role}: {count} concurrent workers")
    
    return schedule, project_completion, critical_tasks

# Main function
def main():
    scenarios = {
        "Expected": tasks_expected,
        "Best": tasks_best,
        "Worst": tasks_worst
    }
    
    for scenario_name, task_durations in scenarios.items():
        compute_schedule_and_critical_path(task_durations, dependencies, scenario_name)
    
    logger.info("\nResults have been logged to 'project_schedule.log'.")

if __name__ == "__main__":
    main()
