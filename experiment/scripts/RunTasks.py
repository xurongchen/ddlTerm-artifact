from DataInfo import Le_Dir, NLe_Dir, Task_Info, Fixed_Seed, Tmp_Dir, Test_Dir
import sys
import os
import random
sys.path.append(os.path.abspath('code'))
from IceTerm import IceTerm #pylint: disable=import-error
from Logger import Logger #pylint: disable=import-error
import xml.etree.ElementTree as ET
import pickle
import datetime
import shutil
import subprocess, signal
from functools import reduce
import time


def kill_by_name(name):
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.decode().splitlines():
        if name in line:
            try:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)
                print(f'[Warning] Process {name}@{pid} found. Automatically killed.')
            except ProcessLookupError:
                ...
    # import pdb;pdb.set_trace()

def kill_related_process():
    for name in ['z3', 'mono', 'c5.0']:
        kill_by_name(name)


if len(sys.argv) == 1:
    raise RuntimeError('Please specify a strategy XML file.')

rootET = ET.parse(sys.argv[1]).getroot()
logLevel = 0
alwaysCompile = True
# import pdb; pdb.set_trace()
strategyList = []
Log_Lgs = None
Log_Excel = None
Log_Dir = os.getcwd()
print('[Info] Setting the strategy...')
for elem in rootET:
    if elem.tag == 'Name':
        print('[Info] Using strategy {}'.format(elem.text))
        continue
    elif elem.tag == 'Log':
        logLevel = int(elem.text)
        continue
    elif elem.tag == 'Log_Lgs':
        Log_Lgs = elem.text
    elif elem.tag == 'Log_Excel':
        Log_Excel = elem.text
    elif elem.tag == 'Log_Dir':
        Log_Dir = elem.text
    elif elem.tag == 'Tmp':
        # Use explicit tmp directory (Support fast tmpfs feature)
        tmpPath = elem.text
        if not os.path.isdir(tmpPath):
            raise RuntimeError(f'Cannot find the tmp directory {tmpPath}')
        Tmp_Dir = os.path.join(tmpPath, 'tmp')
        Test_Dir = os.path.join(tmpPath, 'test')
    elif elem.tag == 'Complie':
        if elem.text in ['Always', 'always', 'ALWAYS']:
            alwaysCompile = True
        else:
            alwaysCompile = False
    elif elem.tag == 'NLe' or elem.tag == 'Le':
        strategy = {}
        strategy['UseLexical'] = elem.tag == 'Le'
        # Default setting begin.
        strategy['Timeout'] = None
        strategy['TestRound'] = 100
        strategy['UseAdvancedCBC'] = True
        strategy['CBC_Limit'] = 30
        strategy['MLearnTarget'] = 'LSM_L2'
        # Default setting end.

        for setting in elem:
            if setting.tag in ['TestRound','CBC_Limit','TestLB','TestUB','TestNBLB',
                    'TestNBUB','TestNBRound','CBC_Advance','CBC_Advance_Limit',
                    'LexicalRankMin','LexicalRankMax','MLearnClusterNum', 'BMC_Limit']: # int
                try:
                    strategy[setting.tag] = int(setting.text)
                except ValueError:
                    raise RuntimeError('Unexpected int setting for {}'.format(setting.tag))
            
            elif setting.tag in ['MLearnTarget','LexicalStrategy','MLearnStrategy']: # str
                strategy[setting.tag] = setting.text
            
            elif setting.tag in ['UseAdvancedCBC','ErrorNearByTest']: # bool
                if setting.text in ['True', 'true', 'TRUE']:
                    strategy[setting.tag] = True
                elif setting.text in ['False', 'false', 'FALSE']:
                    strategy[setting.tag] = False
                else:
                    raise RuntimeError('Unexpected bool setting for {}'.format(setting.tag))
            elif setting.tag in ['Timeout']: # Noneable int
                if setting.text == 'None':
                    strategy[setting.tag] = None
                else:
                    try:
                        strategy[setting.tag] = int(setting.text)
                    except ValueError:
                        raise RuntimeError('Unexpected noneable int setting for {}'.format(setting.tag))
            else:
                raise RuntimeError('Unknown Tag: {}'.format(setting.tag))
        strategyList.append(strategy)



