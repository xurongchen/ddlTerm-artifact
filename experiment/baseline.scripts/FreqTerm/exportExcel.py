import os
import subprocess
import re
import pickle
import functools
import xlsxwriter

resultFile = 'Result_bench-term_TO120_B_All.rst'
outPutXlsx = 'Result_bench-term_TO120_B_All_Single.xlsx'

with open(resultFile, 'rb') as fopen:
    result = pickle.load(fopen)

benchmarks = set()
configs = []
for config in result.keys():
    benchmarks = benchmarks | set(result[config])
    configs.append(config)
benchmarks = list(benchmarks)

wb = xlsxwriter.Workbook(outPutXlsx)
ws = wb.add_worksheet()
row = 0
col = 0
ws.write(row, col, 'Bench')
col += 1
for c in configs:
    ws.write(row, col, 'R:{}'.format(c))
    col += 1
    ws.write(row, col, 'T:{}'.format(c))
    col += 1

row += 1
for b in benchmarks:
    col = 0
    name = b.split('/')[-1]
    if name.endswith('.smt'):
        name= name[:-4]
    elif name.endswith('.smt2'):
        name= name[:-5]
    ws.write(row, col, name)
    col += 1
    for c in configs:
        ws.write(row, col, 'Timeout' if result[c][b][1] - 60 > -0.05 and result[c][b][0] == 'Unknown' else result[c][b][0])
        col += 1
        ws.write(row, col, result[c][b][1])
        col += 1
    row += 1
wb.close()
