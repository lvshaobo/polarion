import csv

"""
cases = []
with open('failed_result.csv') as fcsv:
    for row in fcsv.readlines():
        cases.append(row)

print(cases[:5])
"""
cases = []
with open('failed_result.csv') as fcsv:
    for row in csv.reader(fcsv):
        cases.append(row)

print(cases[:5])
