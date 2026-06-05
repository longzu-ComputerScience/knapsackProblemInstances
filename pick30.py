from pathlib import Path
import shutil
import re
import csv
from collections import defaultdict

SRC = Path("problemInstances")
DST = Path("selected_30_tests")
TOTAL_TESTS = 30
PARAMS = ("c", "g", "f", "eps", "s")
DEMO_TESTS = [
    {
        "capacity": 10,
        "items": [
            (1, 10, 5),
            (2, 40, 4),
            (3, 30, 6),
            (4, 50, 3),
            (5, 35, 7),
        ],
    },
    {
        "capacity": 15,
        "items": [
            (1, 12, 4),
            (2, 10, 6),
            (3, 20, 5),
            (4, 15, 7),
            (5, 25, 8),
            (6, 30, 9),
        ],
    },
    {
        "capacity": 18,
        "items": [
            (1, 14, 3),
            (2, 18, 5),
            (3, 24, 6),
            (4, 30, 9),
            (5, 11, 4),
            (6, 35, 10),
            (7, 28, 8),
        ],
    },
    {
        "capacity": 20,
        "items": [
            (1, 15, 4),
            (2, 22, 6),
            (3, 14, 5),
            (4, 31, 8),
            (5, 40, 11),
            (6, 18, 7),
            (7, 27, 9),
            (8, 12, 3),
        ],
    },
    {
        "capacity": 25,
        "items": [
            (1, 20, 5),
            (2, 18, 4),
            (3, 35, 9),
            (4, 40, 10),
            (5, 12, 3),
            (6, 28, 7),
            (7, 50, 13),
            (8, 24, 6),
            (9, 16, 4),
            (10, 30, 8),
        ],
    },
]

if DST.exists():
    shutil.rmtree(DST)

DST.mkdir()

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


def write_demo_test(case_dir, demo):
    items = demo["items"]
    capacity = demo["capacity"]
    best_profit = -1
    best_weight = 0
    best_items = []

    for mask in range(1 << len(items)):
        chosen = [item for index, item in enumerate(items) if mask & (1 << index)]
        total_profit = sum(item[1] for item in chosen)
        total_weight = sum(item[2] for item in chosen)

        if total_weight > capacity:
            continue

        if (
            total_profit > best_profit
            or (total_profit == best_profit and total_weight < best_weight)
        ):
            best_profit = total_profit
            best_weight = total_weight
            best_items = chosen

    with open(case_dir / "test.in", "w") as file:
        file.write(f"{len(items)}\n")

        for item_id, profit, weight in items:
            file.write(f"{item_id} {profit} {weight}\n")

        file.write(f"{capacity}\n")

    with open(case_dir / "answer.out", "w") as file:
        file.write(f"{best_profit}\n")

        for _, profit, weight in best_items:
            file.write(f"{profit} {weight}\n")

    with open(case_dir / "time.out", "w") as file:
        file.write("0.000000\n")

    return best_profit


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

        case_id = f"test{i:02d}"
        case_dir = DST / case_id
        case_dir.mkdir()

        test_source = instance / "test.in"
        answer_source = instance / "outp.out"
        time_source = instance / "time.out"

        if not answer_source.is_file() or not time_source.is_file():
            raise RuntimeError(f"Missing output files for {instance.name}")

        shutil.copyfile(test_source, case_dir / "test.in")
        shutil.copyfile(answer_source, case_dir / "answer.out")
        shutil.copyfile(time_source, case_dir / "time.out")

        mp.write(
            f"{case_id}/test.in <- {instance.name}/test.in\n"
            f"{case_id}/answer.out <- {instance.name}/outp.out\n"
            f"{case_id}/time.out <- {instance.name}/time.out\n"
            "\n"
        )

        summary_rows.append({
            "category": "selected",
            "index": i,
            "case_dir": case_id,
            "test_file": f"{case_id}/test.in",
            "answer_file": f"{case_id}/answer.out",
            "time_file": f"{case_id}/time.out",
            "source_instance": instance.name,
            "optimal_profit": first_line(answer_source),
            "combo_time_seconds": first_line(time_source),
        })

demo_root = DST / "demo_tests"
demo_root.mkdir()

with open(DST / "mapping.txt", "a") as mp:
    mp.write("Demo tests generated by pick30.py\n\n")

    for i, demo in enumerate(DEMO_TESTS, start=1):
        case_id = f"demo{i:02d}"
        case_dir = demo_root / case_id
        case_dir.mkdir()

        optimal_profit = write_demo_test(case_dir, demo)

        mp.write(
            f"demo_tests/{case_id}/test.in <- generated demo case\n"
            f"demo_tests/{case_id}/answer.out <- generated optimal answer\n"
            f"demo_tests/{case_id}/time.out <- not measured; placeholder 0.000000\n"
            "\n"
        )

        summary_rows.append({
            "category": "demo",
            "index": i,
            "case_dir": f"demo_tests/{case_id}",
            "test_file": f"demo_tests/{case_id}/test.in",
            "answer_file": f"demo_tests/{case_id}/answer.out",
            "time_file": f"demo_tests/{case_id}/time.out",
            "source_instance": "generated_demo",
            "optimal_profit": optimal_profit,
            "combo_time_seconds": "0.000000",
        })

with open(DST / "summary.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=summary_rows[0].keys())
    writer.writeheader()
    writer.writerows(summary_rows)

with open(DST / "README_selected.txt", "w") as file:
    file.write(
        "Selected 30 knapsack test cases\n"
        "\n"
        "Folder structure:\n"
        "- testXX/test.in: input instance in test.in format.\n"
        "- testXX/answer.out: expected optimal output copied from outp.out.\n"
        "- testXX/time.out: solve time from combo in seconds; -1 means timeout or failure.\n"
        "- demo_tests/demoXX/test.in: small generated input for demo videos.\n"
        "- demo_tests/demoXX/answer.out: optimal answer for the demo input.\n"
        "- demo_tests/demoXX/time.out: placeholder 0.000000, not benchmarked by combo.\n"
        "- mapping.txt: source folder for each copied file.\n"
        "- summary.csv: one-row summary per test case.\n"
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
print("Demo:", len(DEMO_TESTS))
print("Output folder:", DST)
