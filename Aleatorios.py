import csv
import random

ROWS = 4
COLUMNS = 128
MIN_VALUE = 0.8
MAX_VALUE = 1.5

random_data = [
    [random.uniform(MIN_VALUE, MAX_VALUE) for _ in range(COLUMNS)]
    for _ in range(ROWS)
]

with open('aleatorios.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(random_data)
