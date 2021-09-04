import os
import subprocess
import re
import pickle
import functools

def RunBench(benchPath, rank, nonterm, solver='freqhorn', timeout=60):
    Args = ['/usr/bin/time', '/usr/bin/timeout', str(timeout), './term', benchPath, '--nonterm', str(nonterm), '--rank', str(rank), '--solver', solver]
    # print(functools.reduce(lambda x,y: '{} {}'.format(x, y), Args))
    process = subprocess.Popen(Args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdoutDecode = stdout.decode()
    stderrDecode = stderr.decode()
    output = stdoutDecode + stderrDecode
    # print(output)
    realtimeMatcher = re.search(r'(\d+):(\d+(\.\d+)?)elapsed', output)
    realtime = float(realtimeMatcher.group(1)) * 60 + float(realtimeMatcher.group(2))
    if '---> Terminates!' in output:
        return 'Termination', realtime
    else:
        return 'Unknown', realtime
        

testDirList = [
    # 'bench_horn', 
    # 'bench_horn_cex', 
    # 'bench_horn_multiple',
    # 'bench_nonterm',
    'bench_term',
    # 'bench_test',
    # 'kind-bench',
    # 'kind-expr'
    ]

# Just verify the termination programs
# SetBench = set()
# SetBench_rank1 = dict()
# SetBench_rank2 = dict()

curDir = os.path.abspath('.')
solvers = ['spacer', 'freqhorn', 'muz']
# solvers = ['muz']
# ranks = [1,2]
ranks = [3]
result = dict()
for s in solvers:
    for r in ranks:
        tn = s + 'R{}'.format(r)
        result[tn] = dict()

for d in testDirList:
    dirPath = os.path.join(curDir, d)
    files = os.listdir(dirPath)
    for f in files:
        fPath = os.path.join(dirPath, f)
        if os.path.isfile(fPath) and f.split('.')[-1] in ('smt', 'smt2'):
            print('Running benchmark', fPath)
            # SetBench.add(fPath)
            for s in solvers:
                for r in ranks:
                    outcome, runtime = RunBench(fPath, r, 0, s, 120)
                    tn = s + 'R{}'.format(r)
                    result[tn][fPath] = (outcome, runtime)

                    print('Rank {} Solver {}: {} in {}s'.format(r,s, outcome, runtime))



fopen = open('Result_bench-term_TO120_B_All.rst','wb')
pickle.dump(result, fopen)
fopen.close()

# solved1 = set(filter(lambda x: x == 'Termination', SetBench_rank1))
# solved2 = set(filter(lambda x: x == 'Termination', SetBench_rank2))

# print(solved2 - solved1)
