import subprocess
import os
import re
import pickle

BenchDir = 'c_bench_term'

Commands = ['/usr/bin/time', '/usr/bin/timeout', \
    '120', './Ultimate.py', '--spec', 'Termination.prp', \
    '--architecture', '32bit', '--file']

results = []

for file in os.listdir(BenchDir):
    filePath = os.path.join(BenchDir, file)
    if not (os.path.isfile(filePath) and file.split('.')[-1] == 'c'):
        continue
    print(file[:-2])
    process = subprocess.Popen(Commands + [filePath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    stdoutStr = stdout.decode()
    stderrStr = stderr.decode()

    result = 'Timeout'
    if 'Result' in stdoutStr:
        result = stdoutStr.split('\n')[-2].strip()
    
    realtimeMatcher = re.search(r'(\d+):(\d+(\.\d+)?)elapsed', stderrStr)

    realtime = float(realtimeMatcher.group(1)) * 60 + float(realtimeMatcher.group(2))

    print(result, realtime)
    results.append((file[:-2], result, realtime))

fopen = open('Result_TO120.rst','wb')
pickle.dump(results, fopen)
fopen.close()


