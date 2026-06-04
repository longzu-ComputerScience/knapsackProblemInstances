from pathlib import Path
import shutil
import re
import csv
from collections import defaultdict

SRC = Path("problemInstances")
DST = Path("selected_30_tests")
TOTAL_TESTS = 30
PARAMS = ("c", "g", "f", "eps", "s")

DST.mkdir(exist_ok=True)

all_instances = [
    d for d in SRC.iterdir()
    if d.is_dir() and (d / "test.in").is_file()
]
all_instances.sort(key=lambda x: x.name)


def param_value(name, param):
    match = re.search(rf"(?:^|_){param}_([^_]+)", name)
    return match.group(1) if match else None


def int_param(name, param):
    value = param_value(name, param)
    return int(value) if value is not None else None


def numeric_key(value):
    return float(value)


def instance_params(instance):
    return tuple(param_value(instance.name, param) for param in PARAMS)


def first_line(path):
    with open(path, "r") as file:
        return file.readline().strip()


groups_by_n = defaultdict(list)

for instance in all_instances:
    n = int_param(instance.name, "n")

    if n is not None:
        groups_by_n[n].append(instance)

if not groups_by_n:
    raise RuntimeError("No problem instances found. Expected subfolders containing test.in.")

if len(all_instances) < TOTAL_TESTS:
    raise RuntimeError(f"Only found {len(all_instances)} problem instances.")

for instances in groups_by_n.values():
    instances.sort(key=lambda x: x.name)

param_values = {
    param: sorted(
        {
            param_value(instance.name, param)
            for instance in all_instances
            if param_value(instance.name, param) is not None
        },
        key=numeric_key,
    )
    for param in PARAMS
}

param_indexes = {
    param: {value: index for index, value in enumerate(values)}
    for param, values in param_values.items()
}


def distance_to_target(instance, target):
    distance = 0.0

    for param, target_value in zip(PARAMS, target):
        values = param_values[param]
        span = max(len(values) - 1, 1)
        instance_value = param_value(instance.name, param)

        distance += (
            (param_indexes[param][instance_value] - param_indexes[param][target_value])
            / span
        ) ** 2

    return distance


def select_diverse(instances, k, offset):
    if len(instances) <= k:
        return instances

    by_params = {instance_params(instance): instance for instance in instances}
    selected = []
    used = set()

    for i in range(k):
        target = tuple(
            param_values[param][(i + offset) % len(param_values[param])]
            for param in PARAMS
        )
        candidate = by_params.get(target)

        if candidate is None or candidate.name in used:
            candidate = min(
                (instance for instance in instances if instance.name not in used),
                key=lambda instance: (distance_to_target(instance, target), instance.name),
            )

        selected.append(candidate)
        used.add(candidate.name)

    return selected

quotas = {n: 0 for n in groups_by_n}
remaining = TOTAL_TESTS

while remaining > 0:
    progressed = False

    for n in sorted(groups_by_n):
        if quotas[n] < len(groups_by_n[n]):
            quotas[n] += 1
            remaining -= 1
            progressed = True

            if remaining == 0:
                break

    if not progressed:
        break

selected = []

for offset, n in enumerate(sorted(groups_by_n)):
    selected.extend(select_diverse(groups_by_n[n], quotas[n], offset))

if len(selected) != TOTAL_TESTS:
    raise RuntimeError(f"Expected {TOTAL_TESTS} tests, got {len(selected)}")

summary_rows = []

with open(DST / "mapping.txt", "w") as mp:

    for i, instance in enumerate(selected, start=1):

        test_name = f"test{i:02d}.txt"
        answer_name = f"answer{i:02d}.out"
        time_name = f"time{i:02d}.out"

        test_source = instance / "test.in"
        answer_source = instance / "outp.out"
        time_source = instance / "time.out"

        if not answer_source.is_file() or not time_source.is_file():
            raise RuntimeError(f"Missing output files for {instance.name}")

        shutil.copyfile(test_source, DST / test_name)
        shutil.copyfile(answer_source, DST / answer_name)
        shutil.copyfile(time_source, DST / time_name)

        mp.write(
            f"{test_name} <- {instance.name}/test.in\n"
            f"{answer_name} <- {instance.name}/outp.out\n"
            f"{time_name} <- {instance.name}/time.out\n"
            "\n"
        )

        summary_rows.append({
            "index": i,
            "test_file": test_name,
            "answer_file": answer_name,
            "time_file": time_name,
            "source_instance": instance.name,
            "optimal_profit": first_line(answer_source),
            "combo_time_seconds": first_line(time_source),
        })

with open(DST / "summary.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=summary_rows[0].keys())
    writer.writeheader()
    writer.writerows(summary_rows)

with open(DST / "README_selected.txt", "w") as file:
    file.write(
        "Selected 30 knapsack test cases\n"
        "\n"
        "Files:\n"
        "- testXX.txt: input instance in test.in format.\n"
        "- answerXX.out: expected optimal output copied from outp.out.\n"
        "- timeXX.out: solve time from combo in seconds; -1 means timeout or failure.\n"
        "- mapping.txt: source folder for each copied file.\n"
        "- summary.csv: one-row summary per selected test case.\n"
        "\n"
        "Input format:\n"
        "line 1: number of items n\n"
        "next n lines: id profit weight\n"
        "last line: knapsack capacity\n"
        "\n"
        "Answer format:\n"
        "line 1: optimal total profit\n"
        "remaining lines: selected items as profit weight\n"
    )

print("Done.")
print("Selected:", len(selected))
print("Output folder:", DST)
