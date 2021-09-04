import argparse
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


parser = argparse.ArgumentParser(description='ddlTerm')

parser.add_argument("--name")
parser.add_argument("--ledir")
parser.add_argument("--nledir")
parser.add_argument("--seed", default=888)
parser.add_argument("--tmp", default="tmp")
parser.add_argument("--test", default="test")
parser.add_argument("--vars")
parser.add_argument("--conf")
parser.add_argument("--log", default=None)
parser.add_argument("--excel", default=None)

args = parser.parse_args()
task_name = args.name
task_ledir = args.ledir
task_nledir = args.nledir
task_seed = int(args.seed)
task_tmp = args.tmp
task_vars = args.vars
task_test = args.test
task_conf = args.conf
task_log = args.log
task_excel = args.excel

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


rootET = ET.parse(task_conf).getroot()
logLevel = 0
alwaysCompile = True
# import pdb; pdb.set_trace()
strategyList = []

print('[Info] Setting the strategy...')
for elem in rootET:
    if elem.tag == 'Name':
        print('[Info] Using strategy {}'.format(elem.text))
        continue
    elif elem.tag == 'Log':
        logLevel = int(elem.text)
    elif elem.tag == 'Tmp':
        # Use explicit tmp directory (Support fast tmpfs feature)
        tmpPath = elem.text
        if not os.path.isdir(tmpPath):
            raise RuntimeError(f'Cannot find the tmp directory {tmpPath}')
        task_tmp = os.path.join(tmpPath, task_tmp)
        task_test = os.path.join(tmpPath, task_test)
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

if os.path.exists(task_tmp):
    shutil.rmtree(task_tmp)
    os.mkdir(task_tmp)

if os.path.exists(task_test):
    shutil.rmtree(task_test)
    os.mkdir(task_test)

# solvedNum = 0
# runNum = 1
LogList = []

taskName = task_name
print('[Info] Running the task {}...'.format(taskName))
if task_vars == '|':
    variableInfo = []
else:
    variableInfo = list(task_vars.split('|'))
benchLogList = []
Result = 'Failed'
for strategy in strategyList:
    random.seed(task_seed)
    if strategy['UseLexical']:
        benchDir = task_ledir
    else:
        benchDir = task_nledir

    taskBplPath = os.path.join(benchDir, taskName, '{}.bpl'.format(taskName))
    taskCPath = os.path.join(benchDir, taskName, '{}.c'.format(taskName))
    taskOPath = os.path.join(benchDir, taskName, '{}.o'.format(taskName))
    
    if not os.path.exists(taskOPath) or alwaysCompile:
        if os.path.exists(taskCPath):
            print('[Info] C File find! Trying make compilation...')
            # print('[Info] => Run cmd: {}'.format('g++ {} -o {}'.format(taskCPath, taskOPath)))
            ret = os.popen('g++ {} -o {}'.format(taskCPath, taskOPath))
            retvalue = ret.read()
            if not retvalue.strip() == '':
                print(retvalue)
            print('[Info] => Compile success!')
        else:
            raise RuntimeError('Compile failed in {}'.format(taskName))
    
    logger = Logger(printLevel=logLevel)
    logger.LogStatistic()
    it = IceTerm(taskName, task_tmp, taskBplPath, taskOPath, variableInfo, task_test, logger=logger, timeout=strategy['Timeout'])

    for k in strategy.keys():
        if k == 'Timeout':
            continue
        setattr(it, k, strategy[k])
    try:
        it.checkTermination()
        logger.FormatBound()
    except RuntimeError:
        logger.Stat_Result = "Runtime Error"
    
    benchLogList.append(logger)
    print('[Info] => Sub-Result: {}'.format(logger.Stat_Result))

    if logger.Stat_Result == 'Termination':
        Result = 'Termination'
        print('[Info] Bound is:', logger.Stat_FinalBound)
        print('[Info] Inv is:', logger.Stat_FinalInv)
        break
    else:
        ...
    # Kill unstopped process
    kill_related_process()
    # Trying next strategy

print('[Info] Result: {} ({:3f} s)'.format(Result, sum(map(lambda y: y.Stat_TotalTime, benchLogList))))
# if Result == 'Termination':
#     solvedNum += 1

# print('[Info] Solved: {}/{}'.format(solvedNum, runNum))
# runNum += 1
LogList.append(benchLogList)

currentTime = datetime.datetime.now().strftime('%Y%m%d%H%M')
if task_log != None:
    Log_Lgs = task_log.replace('_TIME_',currentTime)
    fopen = open('{}.lgs'.format(Log_Lgs),'wb')
    pickle.dump(LogList, fopen)
    fopen.close()

if task_excel != None:
    Log_Excel = task_excel.replace('_TIME_',currentTime)
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

    Logger.Export2Excel(LogList, attrMakers, '{}.xlsx'.format(Log_Excel))