LogList = []
solvedNum = 0
runNum = 1
for bench in Task_Info:
    time.sleep(1)
    taskName = bench[0]
    print('[Info] Task {}'.format(taskName))
    variableInfo = '|'.join(bench[1])
    if variableInfo == '':
        variableInfo = '|'

    Commands = ['python3', 'experiment/scripts/ddlTerm.py', \
        '--name', taskName, \
        '--ledir', Le_Dir, \
        '--nledir', NLe_Dir, \
        '--vars', variableInfo, \
        '--conf', sys.argv[1], \
        '--log', f'single.{taskName}']

    process = subprocess.Popen(Commands, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    stdoutStr = stdout.decode()
    print(stdoutStr)

    Result = stdoutStr.split('\n')[-2].strip()
    
    if 'Termination' in Result:
        solvedNum += 1

    print('[Info] Solved: {}/{}'.format(solvedNum, runNum))
    runNum += 1
    conf_fopen = open( f'single.{taskName}.lgs','rb')
    benchLogList = pickle.load(conf_fopen)
    conf_fopen.close()
    os.remove(f'single.{taskName}.lgs')
    LogList.extend(benchLogList)

currentTime = datetime.datetime.now().strftime('%Y%m%d%H%M')
if Log_Lgs != None:
    Log_Lgs = Log_Lgs.replace('_TIME_',currentTime)
    fopen = open(os.path.join(Log_Dir, '{}.lgs'.format(Log_Lgs)),'wb')
    pickle.dump(LogList, fopen)
    fopen.close()

if Log_Excel != None:
    Log_Excel = Log_Excel.replace('_TIME_',currentTime)
    attrMakers = [
        ('Task', lambda x: x[0].Stat_Name),
        ('Result', lambda x: 'Termination' if x[-1].Stat_Result == 'Termination' else 'Failed'),
        ('RoB', lambda x: sum(map(lambda y: y.Stat_BoundRefineNum, x))),
        ('RoI_Total', lambda x: sum(map(lambda y: sum(y.Stat_InvRefineNumList), x))),
        ('RoI_Max', lambda x: max(map(lambda y: max([0] + y.Stat_InvRefineNumList), x))),
        ('T_Total', lambda x: sum(map(lambda y: y.Stat_TotalTime, x))),
        ('ToT_Total', lambda x: sum(map(lambda y: sum(y.Stat_TestTimeList), x))),
        ('ToT_Max', lambda x: max(map(lambda y: max([0] + y.Stat_TestTimeList), x))),
        ('ToB_Total', lambda x: sum(map(lambda y: sum(y.Stat_BoundTimeList), x))),
        ('ToB_Max', lambda x: max(map(lambda y: max([0] + y.Stat_BoundTimeList), x))),
        ('ToI_Total', lambda x: sum(map(lambda y: sum(y.Stat_InvTimeList), x))),
        ('ToI_Max', lambda x: max(map(lambda y: max([0] + y.Stat_InvTimeList), x))),
        ('ToC_Total', lambda x: sum(map(lambda y: sum(y.Stat_CBCTimeList), x))),
        ('ToC_Max', lambda x: max(map(lambda y: max([0] + y.Stat_CBCTimeList), x))),
        ('ToM_Total', lambda x: sum(map(lambda y: sum(y.Stat_BMCTimeList), x))),
        ('ToM_Max', lambda x: max(map(lambda y: sum(y.Stat_BMCTimeList), x))),
        ('FinalInv', lambda x: x[-1].Stat_FinalInv),
        ('FinalBound', lambda x: x[-1].Stat_FinalBound),
        ('SizeC', lambda x: x[0].Stat_CFileSize),
        ('SizeBpl', lambda x: x[0].Stat_BplFileSize),
        ('RoB:ICE', lambda x: len(list(filter(lambda t:t>0, reduce(lambda z,r: z+r, map(lambda y: y.Stat_InvTimeList, x), []))))),
        ('RoB:BMC', lambda x: len(list(filter(lambda t:t>0, reduce(lambda z,r: z+r, map(lambda y: y.Stat_BMCTimeList, x), []))))),
        ('RoB:CBC', lambda x: len(list(filter(lambda t:t>0, reduce(lambda z,r: z+r, map(lambda y: y.Stat_CBCTimeList, x), []))))),
    ]

    Logger.Export2Excel(LogList, attrMakers, os.path.join(Log_Dir, '{}.xlsx'.format(Log_Excel)))




