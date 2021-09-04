import subprocess
import os
import re
import pickle
import xlsxwriter

fopen = open('Result_TO120_noS2.rst','rb')
loggers = pickle.load(fopen)
fopen.close()

attrMakers = [
    ('Benchmark', lambda x: x[0]),
    ('Result', lambda x: x[1]),
    ('Time', lambda x: x[2]),
    ]

outputFile = "APROVE_Single.xlsx"
wb = xlsxwriter.Workbook(outputFile)
ws = wb.add_worksheet()
row = 0
col = 0
for a in attrMakers:
    ws.write(row, col, a[0])
    col += 1
row += 1
for l in loggers:
    col = 0
    for a in attrMakers:
        ws.write(row, col, a[1](l))
        col += 1
    row += 1
wb.close()
