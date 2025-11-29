import random

# heads_total = 0
# tails_total = 0

# for i in range(10**6):
# 	a = random.randint(0, 1)
# 	if a == 1:
# 		heads_total += 1
# 	elif a == 0:
# 		tails_total += 1

# print(f"{heads_total=}")
# print(f"{tails_total=}")

# prob_heads = heads_total / (heads_total + tails_total)
# prob_tails = tails_total / (heads_total + tails_total)

# print(f"{prob_heads=}")
# print(f"{prob_tails=}")

# print(f"sum: {prob_heads + prob_tails}")

counts = dict()

for i in range(1000):
	a = random.randint(1, 6) # 1, 2, 3, 4, 5, 6
	counts[a] = counts.get(a, 0) + 1

# print(f"{counts=}")
events_total = sum([v for k, v in counts.items()])
print(f"{events_total=}")

sum_of_probas = 0.
for k, v in counts.items():
	proba = v / events_total
	print(f"{k} : {v}		{proba=}")
	sum_of_probas += proba

print(f"{sum_of_probas=}")
