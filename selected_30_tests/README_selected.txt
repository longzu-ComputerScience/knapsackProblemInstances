Selected 30 knapsack test cases

Files:
- testXX.txt: input instance in test.in format.
- answerXX.out: expected optimal output copied from outp.out.
- timeXX.out: solve time from combo in seconds; -1 means timeout or failure.
- mapping.txt: source folder for each copied file.
- summary.csv: one-row summary per selected test case.

Input format:
line 1: number of items n
next n lines: id profit weight
last line: knapsack capacity

Answer format:
line 1: optimal total profit
remaining lines: selected items as profit weight
