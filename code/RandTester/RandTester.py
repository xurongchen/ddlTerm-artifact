import os
import subprocess
import re
import random
from functools import reduce, partial
import sys
sys.path.append(os.path.abspath('code'))
from StateTrans import TraceStateTrans #pylint: disable=import-error
from StateTrans.TraceStateTrans import * #pylint: disable=import-error

class RandTester:
    def __init__(self, logger, vars, exec, args=[]):
        self.Logger = logger
        self.Vars = vars
        self.Exec = exec
        self.Args = args
        self.DEFAULT_INF_VALUE = 1000
        self.MAX_SAMPLE_ONCE = 25
        
        

    
    def randFunction(self, strategy='naive', lb='inf', ub='inf', nearby=0):
        def naiveRand():
            randValues = []
            for item in range(len(self.Vars)):
                itemLb = lb if type(lb) not in (tuple, list) else itemLb[item]
                itemUb = ub if type(ub) not in (tuple, list) else itemUb[item]
                itemLb = itemLb if itemLb != 'inf' else - self.DEFAULT_INF_VALUE
                itemUb = itemUb if itemUb != 'inf' else self.DEFAULT_INF_VALUE

                randValues.append(random.randint(itemLb, itemUb))
            return randValues
        def nearbyRand():
            randValues = []
            for item in range(len(self.Vars)):
                nbValue = nearby if type(nearby) not in (tuple, list) else nearby[item]
                itemLb = lb if type(lb) not in (tuple, list) else itemLb[item]
                itemUb = ub if type(ub) not in (tuple, list) else itemUb[item]
                itemLb = nbValue + itemLb if itemLb != 'inf' else - self.DEFAULT_INF_VALUE
                itemUb = nbValue + itemUb if itemUb != 'inf' else self.DEFAULT_INF_VALUE
                if itemLb > itemUb:
                    raise ValueError('The lower bound is greater than the upper bound!')

                # print('[Debug]item={},{}-{}'.format(item,itemLb,itemUb))
                randValues.append(random.randint(itemLb, itemUb))
            return randValues
        if strategy == 'naive':
            return naiveRand
        elif strategy == 'nearby':
            return nearbyRand

    def executeTest(self, randFunc, require=None, option='default'):
        # print('[Debug] in')
        process = subprocess.Popen(
            [self.Exec] + self.Args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # print('[Debug] out')
        if len(self.Vars) > 0:
            stdout, _ = process.communicate(input=str(reduce(
                lambda x, y: '{} {}'.format(x, y), randFunc())).encode())
        else:
            stdout, _ = process.communicate()
        stdout = stdout.decode()
        if stdout == '':
            return []
        if not stdout.startswith('[Testing]'): # No interface version info
            print("[Warning] No testing interface info!")
            return [list(map(int, stdout.split(',')))]
        
        reMatcher = r'\[Testing\] <Interface V(.*)\.(.*)>(.*)'
        versionResult = re.search(reMatcher, stdout.splitlines()[0])
        if versionResult is None:
            raise IOError('Version unknown!')
        versionLarge = versionResult.group(1)
        versionSmall = versionResult.group(2)
        if require != None and not require(versionLarge, versionSmall):
            raise RuntimeError('Test requirement is not satisfied!')
        if versionLarge == '2':
            dataTrace = []
            stdLines = stdout.splitlines()[1:]
            for line in stdLines:
                modifiedline = line.replace(' ','').replace('\n','').replace('\t','').replace('\r','')
                if modifiedline == '':
                    continue
                if len(self.Vars) == 0: # No test input
                    dataTrace.append([])
                    continue
                dataTrace.append(list(map(int, modifiedline.split(','))))
            dataTraceLen = len(dataTrace)
            
            for i in range(dataTraceLen):
                dataTrace[i].append(dataTraceLen - i)
            
            # Set Maximun number of samples in one test, making the sample number not too large
            if dataTraceLen > self.MAX_SAMPLE_ONCE and self.MAX_SAMPLE_ONCE != 0:
                SampleDistance = dataTraceLen // self.MAX_SAMPLE_ONCE
            else:
                return dataTrace

            SelectedDataTrace = []
            for it in range(dataTraceLen):
                if it % SampleDistance == 0:
                    SelectedDataTrace.append(dataTrace[it])
            
            return SelectedDataTrace
        elif versionLarge == '3' and versionSmall == '0TR':
            if option == 'trace':
                return TraceStates.TestResult2TraceV3_0(stdout.splitlines(), self.Vars)  #pylint: disable=undefined-variable
            dataTrans = TraceStateTrans.TestResult2DataV3_0(stdout.splitlines(), self.Vars, logger=self.Logger)
            return dataTrans
        elif versionLarge == '4' and versionSmall == '0':
            dataList, infoDictList = TraceStates.TestResult2V4_0(stdout.splitlines(), self.Vars, self)  #pylint: disable=undefined-variable
            if len(infoDictList) > 0:
                self.Logger.TestDataInfo.append(infoDictList)
            return dataList
        elif versionLarge == '4' and versionSmall == '0TR':
            if not option == 'trace':
                raise NotImplementedError('Unsupported version configuration.')
            ts, infoDictList = TraceStates.TestResult2TraceV4_0(stdout.splitlines(), self.Vars)  #pylint: disable=undefined-variable
            self.Logger.TestDataInfo.append(infoDictList)
            return ts
        else:
            raise NotImplementedError('Unsupported testing version.')

    # Use return value as data. (Different from 'generateBound')
    # The return value is a list of class TraceStateTrans
    def generateBoundLexical(self, randFunc, mode='round', round='default', number='default', maxRound='default', duplicate=True, testOption='default'):
        returnData = []
        if mode == 'round':
            if round == 'default':
                round = 100
            if maxRound == 'default':
                maxRound = round * 10

            roundK = 0
            roundTry = 0
            while roundK < round and roundTry < maxRound:
                roundTry += 1
                ret = self.executeTest(randFunc, require=lambda l,s: 'TR' in s, option=testOption)
                if type(ret) == TraceStates and len(ret.States) == 0: #pylint: disable=undefined-variable
                    continue
                if type(ret) != TraceStates and len(ret) == 0: #pylint: disable=undefined-variable
                    continue
                returnData += [ret]
                roundK += 1
        elif mode == 'number':
            if number == 'default':
                number = 100
            if maxRound == 'default':
                maxRound = number * 10

            numberK = 0
            roundTry = 0
            while numberK < number and roundTry < maxRound:
                roundTry += 1
                ret = self.executeTest(randFunc, require=lambda l,s: 'TR' in s, option=testOption)
                if type(ret) == TraceStates and len(ret.States) == 0: #pylint: disable=undefined-variable
                    continue
                if type(ret) != TraceStates and len(ret) == 0: #pylint: disable=undefined-variable
                    continue
                returnData += [ret]
                numberK += len(ret)

        if not duplicate:
            returnData = list(set(returnData))
        return returnData

    def generateBound(self, randFunc, mode='round', round='default', number='default', maxRound='default', duplicate=True, outputFile='bound.csv'):
        content = ''
        for item in self.Vars:
            content += '{},'.format(item)
        content += 'r\n'

        if mode == 'round':

            if round == 'default':
                round = 100
            if maxRound == 'default':
                maxRound = round * 10

            visDict = {}
            roundK = 0
            roundTry = 0
            while roundK < round and roundTry < maxRound:
                roundTry += 1
                ret = self.executeTest(randFunc, require=lambda l,s: 'TR' not in s)
                if len(ret) == 0:
                    continue

                for retline in ret:
                    if not duplicate and tuple(retline) in visDict.keys():
                        continue
                    if not duplicate:
                        visDict[tuple(retline)] = True
                    firstVar = True
                    for item in retline:
                        if firstVar:
                            content += '{}'.format(item)
                            firstVar = False
                        else:
                            content += ',{}'.format(item)
                    content += '\n'
                roundK += 1

        elif mode == 'number':
            if number == 'default':
                number = 100
            if maxRound == 'default':
                maxRound = number * 10

            visDict = {}
            numberK = 0
            roundTry = 0
            while numberK < number and roundTry < maxRound:
                roundTry += 1
                ret = self.executeTest(randFunc, require=lambda l,s: 'TR' not in s)
                if len(ret) == 0:
                    continue

                for retline in ret:
                    if not duplicate and tuple(retline) in visDict.keys():
                        continue
                    if not duplicate:
                        visDict[tuple(retline)] = True
                    firstVar = True
                    for item in retline:
                        if firstVar:
                            content += '{}'.format(item)
                            firstVar = False
                        else:
                            content += ',{}'.format(item)
                    content += '\n'
                    numberK += 1
        
        fw = open(outputFile, 'w')
        fw.write(content)
        fw.close()


