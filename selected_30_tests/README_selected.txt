Selected 30 knapsack test cases

Folder structure:
- testXX/test.in: input instance in test.in format.
- testXX/answer.out: expected optimal output copied from outp.out.
- testXX/time.out: solve time from combo in seconds; -1 means timeout or failure.
- demo_tests/demoXX/test.in: small generated input for demo videos.
- demo_tests/demoXX/answer.out: optimal answer for the demo input.
- demo_tests/demoXX/time.out: placeholder 0.000000, not benchmarked by combo.
- mapping.txt: source folder for each copied file.
- summary.csv: one-row summary per test case.

Input format:
line 1: number of items n
next n lines: id profit weight
last line: knapsack capacity

Answer format:
line 1: optimal total profit
remaining lines: selected items as profit weight
