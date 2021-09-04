import os
from MLearner.MLearn import MLearn #pylint: disable=import-error
from IceCaller.IceCaller import IceCaller #pylint: disable=import-error
from CBChecker.CBChecker import CBChecker #pylint: disable=import-error
from BG0Checker.BG0Checker import BG0Checker #pylint: disable=import-error
from BMCFinder.BMCFinder import BMCFinder #pylint: disable=import-error
from RandTester.RandTester import RandTester #pylint: disable=import-error
from ErrorFinder.ErrorFinder import ErrorFinder #pylint: disable=import-error
from functools import reduce
from Logger import Logger #pylint: disable=import-error
from StateTrans import TraceStateTrans #pylint: disable=import-error
from StateTrans.TraceStateTrans import * #pylint: disable=import-error
import numpy as np
import shutil
class IceTerm:

    def __init__(self, taskName, tmpDir, templateBpl, execFile, varList, testRoundDir='test', mLearnFile='mData', iterateVar='i',roundVar='r', IceLearner='dt_penalty', logger = Logger(), timeout=None, clearTmp=False):

        self.projectDir = '/'.join(os.getcwd().split('/'))
        self.IceLearner = IceLearner
        getAbsPath = lambda path: os.path.join(self.projectDir, path)
        self.TaskName = taskName
        self.TmpDir = getAbsPath(tmpDir)
        if clearTmp and os.path.exists(self.TmpDir):
            shutil.rmtree(self.TmpDir)
        if not os.path.exists(self.TmpDir):
            os.mkdir(self.TmpDir)
        self.TemplateBpl = getAbsPath(templateBpl)
        self.ExecFile = getAbsPath(execFile)
        self.VarList = varList
        self.TestRoundDir = getAbsPath(testRoundDir)
        if clearTmp and os.path.exists(self.TestRoundDir):
            shutil.rmtree(self.TestRoundDir)
        if not os.path.exists(self.TestRoundDir):
            os.mkdir(self.TestRoundDir)
        self.MLearnFile = os.path.join(self.TestRoundDir, 'TEST_{}_{}.csv'.format(self.TaskName, mLearnFile))

        # Init test setting
        self.TestID = 1000
        self.TestRound = 10
        self.TestLB = -10
        self.TestUB = 10

        # Mutation test setting 
        self.TestNBLB = -5
        self.TestNBUB = 5
        self.TestNBRound = 3
        # self.TestNBRound = 0

        self.IterateVar = iterateVar
        self.RoundVar = roundVar
        self.ErrorNearByTest = True

        # Reuse settings
        self.posReuse = 'test'
        self.negReuse = 'test'
        self.impReuse = ''
        self.balanceReuse = None
        self.paramsReuse = {'max_abslute_size':3,'max_relative_size':10}

        # self.posReuse = ''
        # self.negReuse = ''
        # self.impReuse = ''
        # self.balanceReuse = None
        # self.paramsReuse = {}

        
        self.Setting = {}

        # CBC settings
        self.UseAdvancedCBC = True
        self.CBC_Advance = 2
        self.CBC_Advance_Limit = 15
        self.CBC_Limit = 30
        self.LastCBC_Value = -1 # for lexical only

        # BG0C settings
        self.UseBG0C = False
        
        self.Logger = logger
        if self.Logger.Stat:
            self.Logger.Stat_BplFileSize = os.path.getsize(self.TemplateBpl)
            if os.path.exists(self.TemplateBpl[:-3] + 'c'):
                self.Logger.Stat_CFileSize = os.path.getsize(self.TemplateBpl[:-3] + 'c')
            else:
                self.Logger.Stat_CFileSize = None

        # Timeout Monitor
        self.TimeoutMonitor = None
        if os.path.exists('/usr/bin/timeout'):
            self.TimeoutMonitor = '/usr/bin/timeout'
        if timeout != None and self.TimeoutMonitor == None:
            raise RuntimeError('No timeout monitor found!')
        # else:
        #     self.Logger.Stat = True # use stat timer
        self.Timeout = timeout
        self.OnceTestTimeout = 2
        # self.OnceTestTimeout = 0.5

        # Lexical
        self.UseLexical = False
        self.LexicalDistribution = []
        self.LexicalDistributionV0 = []
        self.LexicalDistributionResult = []
        self.LexicalID2Trace = []
        self.LexicalIDInDistribution = []
        self.LexicalBoundGenerator = None
        self.LexicalMDataDict = {}
        self.LexicalMDataDictV0 = {}
        self.LexicalAllStateMData = None
        self.LexicalSimpFailedMData = (['1'] + self.VarList + [self.RoundVar], [])
        self.LexicalLastDistribution = None
        self.LexicalUnsatNum = 0
        self.LexicalCurrentRank = 0
        self.LexicalMLearnKnowledge = {}
        self.LexicalRankMin = 1
        self.LexicalRankMax = 3
        # Strategy: SimExpBest, ExpBest(Discard), SimExp, TraceBest
        self.LexicalStrategy = 'TraceBest'
        self.__LexicalMLStrategy = None
        self.LexicalACBC_CEX = []
        # self.LexicalConstMax = 150
        # self.LexicalLastLargeConst = 150
        self.LexicalMaxLoss = 50000
        self.MLearnTarget = 'L2'
        # self.MLearnTarget = 'LSM_L2'
        # self.MLearnTarget = 'L2_LittleLSM'
        # self.__IceCaller = None
        self.MLearnClusterNum = 10
        self.MLearnStrategy = 'default'
        self.MLearnTraceTimeoutWithResult = 10

        # BMC Check
        self.BMC_Limit_Adapt = False
        self.BMC_Limit_Adapt_Max = 10
        self.BMC_Limit = 10 # -1 => do not do BMC
        self.BMC_Timeout = 0.5 # -1 => no bmc timeout

        # multi CEX limit (order by Trace Len)
        self.CEX_Once_Limit = 1 # None means all

        # ICE reuse
        # self.ICE_PosReuse = False
        # self.ICE_NegReuse = False
        # self.ICE_ImpReuse = False

    @staticmethod
    def LexicalL2Loss(lexical):
        loss = 0
        for it in lexical:
            for b in it:
                for v in b:
                    loss += v ** 2 + 0.001
        return loss

    def checkTerminationLexicalTrace(self):
        self.Logger.Use_Lexical = True
        if self.Logger.Stat or self.Timeout != None:
            self.Logger.StartTimer('total')
            self.Logger.Stat_Name = self.TaskName
        self.Logger.Log('Running Task \'{}\''.format(self.TaskName), level=0)
        currentResult = {'Result': 'Starting'}
        ic = IceCaller(self.Logger, self.VarList, self.TmpDir, self.TemplateBpl, self.IceLearner, posReuse = self.posReuse, negReuse = self.negReuse, impReuse = self.impReuse, balanceReuse = self.balanceReuse, paramsReuse = self.paramsReuse)
        # self.__IceCaller = ic
        checkRound = 0
        BoundLearningTraces = []
        # print('TO', self.Timeout)
        while True:
            # for itr in BoundLearningTraces:
            #     self.Logger.Log('[Debug] TR: {}'.format(itr))
            # import pdb; pdb.set_trace()
            if self.Timeout != None:
                if self.Logger.CalcTimePass('total') > self.Timeout:
                    currentResult = {'Result': 'Timeout'}
            checkRound += 1
            if currentResult['Result'] == 'Verified':
                self.Logger.Log('[Info] The termination is proved.')
                inv = currentResult['Invariant']

                if inv != None:
                    invM = IceCaller.prettyInv(self.Logger, inv)
                    self.Logger.Log('[Info] The loop invariant is: {}'.format(invM))
                else:
                    self.Logger.Log('[Info] The const bound checker proved with bound {}.'.format(currentResult['ConstBoundChecker']))

                if self.Logger.Stat:
                    self.Logger.Stat_Result = 'Termination'
                    self.Logger.Stat_TotalTime = self.Logger.CalcTimePass('total')
                    self.Logger.Stat_BoundRefineNum = checkRound - 1
                    if inv != None:
                        self.Logger.Stat_FinalInv = invM
                    else:
                        self.Logger.Stat_FinalInv = 'CBC {}'.format(currentResult['ConstBoundChecker'])
                return
            elif currentResult['Result'].startswith('Failed'):
                self.Logger.Log('[Info] Check round {}:'.format(checkRound))

                if currentResult['Result'] == 'Failed-Simp':
                    error = ErrorFinder.simpCounterexample(self.Logger, ic.fileName, self.VarList, currentResult['Error'])
                    errorInputs = []
                    errorTraces = []
                    for e in error:
                        errorValue = []
                        for v in self.VarList:
                            errorValue.append(e[0][v])
                        errorInputs.append(tuple(errorValue))
                        errTr = TraceStates(self.VarList) #pylint: disable=undefined-variable
                        errTr.appendInitState(errorValue)
                        errorTraces.append(errTr)

                elif currentResult['Result'] in ['Failed-CBC', 'Failed-BG0C']:
                    error = currentResult['Counterexample']
                    errorInputs = []
                    errorTraces = []
                    for e in error:
                        errorValue = []
                        for v in self.VarList:
                            errorValue.append(e[0][v])
                        errorInputs.append(tuple(errorValue))
                        errTr = TraceStates(self.VarList) #pylint: disable=undefined-variable
                        errTr.appendInitState(errorValue)
                        errorTraces.append(errTr)

                    # import pdb; pdb.set_trace()
                    # raise NotImplementedError("Failed-CBC or BG0C not finish")
                elif currentResult['Result'] == 'Failed-BMC':
                    if not currentResult['ReturnType'] == 'trace':
                        raise RuntimeError('Return type is not trace in trace checking.')
                    errorTraces, errorInputs = currentResult['ErrorTrace'], currentResult['ErrorInput']
                elif currentResult['Result'] == 'Failed':
                    ef = ErrorFinder.load(self.Logger, ic.fileName, self.VarList)
                    errorInputs, errorTraces = ef.getErrorInputLexical(option='trace')
                    # import pdb; pdb.set_trace()
                else:
                    raise RuntimeError('Unknown Failed type!')

                if self.BMC_Limit >= 0 and self.BMC_Limit_Adapt:
                    minErTrLen = min(map(lambda x: len(x.States), errorTraces))
                    print(minErTrLen, self.BMC_Limit)
                    if minErTrLen >= self.BMC_Limit - 1:
                        self.BMC_Limit = min(max(1, self.BMC_Limit * 2), self.BMC_Limit_Adapt_Max)

                if self.CEX_Once_Limit != None:
                    zipInfo = list(zip(errorTraces, errorInputs))
                    zipInfo.sort(key = lambda x: len(x[0].States))
                    zipInfo = zipInfo[:self.CEX_Once_Limit]
                    errorTraces = list(map(lambda x:x[0], zipInfo))
                    errorInputs = list(map(lambda x:x[1], zipInfo))

                self.Logger.Log('[Info] Error traces with input are: {}'.format(errorInputs))
                # self.Logger.Log('[Info] Error traces are:')
                # for it in transdata:
                #     self.Logger.Log('[Info]   {}'.format(it))
                for itr in errorTraces:
                    self.Logger.Log('[Info] Error trace: {}'.format(itr))
                # import pdb; pdb.set_trace()
                BoundLearningTraces += errorTraces
                if self.Logger.Stat:
                    self.Logger.Stat_TestTimeList.append(0)
                    self.Logger.Stat_TestStateNumList.append(0)
                if self.ErrorNearByTest:
                    self.Logger.Log('[Info] Running the nearby test...')
                    eid = 0
                    for eValue in errorInputs:
                        self.Logger.Log('[Info] Nearby Test @ {} starts...'.format(tuple(eValue)))
                        if self.Logger.Stat:
                            self.Logger.StartTimer('Test@{}_S1E{}'.format(checkRound, eid))
                        nbTestTRs = self.runRandTestLexical(TraceCEX=tuple(eValue), Testmode='rand', testOption='trace')
                        if self.Logger.Stat:
                            TimeS1 = self.Logger.CalcTimePass('Test@{}_S1E{}'.format(checkRound, eid))
                            NumS1 = len(nbTestTRs)
                        BoundLearningTraces += nbTestTRs
                        if self.Logger.Stat:
                            self.Logger.StartTimer('Test@{}_S2E{}'.format(checkRound, eid))
                        taTestTRs = self.runRandTestLexical(TraceCEX=tuple(eValue), Testmode='target', testOption='trace')
                        if self.Logger.Stat:
                            TimeS2 = self.Logger.CalcTimePass('Test@{}_S2E{}'.format(checkRound, eid))
                            NumS2 = len(taTestTRs)
                            self.Logger.Stat_TestTimeList[-1] += TimeS1 + TimeS2
                            self.Logger.Stat_TestStateNumList[-1] += NumS1 + NumS2
                        BoundLearningTraces += taTestTRs
                        eid += 1
                
                self.Logger.Log('[Info] Running the bound leaner...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Bound@{}'.format(checkRound))

                if self.Timeout != None:
                    boundList = self.runLexicalTraceMLearn(BoundLearningTraces, self.LexicalRankMin, self.LexicalRankMax, self.Timeout - int(self.Logger.CalcTimePass('total')) - 1, self.MLearnTraceTimeoutWithResult)
                else:
                    boundList = self.runLexicalTraceMLearn(BoundLearningTraces, self.LexicalRankMin, self.LexicalRankMax)
                if self.Timeout != None and self.Logger.CalcTimePass('total') > self.Timeout:
                    continue

                if boundList != None:
                    self.Logger.Log('[Info] Lexical bound is: {}'.format(tuple(boundList)))
                else:
                    self.Logger.Log('[Info] Lexical bound not found!')

                if self.Logger.Stat:
                    self.Logger.Stat_BoundTimeList.append(self.Logger.CalcTimePass('Bound@{}'.format(checkRound)))
                    self.Logger.Stat_FinalBound = boundList
                    if self.Logger.Stat_LogAllBound:
                        self.Logger.Stat_BoundList.append(boundList)
                if boundList == None:
                    currentResult['Result'] = 'Unknown'
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(0)
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                    continue

                ic.GenerateConcreteBplFileLexicalTemplate(boundList)
                
                retCBC = self.doCBC(boundList)
                if retCBC > 0:
                    self.Logger.Log('[Info] Running CBC...')
                    if self.Logger.Stat:
                        self.Logger.StartTimer('CBC@{}'.format(checkRound))
                    cc = CBChecker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResult = cc.ExecuteCBC(retCBC)
                    else:
                        currentResult = cc.ExecuteCBC(retCBC, timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(self.Logger.CalcTimePass('CBC@{}'.format(checkRound)))
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                    continue
                else:
                    self.Logger.Stat_CBCTimeList.append(0)

                if self.UseBG0C:
                    self.Logger.Log('[Info] Running BG0C...')
                    self.Logger.StartTimer('BG0C@{}'.format(checkRound))
                    bc = BG0Checker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    bcRet, bcState = bc.ExecuteBG0C(boundList)
                    self.Logger.Stat_BG0CTimeList.append(self.Logger.CalcTimePass('BG0C@{}'.format(checkRound)))
                    if not bcRet:
                        currentResult = bcState
                        self.Logger.Stat_InvTimeList.append(0)
                        continue
                else:
                    self.Logger.Stat_BG0CTimeList.append(0)

                if self.BMC_Limit >= 0:
                    self.Logger.Log('[Info] Running BMC...')
                    self.Logger.StartTimer('BMC@{}'.format(checkRound))
                    bf = BMCFinder(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResultTmp = bf.ExecuteBMC(self.BMC_Limit, ret = 'trace')
                    else:
                        currentResultTmp = bf.ExecuteBMC(self.BMC_Limit, ret = 'trace' , timeoutMonitor=self.TimeoutMonitor, timeout=min(self.BMC_Timeout, self.Timeout - 1 - int(self.Logger.CalcTimePass('total'))))
                    if currentResultTmp['Result'] in ['Failed-BMC']:
                        currentResult = currentResultTmp
                        if self.Logger.Stat:
                            self.Logger.Stat_BMCTimeList.append(self.Logger.CalcTimePass('BMC@{}'.format(checkRound)))
                            self.Logger.Stat_InvTimeList.append(0)
                            self.Logger.Stat_InvRefineNumList.append(0)
                        # print('[BMC:Debug] BMC found bound cex with bound {}, errorTraceLen {}'.format(boundList, list(map(lambda x: len(x.States), currentResult['ErrorTrace']))))
                        continue
                    else:
                        # print('[BMC:Debug] BMC found no bound cex with bound {}. ({})'.format(boundList, currentResultTmp['Result']))
                        if self.Logger.Stat:
                            self.Logger.Stat_BMCTimeList.append(self.Logger.CalcTimePass('BMC@{}'.format(checkRound)))
                else:
                    self.Logger.Stat_BMCTimeList.append(0)

                self.Logger.Log('[Info] Running ICE...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Inv@{}'.format(checkRound))
                if self.Timeout == None:
                    currentResult = ic.ExecuteICE()
                else:
                    currentResult = ic.ExecuteICE(timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                if self.Logger.Stat:
                    self.Logger.Stat_InvTimeList.append(self.Logger.CalcTimePass('Inv@{}'.format(checkRound)))

            elif currentResult['Result'] == 'Starting':
                self.Logger.Log('[Info] Check round {}:'.format(checkRound))

                self.Logger.Log('[Info] Running the test...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Test@{}'.format(checkRound))

                newTestTraces = self.runRandTestLexical(TraceCEX=None, Testmode='rand', testOption='trace')
                BoundLearningTraces += newTestTraces
                # BoundLearningTraces = list(set(BoundLearningTraces))

                if self.Logger.Stat:
                    self.Logger.Stat_TestTimeList.append(self.Logger.CalcTimePass('Test@{}'.format(checkRound)))
                    self.Logger.Stat_TestStateNumList.append(len(newTestTraces))


                if self.Logger.Stat:
                    self.Logger.Stat_BoundStateNumList.append(len(BoundLearningTraces))

                self.Logger.Log('[Info] Running the bound leaner...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Bound@{}'.format(checkRound))
                # find All
                if self.Timeout != None:
                    boundList = self.runLexicalTraceMLearn(BoundLearningTraces, self.LexicalRankMin, self.LexicalRankMax, self.Timeout - int(self.Logger.CalcTimePass('total')) - 1, self.MLearnTraceTimeoutWithResult)
                else:
                    boundList = self.runLexicalTraceMLearn(BoundLearningTraces, self.LexicalRankMin, self.LexicalRankMax)

                if self.Timeout != None and self.Logger.CalcTimePass('total') > self.Timeout:
                    continue
                # import pdb; pdb.set_trace()
                if boundList != None:
                    self.Logger.Log('[Info] Lexical bound is: {}'.format(tuple(boundList)))
                else:
                    self.Logger.Log('[Info] Lexical bound not found!')
                # print(boundList)
                # import pdb; pdb.set_trace()
                if self.Logger.Stat:
                    self.Logger.Stat_BoundTimeList.append(self.Logger.CalcTimePass('Bound@{}'.format(checkRound)))
                    self.Logger.Stat_FinalBound = boundList
                    if self.Logger.Stat_LogAllBound:
                        self.Logger.Stat_BoundList.append(boundList)
                if boundList == None:
                    currentResult['Result'] = 'Unknown'
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(0)
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                        self.Logger.Stat_BMCTimeList.append(0)
                    continue
                # append > 0
                # boundList.append((self.IterateVar, '1'))

                ic.GenerateConcreteBplFileLexicalTemplate(boundList)
                retCBC = self.doCBC(boundList)
                if retCBC > 0:
                    self.Logger.Log('[Info] Running CBC...')
                    if self.Logger.Stat:
                        self.Logger.StartTimer('CBC@{}'.format(checkRound))
                    cc = CBChecker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResult = cc.ExecuteCBC(retCBC)
                    else:
                        currentResult = cc.ExecuteCBC(retCBC, timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(self.Logger.CalcTimePass('CBC@{}'.format(checkRound)))
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                        self.Logger.Stat_BMCTimeList.append(0)
                    continue
                else:
                    self.Logger.Stat_CBCTimeList.append(0)


                if self.UseBG0C:
                    self.Logger.Log('[Info] Running BG0C...')
                    self.Logger.StartTimer('BG0C@{}'.format(checkRound))
                    bc = BG0Checker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    bcRet, bcState = bc.ExecuteBG0C(boundList)
                    self.Logger.Stat_BG0CTimeList.append(self.Logger.CalcTimePass('BG0C@{}'.format(checkRound)))
                    if not bcRet:
                        currentResult = bcState
                        self.Logger.Stat_BMCTimeList.append(0)
                        self.Logger.Stat_InvTimeList.append(0)
                        continue
                else:
                    self.Logger.Stat_BG0CTimeList.append(0)

                if self.BMC_Limit >= 0:
                    self.Logger.Log('[Info] Running BMC...')
                    self.Logger.StartTimer('BMC@{}'.format(checkRound))
                    bf = BMCFinder(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResultTmp = bf.ExecuteBMC(self.BMC_Limit, ret = 'trace')
                    else:
                        currentResultTmp = bf.ExecuteBMC(self.BMC_Limit, ret = 'trace' , timeoutMonitor=self.TimeoutMonitor, timeout=min(self.BMC_Timeout, self.Timeout - 1 - int(self.Logger.CalcTimePass('total'))))
                    if currentResultTmp['Result'] in ['Failed-BMC']:
                        currentResult = currentResultTmp
                        if self.Logger.Stat:
                            self.Logger.Stat_BMCTimeList.append(self.Logger.CalcTimePass('BMC@{}'.format(checkRound)))
                            self.Logger.Stat_InvTimeList.append(0)
                            self.Logger.Stat_InvRefineNumList.append(0)
                        # print('[BMC:Debug] BMC found bound cex with bound {}, errorTraceLen {}'.format(boundList, list(map(lambda x: len(x.States), currentResult['ErrorTrace']))))
                        continue
                    else:
                        # print('[BMC:Debug] BMC found no bound cex with bound {}. ({})'.format(boundList, currentResultTmp['Result']))
                        if self.Logger.Stat:
                            self.Logger.Stat_BMCTimeList.append(self.Logger.CalcTimePass('BMC@{}'.format(checkRound)))
                else:
                    self.Logger.Stat_BMCTimeList.append(0)
                
                self.Logger.Log('[Info] Running ICE...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Inv@{}'.format(checkRound))
                if self.Timeout == None:
                    currentResult = ic.ExecuteICE()
                else:
                    currentResult = ic.ExecuteICE(timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                if self.Logger.Stat:
                    self.Logger.Stat_InvTimeList.append(self.Logger.CalcTimePass('Inv@{}'.format(checkRound)))

            elif currentResult['Result'] == 'Timeout':
                if self.Logger.Stat:
                    self.Logger.Stat_Result = 'Timeout'
                    self.Logger.Stat_TotalTime = self.Logger.CalcTimePass('total')
                    self.Logger.Stat_BoundRefineNum = checkRound - 1
                    return
            elif currentResult['Result'] == 'Unknown':
                if self.Logger.Stat:
                    self.Logger.Stat_Result = 'Unknown'
                    self.Logger.Stat_TotalTime = self.Logger.CalcTimePass('total')
                    self.Logger.Stat_BoundRefineNum = checkRound - 1
                    return
            else:
                raise RuntimeError('Unknown running state.')


    def runLexicalTraceMLearn(self, traces, minRank=1, maxRank=3, timeout=None, timeoutWithResult=None, CostFunc=LexicalL2Loss.__func__):
        # print('[Debug]', len(traces))
        if self.UseAdvancedCBC:
            # self.__IceCaller.GenerateConcreteBplFileLexicalTemplate([['1']])
            # import pdb; pdb.set_trace()
            ACBC = self.runMLearnWithCBCAdvance(traces)
            if ACBC != None:
                return [[ACBC[0][1]]]

        self.runLexicalTraceMLearnInit(traces)
        minRank = min(minRank, len(self.LexicalID2Trace))
        maxRank = min(maxRank, len(self.LexicalID2Trace))
        self.LexicalBoundGenerator = self.runLexicalTraceMLearnGenerator(traces, minRank, maxRank, CostFunc)
        if len(self.LexicalID2Trace) == 0:
            return [[str(self.LastCBC_Value)]]
        self.Logger.Log('[Info] Trace NUM:{}'.format(len(self.LexicalID2Trace)), level=5)
        bestLexical = None
        bestCost = None
        self.Logger.StartTimer('LexicalTraceTimer')
        while True:
            nextRst = next(self.LexicalBoundGenerator)
            if nextRst == None:
                break
            # print('Usetime = ', self.Logger.CalcTimePass('total'))
            if timeoutWithResult != None and nextRst != None and self.Logger.CalcTimePass('LexicalTraceTimer') > timeoutWithResult:
                self.Logger.Log('[Warning] Lexical bound time limit reached. (With result)')
                break
            if timeout != None and self.Logger.CalcTimePass('LexicalTraceTimer') > timeout:
                self.Logger.Log('[Warning] Lexical bound time limit reached. (Without result)')
                break
            levelInt = 0
            for rkLevel in self.LexicalIDInDistribution:
                self.Logger.Log('[Info] Lexical bound (Level-{}) of {} is: {}'.format(levelInt, rkLevel, nextRst))
                levelInt += 1
            costCurrent = CostFunc(nextRst)
            self.Logger.Log('[Info] Lexical candidate: {}; Cost: {}.'.format(nextRst, costCurrent))
            if bestLexical == None or bestCost > costCurrent:
                bestLexical = nextRst
                bestCost = costCurrent
                
        if bestLexical == None:
            self.Logger.Log('[Info] No lexical result found! rank({}-{})'.format(minRank,maxRank), level=1)
            return None
        self.Logger.Log('[Info] Best lexical candidate: {}.'.format(bestLexical))
             
        nextRstAddConst = []
        for it in bestLexical:
            exprList = []
            for itt in it:
                boundExpr = IceCaller.GenerateExpr(['1'] + self.VarList, itt, self.Logger)
                exprList.append(boundExpr)
            nextRstAddConst.append(exprList)

        return nextRstAddConst

    def runLexicalTraceMLearnInit(self, traces):
        itTuples = set()
        for trace in traces:
            # print(len(trace.Traces))
            for it in trace.Traces:
                itTuples.add(it)
        self.LexicalID2Trace = list(itTuples)
        self.LexicalID2Trace.sort()

    def runLexicalTraceMLearnGenerator(self, traces, minRank=1, maxRank=3, CostFunc=LexicalL2Loss.__func__):
        for rank in range(minRank, maxRank + 1):
            self.Logger.Log('[Info] Current rank is {}'.format(rank))
            self.LexicalDistribution = []
            for _ in range(rank):
                self.LexicalDistribution.append(set())
            self.LexicalCurrentRank = rank
            yield from self.runLexicalTraceMLearnGeneratorDFS(traces, 0, rank, CostFunc)

        yield None

    def runLexicalTraceMLearnCheck(self, traces, CostFunc=LexicalL2Loss.__func__):
        for it in self.LexicalDistribution:
            if len(it) == 0:
                return None
        # print('[Debug] Current trying lexical bound: ', self.LexicalDistribution)
        dimsMDataList = []
        for tr in traces:
            dimsMDataList.append(tr.GenerateMData4Dims(tuple(self.LexicalDistribution), self.RoundVar))
        # print('[Debug]', tuple(self.LexicalDistribution))
        result = []
        for rk in range(self.LexicalCurrentRank):
            MDataList = []
            for DimsMData in dimsMDataList:
                MDataList.append(DimsMData[rk])
            mData = IceTerm.dataMerge(MDataList)
            resultIt = self.runLexicalTraceMLearnCheckRaw(mData, CostFunc)
            # print('[Debug] Result for dim-{} is'.format(rk), resultIt)
            # if rk == 1 and self.LexicalDistribution == [{('L2', 'L3'), ('L2', 'L4')}, {('L1',)}]:
            #     import pdb; pdb.set_trace()
            if resultIt == None:
                return None
            result.append(resultIt)
        return result
            
    def runLexicalTraceMLearnCheckRaw(self, mData, CostFunc=LexicalL2Loss.__func__):
        self.Logger.Log('[Info] ML checking')
        mData[1].sort()
        knowledgeKey = tuple(mData[1])
        if knowledgeKey in self.LexicalMLearnKnowledge.keys():
            return self.LexicalMLearnKnowledge[knowledgeKey]
        self.csvDataWriter(self.MLearnFile, mData)
        # import pdb; pdb.set_trace()
        mLearn = MLearn(self.Logger, self.MLearnFile)
        resultArgs = None
        if self.MLearnStrategy == 'default':
            result = mLearn.Learning(strategy='CLearn-best', target=self.MLearnTarget, ClusterNum = self.MLearnClusterNum)
        else:
            result = mLearn.Learning(strategy=self.MLearnStrategy, target=self.MLearnTarget, ClusterNum = self.MLearnClusterNum)

        if not result['success']:
            self.Logger.Log('[Info] ML msg: {}'.format(result['message']))
            resultArgs = None
        elif result['Args'] == None:
            resultArgs = None
        elif self.LexicalMaxLoss != None and CostFunc((result['Args'], )) > self.LexicalMaxLoss:
            resultArgs = None
        else:
            A_List = result['Args']
            resultArgs = []
            for A in A_List:
                lineA = []
                for item in A:
                    lineA.append(int(item))
                resultArgs.append(lineA)
        self.LexicalMLearnKnowledge[knowledgeKey] = resultArgs
        # import pdb; pdb.set_trace()
        return resultArgs

    def runLexicalTraceMLearnGeneratorDFS(self, traces, now, rank, CostFunc=LexicalL2Loss.__func__):
        if now == len(self.LexicalID2Trace): 
            result = self.runLexicalTraceMLearnCheck(traces, CostFunc)
            if type(result) != type(None):
                yield result
        else:
            for r in range(rank):
                self.LexicalDistribution[r].add(self.LexicalID2Trace[now])
                yield from self.runLexicalTraceMLearnGeneratorDFS(traces, now+1, rank)
                self.LexicalDistribution[r].remove(self.LexicalID2Trace[now])
        ...

    def checkTerminationLexicalDelta(self):
        self.Logger.Use_Lexical = True
        # skip CBC first
        # self.UseAdvancedCBC = False
        # self.CBC_Advance = 0
        # self.CBC_Advance_Limit = 0
        # self.CBC_Limit = 0

        if self.Logger.Stat or self.Timeout != None:
            self.Logger.StartTimer('total')
            self.Logger.Stat_Name = self.TaskName

        self.Logger.Log('Running Task \'{}\''.format(self.TaskName), level=0)
        currentResult = {'Result': 'Starting'}
        ic = IceCaller(self.Logger, self.VarList, self.TmpDir, self.TemplateBpl, self.IceLearner, posReuse = self.posReuse, negReuse = self.negReuse, impReuse = self.impReuse, balanceReuse = self.balanceReuse, paramsReuse = self.paramsReuse)
        # self.__IceCaller = ic
        checkRound = 0
        BoundLearningData = []
        while True:
            # import pdb; pdb.set_trace()
            if self.Timeout != None:
                if self.Logger.CalcTimePass('total') > self.Timeout:
                    currentResult = {'Result': 'Timeout'}
            checkRound += 1
            if currentResult['Result'] == 'Verified':
                self.Logger.Log('[Info] The termination is proved.')
                inv = currentResult['Invariant']

                if inv != None:
                    invM = IceCaller.prettyInv(self.Logger, inv)
                    self.Logger.Log('[Info] The loop invariant is: {}'.format(invM))
                else:
                    self.Logger.Log('[Info] The const bound checker proved with bound {}.'.format(currentResult['ConstBoundChecker']))

                if self.Logger.Stat:
                    self.Logger.Stat_Result = 'Termination'
                    self.Logger.Stat_TotalTime = self.Logger.CalcTimePass('total')
                    self.Logger.Stat_BoundRefineNum = checkRound - 1
                    if inv != None:
                        self.Logger.Stat_FinalInv = invM
                    else:
                        self.Logger.Stat_FinalInv = 'CBC {}'.format(currentResult['ConstBoundChecker'])
                return
            elif currentResult['Result'].startswith('Failed'):
                self.Logger.Log('[Info] Check round {}:'.format(checkRound))

                # MData = IceTerm.csvDataLoader(self.MLearnFile)
                if currentResult['Result'] == 'Failed-Simp':
                    error = ErrorFinder.simpCounterexample(self.Logger, ic.fileName, self.VarList, currentResult['Error'])
                    errorInputs = []
                    errorMData = []
                    for e in error:
                        errorValue = []
                        for v in self.VarList:
                            errorValue.append(e[0][v])
                        errorInputs.append(tuple(errorValue))
                        errorMData.append(tuple([1] + errorValue + [1]))
                        self.LexicalACBC_CEX.append((errorValue, 1))
                    self.LexicalSimpFailedMData[1].extend(errorMData)
                    transdata = []
                    # raise NotImplementedError("Failed-Simp not finish")
                elif currentResult['Result'] in ['Failed-CBC', 'Failed-BG0C']:
                    error = currentResult['Counterexample']
                    errorInputs = []
                    errorMData = []
                    for e in error:
                        errorValue = []
                        for v in self.VarList:
                            errorValue.append(e[0][v])
                        errorInputs.append(tuple(errorValue))
                        errorMData.append(tuple([1] + errorValue + [1]))
                        self.LexicalACBC_CEX.append((errorValue, e[1]))
                    self.LexicalSimpFailedMData[1].extend(errorMData)
                    transdata = []
                    # import pdb; pdb.set_trace()
                    # raise NotImplementedError("Failed-CBC or BG0C not finish")
                elif currentResult['Result'] == 'Failed':
                    ef = ErrorFinder.load(self.Logger, ic.fileName, self.VarList)
                    errorInputs, transdata = ef.getErrorInputLexical()
                    # import pdb; pdb.set_trace()
                else:
                    raise RuntimeError('Unknown Failed type!')

                self.Logger.Log('[Info] Error traces with input are: {}'.format(errorInputs))
                self.Logger.Log('[Info] Error traces are:')
                for it in transdata:
                    self.Logger.Log('[Info]   {}'.format(it))
                
                BoundLearningData += transdata
                if self.Logger.Stat:
                    self.Logger.Stat_TestTimeList.append(0)
                    self.Logger.Stat_TestStateNumList.append(0)
                if self.ErrorNearByTest:
                    self.Logger.Log('[Info] Running the nearby test...')
                    eid = 0
                    for eValue in errorInputs:
                        self.Logger.Log('[Info] Nearby Test @ {} starts...'.format(tuple(eValue)))
                        if self.Logger.Stat:
                            self.Logger.StartTimer('Test@{}_S1E{}'.format(checkRound, eid))
                        nbTestData = self.runRandTestLexical(TraceCEX=tuple(eValue), Testmode='rand')
                        if self.Logger.Stat:
                            TimeS1 = self.Logger.CalcTimePass('Test@{}_S1E{}'.format(checkRound, eid))
                            NumS1 = len(nbTestData)
                        BoundLearningData += nbTestData
                        if self.Logger.Stat:
                            self.Logger.StartTimer('Test@{}_S2E{}'.format(checkRound, eid))
                        taTestData = self.runRandTestLexical(TraceCEX=tuple(eValue), Testmode='target')
                        if self.Logger.Stat:
                            TimeS2 = self.Logger.CalcTimePass('Test@{}_S2E{}'.format(checkRound, eid))
                            NumS2 = len(taTestData)
                            self.Logger.Stat_TestTimeList[-1] += TimeS1 + TimeS2
                            self.Logger.Stat_TestStateNumList[-1] += NumS1 + NumS2
                        BoundLearningData += taTestData
                        eid += 1
                
                BoundLearningData = list(set(BoundLearningData))
                self.Logger.Log('[Info] Running the bound leaner...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Bound@{}'.format(checkRound))

                boundList = self.runLexicalMLearn(BoundLearningData, self.LexicalRankMin, self.LexicalRankMax)

                if boundList != None:
                    self.Logger.Log('[Info] Lexical bound is: {}'.format(tuple(boundList)))
                else:
                    self.Logger.Log('[Info] Lexical bound not found!')

                if self.Logger.Stat:
                    self.Logger.Stat_BoundTimeList.append(self.Logger.CalcTimePass('Bound@{}'.format(checkRound)))
                    self.Logger.Stat_FinalBound = boundList
                    if self.Logger.Stat_LogAllBound:
                        self.Logger.Stat_BoundList.append(boundList)
                if boundList == None:
                    currentResult['Result'] = 'Unknown'
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(0)
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                    continue

                ic.GenerateConcreteBplFileLexicalTemplate(boundList)
                
                retCBC = self.doCBC(boundList)
                if retCBC > 0:
                    self.Logger.Log('[Info] Running CBC...')
                    if self.Logger.Stat:
                        self.Logger.StartTimer('CBC@{}'.format(checkRound))
                    cc = CBChecker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResult = cc.ExecuteCBC(retCBC)
                    else:
                        currentResult = cc.ExecuteCBC(retCBC, timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(self.Logger.CalcTimePass('CBC@{}'.format(checkRound)))
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                    continue

                if self.UseBG0C:
                    self.Logger.Log('[Info] Running BG0C...')
                    self.Logger.StartTimer('BG0C@{}'.format(checkRound))
                    bc = BG0Checker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    bcRet, bcState = bc.ExecuteBG0C(boundList)
                    self.Logger.Stat_BG0CTimeList.append(self.Logger.CalcTimePass('BG0C@{}'.format(checkRound)))
                    if not bcRet:
                        currentResult = bcState
                        self.Logger.Stat_InvTimeList.append(0)
                        continue
                else:
                    self.Logger.Stat_BG0CTimeList.append(0)

                self.Logger.Log('[Info] Running ICE...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Inv@{}'.format(checkRound))
                if self.Timeout == None:
                    currentResult = ic.ExecuteICE()
                else:
                    currentResult = ic.ExecuteICE(timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                if self.Logger.Stat:
                    self.Logger.Stat_InvTimeList.append(self.Logger.CalcTimePass('Inv@{}'.format(checkRound)))
                    self.Logger.Stat_CBCTimeList.append(0)

            elif currentResult['Result'] == 'Starting':
                self.Logger.Log('[Info] Check round {}:'.format(checkRound))

                self.Logger.Log('[Info] Running the test...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Test@{}'.format(checkRound))

                newTestData = self.runRandTestLexical(TraceCEX=None, Testmode='rand')
                BoundLearningData += newTestData
                BoundLearningData = list(set(BoundLearningData))

                if self.Logger.Stat:
                    self.Logger.Stat_TestTimeList.append(self.Logger.CalcTimePass('Test@{}'.format(checkRound)))
                    self.Logger.Stat_TestStateNumList.append(len(newTestData))

                # mDataDict = TraceStateTrans.TestDataTR2mDataDict(BoundLearningData, appendRName=self.RoundVar)

                if self.Logger.Stat:
                    self.Logger.Stat_BoundStateNumList.append(len(BoundLearningData))
                # IceTerm.csvDataWriter(self.MLearnFile, MData)
                self.Logger.Log('[Info] Running the bound leaner...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Bound@{}'.format(checkRound))
                # find All
                boundList = self.runLexicalMLearn(BoundLearningData, self.LexicalRankMin, self.LexicalRankMax)
                # import pdb; pdb.set_trace()
                if boundList != None:
                    self.Logger.Log('[Info] Lexical bound is: {}'.format(tuple(boundList)))
                else:
                    self.Logger.Log('[Info] Lexical bound not found!')
                # print(boundList)
                # import pdb; pdb.set_trace()
                if self.Logger.Stat:
                    self.Logger.Stat_BoundTimeList.append(self.Logger.CalcTimePass('Bound@{}'.format(checkRound)))
                    self.Logger.Stat_FinalBound = boundList
                    if self.Logger.Stat_LogAllBound:
                        self.Logger.Stat_BoundList.append(boundList)
                if boundList == None:
                    currentResult['Result'] = 'Unknown'
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(0)
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                    continue
                # append > 0
                # boundList.append((self.IterateVar, '1'))

                ic.GenerateConcreteBplFileLexicalTemplate(boundList)
                retCBC = self.doCBC(boundList)
                if retCBC > 0:
                    self.Logger.Log('[Info] Running CBC...')
                    if self.Logger.Stat:
                        self.Logger.StartTimer('CBC@{}'.format(checkRound))
                    cc = CBChecker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResult = cc.ExecuteCBC(retCBC)
                    else:
                        currentResult = cc.ExecuteCBC(retCBC, timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(self.Logger.CalcTimePass('CBC@{}'.format(checkRound)))
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                    continue

                if self.UseBG0C:
                    self.Logger.Log('[Info] Running BG0C...')
                    self.Logger.StartTimer('BG0C@{}'.format(checkRound))
                    bc = BG0Checker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    bcRet, bcState = bc.ExecuteBG0C(boundList)
                    self.Logger.Stat_BG0CTimeList.append(self.Logger.CalcTimePass('BG0C@{}'.format(checkRound)))
                    if not bcRet:
                        currentResult = bcState
                        self.Logger.Stat_InvTimeList.append(0)
                        continue
                else:
                    self.Logger.Stat_BG0CTimeList.append(0)
                
                self.Logger.Log('[Info] Running ICE...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Inv@{}'.format(checkRound))
                if self.Timeout == None:
                    currentResult = ic.ExecuteICE()
                else:
                    currentResult = ic.ExecuteICE(timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                if self.Logger.Stat:
                    self.Logger.Stat_InvTimeList.append(self.Logger.CalcTimePass('Inv@{}'.format(checkRound)))
                    self.Logger.Stat_CBCTimeList.append(0)

            elif currentResult['Result'] == 'Timeout':
                if self.Logger.Stat:
                    self.Logger.Stat_Result = 'Timeout'
                    self.Logger.Stat_TotalTime = self.Logger.CalcTimePass('total')
                    self.Logger.Stat_BoundRefineNum = checkRound - 1
                    return
            elif currentResult['Result'] == 'Unknown':
                if self.Logger.Stat:
                    self.Logger.Stat_Result = 'Unknown'
                    self.Logger.Stat_TotalTime = self.Logger.CalcTimePass('total')
                    self.Logger.Stat_BoundRefineNum = checkRound - 1
                    return
            else:
                raise RuntimeError('Unknown running state.')
        ...

    def checkTermination(self):
        # self.Logger.Stat_ICE_PosReuse = self.ICE_PosReuse
        # self.Logger.Stat_ICE_NegReuse = self.ICE_NegReuse
        # self.Logger.Stat_ICE_ImpReuse = self.ICE_ImpReuse

        if self.UseLexical:
            if self.LexicalStrategy.startswith('Trace'):
                return self.checkTerminationLexicalTrace()
            return self.checkTerminationLexicalDelta()
        self.Logger.Use_Lexical = False

        if self.Logger.Stat or self.Timeout != None:
            self.Logger.StartTimer('total')
            self.Logger.Stat_Name = self.TaskName

        self.Logger.Log('Running Task \'{}\''.format(self.TaskName), level=0)
        currentResult = {'Result': 'Starting'}
        ic = IceCaller(self.Logger, self.VarList, self.TmpDir, self.TemplateBpl, self.IceLearner, posReuse = self.posReuse, negReuse = self.negReuse, impReuse = self.impReuse, balanceReuse = self.balanceReuse, paramsReuse = self.paramsReuse)
        # self.__IceCaller = ic
        checkRound = 0
        while True:
            if self.Timeout != None:
                if self.Logger.CalcTimePass('total') > self.Timeout:
                    currentResult = {'Result': 'Timeout'}
            checkRound += 1
            if currentResult['Result'] == 'Verified':
                self.Logger.Log('[Info] The termination is proved.')
                inv = currentResult['Invariant']

                if inv != None:
                    invM = IceCaller.prettyInv(self.Logger, inv)
                    self.Logger.Log('[Info] The loop invariant is: {}'.format(invM))
                else:
                    self.Logger.Log('[Info] The const bound checker proved with bound {}.'.format(currentResult['ConstBoundChecker']))

                if self.Logger.Stat:
                    self.Logger.Stat_Result = 'Termination'
                    self.Logger.Stat_TotalTime = self.Logger.CalcTimePass('total')
                    self.Logger.Stat_BoundRefineNum = checkRound - 1
                    if inv != None:
                        self.Logger.Stat_FinalInv = invM
                    else:
                        self.Logger.Stat_FinalInv = 'CBC {}'.format(currentResult['ConstBoundChecker'])
                return
            elif currentResult['Result'].startswith('Failed'):
                self.Logger.Log('[Info] Check round {}:'.format(checkRound))

                MData = IceTerm.csvDataLoader(self.MLearnFile)
                if currentResult['Result'] == 'Failed-Simp':
                    error = ErrorFinder.simpCounterexample(self.Logger, ic.fileName, self.VarList, currentResult['Error'])
                elif currentResult['Result'] in ['Failed-CBC', 'Failed-BG0C']:
                    error = currentResult['Counterexample']
                elif currentResult['Result'] == 'Failed':
                    ef = ErrorFinder.load(self.Logger, ic.fileName, self.VarList)
                    error = ef.getErrorInput()
                elif currentResult['Result'] == 'Failed-BMC':
                    if currentResult['ReturnType'] != 'default':
                        raise RuntimeError('BMC should return default trace!')
                    error = [] 
                    for tr in currentResult['ErrorTrace']:
                        error.append(tr[0])
                else:
                    raise RuntimeError('Unknown Failed type!')

                if self.BMC_Limit >= 0 and self.BMC_Limit_Adapt:
                    minErTrLen = min(map(lambda x: x[1], error))
                    if minErTrLen >= self.BMC_Limit:
                        self.BMC_Limit = min(max(1, self.BMC_Limit * 2), self.BMC_Limit_Adapt_Max)

                if self.CEX_Once_Limit != None:
                    error.sort(key = lambda x: x[1])
                    error = error[:self.CEX_Once_Limit]

                self.Logger.Log('[Info] Error trace with input is: {}'.format(error))
                eData = self.dataMakeFromErrorList(MData[0], error)
                if self.Logger.Stat:
                    self.Logger.Stat_TestTimeList.append(0)
                    self.Logger.Stat_TestStateNumList.append(0)

                if self.ErrorNearByTest:
                    self.Logger.Log('[Info] Running the nearby test...')
                    eid = 0
                    for e in error:
                        VarValue = []
                        for var in MData[0]:
                            if var == self.RoundVar:
                                continue
                            VarValue.append(e[0][var])
                        self.Logger.Log('[Info] Nearby Test @ {} starts...'.format(tuple(VarValue)))
                        if self.Logger.Stat:
                            self.Logger.StartTimer('Test@{}_S1E{}'.format(checkRound,eid))
                        self.runRandTest(TraceCEX=tuple(VarValue), Testmode='rand')
                        if self.Logger.Stat:
                            TimeS1 = self.Logger.CalcTimePass('Test@{}_S1E{}'.format(checkRound,eid))
                            NumS1 = self.testNumCount(self.getLastTest())
                        TData = IceTerm.csvDataLoader(self.getLastTest())
                        eData = IceTerm.dataMerge([TData, eData])
                        if self.Logger.Stat:
                            self.Logger.StartTimer('Test@{}_S2E{}'.format(checkRound,eid))
                        self.runRandTest(TraceCEX=tuple(VarValue), Testmode='target')
                        if self.Logger.Stat:
                            TimeS2 = self.Logger.CalcTimePass('Test@{}_S2E{}'.format(checkRound,eid))
                            NumS2 = self.testNumCount(self.getLastTest())
                            self.Logger.Stat_TestTimeList[-1] += TimeS1 + TimeS2
                            self.Logger.Stat_TestStateNumList[-1] += NumS1 + NumS2
                        TData = IceTerm.csvDataLoader(self.getLastTest())
                        eData = IceTerm.dataMerge([TData, eData])
                        eid += 1

                MData = IceTerm.dataMerge([MData, eData])
                if self.Logger.Stat:
                    self.Logger.Stat_BoundStateNumList.append(len(MData[1]))
                IceTerm.csvDataWriter(self.MLearnFile, MData)
                self.Logger.Log('[Info] Running the bound leaner...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Bound@{}'.format(checkRound))
                boundList = self.runMLearn()
                if self.Timeout != None and self.Logger.CalcTimePass('total') > self.Timeout:
                    continue
                if type(boundList) == type(None):
                    currentResult = {'Result': 'Unknown', 'Reason': 'MLearn failed.'}
                    continue
                if self.Logger.Stat:
                    self.Logger.Stat_BoundTimeList.append(self.Logger.CalcTimePass('Bound@{}'.format(checkRound)))
                    self.Logger.Stat_FinalBound = boundList
                    if self.Logger.Stat_LogAllBound:
                        self.Logger.Stat_BoundList.append(boundList)
                # append >0
                # boundList.append((self.IterateVar, '1'))

                ic.GenerateConcreteBplFile(boundList)
                retCBC = self.doCBC(boundList)
                if retCBC > 0:
                    self.Logger.Log('[Info] Running CBC...')
                    if self.Logger.Stat:
                        self.Logger.StartTimer('CBC@{}'.format(checkRound))
                    cc = CBChecker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResult = cc.ExecuteCBC(retCBC)
                    else:
                        currentResult = cc.ExecuteCBC(retCBC, timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(self.Logger.CalcTimePass('CBC@{}'.format(checkRound)))
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                        self.Logger.Stat_BMCTimeList.append(0)
                    continue
                else:
                    self.Logger.Stat_CBCTimeList.append(0)

                if self.UseBG0C:
                    self.Logger.Log('[Info] Running BG0C...')
                    self.Logger.StartTimer('BG0C@{}'.format(checkRound))
                    bc = BG0Checker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    bcRet, bcState = bc.ExecuteBG0C(boundList)
                    self.Logger.Stat_BG0CTimeList.append(self.Logger.CalcTimePass('BG0C@{}'.format(checkRound)))
                    if not bcRet:
                        currentResult = bcState
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BMCTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                        continue
                else:
                    self.Logger.Stat_BG0CTimeList.append(0)
                
                if self.BMC_Limit >= 0:
                    self.Logger.Log('[Info] Running BMC...')
                    self.Logger.StartTimer('BMC@{}'.format(checkRound))
                    bf = BMCFinder(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResultTmp = bf.ExecuteBMC(self.BMC_Limit)
                    else:
                        currentResultTmp = bf.ExecuteBMC(self.BMC_Limit, timeoutMonitor=self.TimeoutMonitor, timeout=min(self.BMC_Timeout, self.Timeout - 1 - int(self.Logger.CalcTimePass('total'))))
                    if currentResultTmp['Result'] in ['Failed-BMC']:
                        currentResult = currentResultTmp
                        if self.Logger.Stat:
                            self.Logger.Stat_BMCTimeList.append(self.Logger.CalcTimePass('BMC@{}'.format(checkRound)))
                            self.Logger.Stat_InvTimeList.append(0)
                            self.Logger.Stat_InvRefineNumList.append(0)
                        # print('[BMC:Debug] BMC found bound cex with bound {}, errorTraceLen {}'.format(tuple(map(lambda x:x[1], boundList)), list(map(len, currentResult['ErrorTrace']))))
                        continue
                    else:
                        # print('[BMC:Debug] BMC found no bound cex with bound {}. ({})'.format(tuple(map(lambda x:x[1], boundList)), currentResultTmp['Result']))
                        if self.Logger.Stat:
                            self.Logger.Stat_BMCTimeList.append(self.Logger.CalcTimePass('BMC@{}'.format(checkRound)))
                else:
                    self.Logger.Stat_BMCTimeList.append(0)


                self.Logger.Log('[Info] Running ICE...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Inv@{}'.format(checkRound))
                
                if self.Timeout == None:
                    currentResult = ic.ExecuteICE()
                else:
                    currentResult = ic.ExecuteICE(timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))

                if self.Logger.Stat:
                    self.Logger.Stat_InvTimeList.append(self.Logger.CalcTimePass('Inv@{}'.format(checkRound)))

            elif currentResult['Result'] == 'Starting':
                self.Logger.Log('[Info] Check round {}:'.format(checkRound))

                self.Logger.Log('[Info] Running the test...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Test@{}'.format(checkRound))
                self.runRandTest(TraceCEX=None, Testmode='rand')
                if self.Logger.Stat:
                    self.Logger.Stat_TestTimeList.append(self.Logger.CalcTimePass('Test@{}'.format(checkRound)))
                    self.Logger.Stat_TestStateNumList.append(self.testNumCount(self.getLastTest()))
                MData = IceTerm.csvDataLoader(self.getLastTest())
                if self.Logger.Stat:
                    self.Logger.Stat_BoundStateNumList.append(len(MData[1]))
                IceTerm.csvDataWriter(self.MLearnFile, MData)
                self.Logger.Log('[Info] Running the bound leaner...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Bound@{}'.format(checkRound))
                boundList = self.runMLearn()
                if self.Timeout != None and self.Logger.CalcTimePass('total') > self.Timeout:
                    continue
                if type(boundList) == type(None):
                    currentResult = {'Result': 'Unknown', 'Reason': 'MLearn failed.'}
                    continue
                if self.Logger.Stat:
                    self.Logger.Stat_BoundTimeList.append(self.Logger.CalcTimePass('Bound@{}'.format(checkRound)))
                    self.Logger.Stat_FinalBound = boundList
                    if self.Logger.Stat_LogAllBound:
                        self.Logger.Stat_BoundList.append(boundList)
                # append >0
                # boundList.append((self.IterateVar, '1'))

                ic.GenerateConcreteBplFile(boundList)
                retCBC = self.doCBC(boundList)
                if retCBC > 0:
                    self.Logger.Log('[Info] Running CBC...')
                    if self.Logger.Stat:
                        self.Logger.StartTimer('CBC@{}'.format(checkRound))
                    cc = CBChecker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResult = cc.ExecuteCBC(retCBC)
                    else:
                        currentResult = cc.ExecuteCBC(retCBC, timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                    if self.Logger.Stat:
                        self.Logger.Stat_CBCTimeList.append(self.Logger.CalcTimePass('CBC@{}'.format(checkRound)))
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BG0CTimeList.append(0)
                        self.Logger.Stat_InvRefineNumList.append(0)
                        self.Logger.Stat_CBCTimeList.append(0)
                    continue
                else:
                    self.Logger.Stat_CBCTimeList.append(0)

                if self.UseBG0C:
                    self.Logger.Log('[Info] Running BG0C...')
                    self.Logger.StartTimer('BG0C@{}'.format(checkRound))
                    bc = BG0Checker(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    bcRet, bcState = bc.ExecuteBG0C(boundList)
                    self.Logger.Stat_BG0CTimeList.append(self.Logger.CalcTimePass('BG0C@{}'.format(checkRound)))
                    if not bcRet:
                        currentResult = bcState
                        self.Logger.Stat_InvTimeList.append(0)
                        self.Logger.Stat_BMCTimeList.append(0) 
                        self.Logger.Stat_InvRefineNumList.append(0)
                        continue
                else:
                    self.Logger.Stat_BG0CTimeList.append(0)

                if self.BMC_Limit >= 0:
                    self.Logger.Log('[Info] Running BMC...')
                    self.Logger.StartTimer('BMC@{}'.format(checkRound))
                    bf = BMCFinder(self.Logger, self.TmpDir, self.TemplateBpl, self.VarList, self.IterateVar)
                    if self.Timeout == None:
                        currentResultTmp = bf.ExecuteBMC(self.BMC_Limit)
                    else:
                        currentResultTmp = bf.ExecuteBMC(self.BMC_Limit, timeoutMonitor=self.TimeoutMonitor, timeout=min(self.BMC_Timeout, self.Timeout - 1 - int(self.Logger.CalcTimePass('total'))))
                    if currentResultTmp['Result'] in ['Failed-BMC']:
                        currentResult = currentResultTmp
                        if self.Logger.Stat:
                            self.Logger.Stat_BMCTimeList.append(self.Logger.CalcTimePass('BMC@{}'.format(checkRound)))
                            self.Logger.Stat_InvTimeList.append(0)
                            self.Logger.Stat_InvRefineNumList.append(0)
                        # print('[BMC:Debug] BMC found bound cex with bound {}, errorTraceLen {}'.format(tuple(map(lambda x:x[1], boundList)), list(map(len, currentResult['ErrorTrace']))))
                        continue
                    else:
                        # print('[BMC:Debug] BMC found no bound cex with bound {}. ({})'.format(tuple(map(lambda x:x[1], boundList)), currentResultTmp['Result']))
                        if self.Logger.Stat:
                            self.Logger.Stat_BMCTimeList.append(self.Logger.CalcTimePass('BMC@{}'.format(checkRound)))
                else:
                    self.Logger.Stat_BMCTimeList.append(0)

                self.Logger.Log('[Info] Running ICE...')
                if self.Logger.Stat:
                    self.Logger.StartTimer('Inv@{}'.format(checkRound))
                if self.Timeout == None:
                    currentResult = ic.ExecuteICE()
                else:
                    currentResult = ic.ExecuteICE(timeoutMonitor=self.TimeoutMonitor, timeout=self.Timeout - 1 - int(self.Logger.CalcTimePass('total')))
                if self.Logger.Stat:
                    self.Logger.Stat_InvTimeList.append(self.Logger.CalcTimePass('Inv@{}'.format(checkRound)))

            elif currentResult['Result'] == 'Timeout':
                if self.Logger.Stat:
                    self.Logger.Stat_Result = 'Timeout'
                    self.Logger.Stat_TotalTime = self.Logger.CalcTimePass('total')
                    self.Logger.Stat_BoundRefineNum = checkRound - 1
                    return
            elif currentResult['Result'] == 'Unknown':
                if self.Logger.Stat:
                    self.Logger.Stat_Result = 'Unknown'
                    self.Logger.Stat_TotalTime = self.Logger.CalcTimePass('total')
                    self.Logger.Stat_BoundRefineNum = checkRound - 1
                    return
            else:
                raise RuntimeError('Unknown running state.')

    
    def doCBC(self, boundList):
        if self.CBC_Limit == 0:
            return -1
        # Lexical:
        if self.UseLexical:
            if len(boundList) != 1 or len(boundList[0]) != 1:
                return -1
            try:
                intV = int (boundList[0][0])
                if intV <= self.CBC_Limit:
                    if intV == self.LastCBC_Value:
                        # Turn off CBC
                        self.UseAdvancedCBC = False
                        self.CBC_Limit = -1
                        return -1
                    self.LastCBC_Value = intV
                    return intV
                return -1
            except ValueError:
                return -1
        # No Lexical
        if len(boundList) > 1:
            return -1
        try:
            intV = int (boundList[0][1])
            if intV <= self.CBC_Limit:
                return intV
            return -1
        except ValueError:
            return -1

    def runMLearnWithCBCAdvance(self, trace=None):
        maxBound = 0
        if type(trace) != type(None):
            for tr in trace:
                # import pdb; pdb.set_trace()
                if maxBound < tr.LoopIt + 1:
                    maxBound = tr.LoopIt + 1
        elif not self.UseLexical:
            with open(self.MLearnFile, 'r') as dataFile:
                lines = dataFile.readlines()
            for i in range(1, len(lines)):
                line = lines[i].replace(' ','').replace('\r','').replace('\t','').replace('\n','')
                if line == '':
                    continue
                lineRound = int(line.split(',')[-1])
                if lineRound > maxBound:
                    maxBound = lineRound
        else:
            for it in self.LexicalACBC_CEX:
                if it[1] > maxBound:
                    maxBound = it[1]
        if maxBound > self.CBC_Advance_Limit:
            return None
        else:
            nextCBC = self.CBC_Advance_Limit if maxBound + self.CBC_Advance > self.CBC_Advance_Limit else maxBound + self.CBC_Advance
            if nextCBC == self.LastCBC_Value:
                self.UseAdvancedCBC = False
                self.CBC_Limit = -1
                self.Logger.Log('[Info] Same ACBC bound ' + str(nextCBC) + '. Skip CBC in future.')
                return None
            self.Logger.Log('[Info] Use Advanced CBC: ' + str(nextCBC))
            return [(self.IterateVar, str(nextCBC))]

    def runMLearn(self):
        if self.UseAdvancedCBC:
            ACBC = self.runMLearnWithCBCAdvance()
            if ACBC != None:
                return ACBC
        mLearn = MLearn(self.Logger, self.MLearnFile)
        if mLearn.Vars.shape[0] == 0:
            return [(self.IterateVar, '1')]
        if self.MLearnStrategy == 'default':
            result = mLearn.Learning(target=self.MLearnTarget, ClusterNum = self.MLearnClusterNum)
        else:
            result = mLearn.Learning(strategy=self.MLearnStrategy, target=self.MLearnTarget, ClusterNum = self.MLearnClusterNum)

        if not result['success']:
            self.Logger.Log('[Warning] MLearn: {}'.format(result['message']))
            return None
            # raise RuntimeError(result['message'])
        A_List = result['Args']
        int_A_List = []
        for A in A_List:
            lineA = []
            for item in A:
                lineA.append(int(item))
            int_A_List.append(lineA)
        # print(int_A_List)
        boundList = []
        for A in int_A_List:
            boundExpr = IceCaller.GenerateExpr(['1'] + self.VarList, A, self.Logger)
            self.Logger.Log('[Info] One bound for {} is: {}'.format(self.IterateVar, boundExpr))
            boundList.append((self.IterateVar, boundExpr))
        return boundList



    def runLexicalMLearn(self, BoundLearningData, minRank=1, maxRank=3, CostFunc=LexicalL2Loss.__func__):
        if self.UseAdvancedCBC:
            # self.__IceCaller.GenerateConcreteBplFileLexicalTemplate([['1']])
            ACBC = self.runMLearnWithCBCAdvance()
            if ACBC != None:
                return [[ACBC[0][1]]]
        if self.LexicalStrategy == 'SimExprBest':
            self.__LexicalMLStrategy = 'single-best'
            return self.runLexicalMLearnExprBest(BoundLearningData, minRank, maxRank, CostFunc)
        elif self.LexicalStrategy == 'SimExpr':
            self.__LexicalMLStrategy = 'single-best'
            return self.runLexicalMLearnSimExpr(BoundLearningData, minRank, maxRank)
        elif self.LexicalStrategy == 'ExprBest':
            raise RuntimeError('Only support single expr when using state diff.')
            # self.__LexicalMLStrategy = 'CLearn-single-best'
            # return self.runLexicalMLearnExprBest(BoundLearningData, minRank, maxRank, CostFunc)
        else:
            raise RuntimeError('Unknown Lexical MLearn Strategy.')


    # Try to find best lexical according to costFunc
    def runLexicalMLearnExprBest(self, BoundLearningData, minRank=1, maxRank=3, CostFunc=LexicalL2Loss.__func__):
        MDataDict = TraceStateTrans.TestDataTR2mDataDict(BoundLearningData, appendRName=self.RoundVar)
        MDataDictV0 = TraceStateTrans.TestDataTR2mDataDict(BoundLearningData, appendRName=self.RoundVar, appendValue = 0)
        self.LexicalAllStateMData = TraceStateTrans.TestDataP2mData(BoundLearningData, appendRName=self.RoundVar)
        # print('[Debug] MDataDict:', MDataDict)
        # print('[Debug] MDataDictV0:', MDataDictV0)

        self.Logger.Log('[Info] Trace NUM:{}'.format(len(MDataDict.keys())), level=5)
        self.runLexicalMLearnInit(MDataDict, MDataDictV0, minRank, maxRank)
        self.LexicalBoundGenerator = self.runLexicalMLearnGenerator(minRank, maxRank)

        bestLexical = None
        bestCost = None
        while True:
            nextRst = next(self.LexicalBoundGenerator)
            if nextRst == None:
                break
            for rankLevel in range(self.LexicalCurrentRank):
                rankLevelList = []
                for idx in range(len(self.LexicalIDInDistribution)):
                    if self.LexicalIDInDistribution[idx] == rankLevel:
                        rankLevelList.append(self.LexicalID2Trace[idx])
                self.Logger.Log('[Info] Lexical {} of {} is: {}'.format(rankLevel, self.LexicalCurrentRank, rankLevelList))
            # import pdb; pdb.set_trace()
            costCurrent = CostFunc(nextRst)
            self.Logger.Log('[Info] Lexical candidate: {}; Cost: {}.'.format(nextRst, costCurrent))
            if bestLexical == None or bestCost > costCurrent:
                bestLexical = nextRst
                bestCost = costCurrent
        # import pdb; pdb.set_trace()
        if bestLexical == None:
            self.Logger.Log('[Info] No lexical result found! rank({}-{})'.format(minRank,maxRank), level=1)
            return None
        self.Logger.Log('[Info] Best lexical candidate: {}.'.format(bestLexical))
            
        nextRstAddConst = []
        for it in bestLexical:
            exprList = []
            for itt in it:
                boundExpr = IceCaller.GenerateExpr(['1'] + self.VarList, itt, self.Logger)
                exprList.append(boundExpr)
            nextRstAddConst.append(exprList)

        return nextRstAddConst


        
    def runLexicalMLearnSimExpr(self, BoundLearningData, minRank=1, maxRank=3):
        MDataDict = TraceStateTrans.TestDataTR2mDataDict(BoundLearningData, appendRName=self.RoundVar)
        MDataDictV0 = TraceStateTrans.TestDataTR2mDataDict(BoundLearningData, appendRName=self.RoundVar, appendValue = 0)
        self.LexicalAllStateMData = TraceStateTrans.TestDataP2mData(BoundLearningData, appendRName=self.RoundVar)
        # print('[Debug] MDataDict:', MDataDict)
        # print('[Debug] MDataDictV0:', MDataDictV0)

        self.Logger.Log('[Info] Trace NUM:{}'.format(len(MDataDict.keys())), level=5)
        # self.LexicalMDataDict = MDataDict
        # for tr in MDataDict.keys():
        #     if tr not in self.LexicalID2Trace:
        #         self.LexicalID2Trace.append(tr)
        # if self.LexicalBoundGenerator == None:
        #     self.LexicalBoundGenerator = self.runLexicalMLearnGenerator(minRank, maxRank)
        lastTraceLen = len(self.LexicalID2Trace)
        self.runLexicalMLearnInit(MDataDict, MDataDictV0, minRank, maxRank)
        # self.Logger.Log('[Debug] Current distribution is {}'.format(self.LexicalDistribution))
        # self.Logger.Log('[Debug] Current distribution0 is {}'.format(self.LexicalDistributionV0))
        # Recheck current
        nextRst = None
        if self.LexicalBoundGenerator != None and self.LexicalUnsatNum == 0 and lastTraceLen == len(self.LexicalID2Trace):
            # return list(map(lambda x: x[-1], self.LexicalDistributionResult))
            nextRst = self.runLexicalFinalResult(self.LexicalCurrentRank)

        if self.LexicalBoundGenerator == None:
            self.LexicalBoundGenerator = self.runLexicalMLearnGenerator(minRank, maxRank)

        if nextRst == None:
            nextRst = next(self.LexicalBoundGenerator)

        # while nextRst != None:
        #     print(nextRst)
        #     nextRst = next(self.LexicalBoundGenerator)

        # import pdb; pdb.set_trace()

        if nextRst == None:
            self.Logger.Log('[Info] No lexical result found! rank({}-{})'.format(minRank,maxRank), level=1)
            return None

        # allState = []
        # for it in BoundLearningData:
        #     allState.append(it.Begin)
        #     allState.append(it.End)

        # allState = list(set(allState))

        # constList = []
        # nextRstAddConst = []
        # for it in nextRst:
        #     constList.append(0)
        #     if len(it) != 1:
        #         raise RuntimeError('Only support len = 1 lexical.')
        #     A = np.array(it[0])
        #     for s in allState:
        #         snp = np.array(s)
        #         val = np.dot(A, snp.T)
        #         if val + constList[-1] <= 0:
        #             constList[-1] = - val + 1
        #     # if constList[-1] >= self.LexicalConstMax:
        #     #     constList[-1] = self.LexicalLastLargeConst * 2
        #     #     self.LexicalLastLargeConst = constList[-1]
        #     boundExpr = IceCaller.GenerateExpr(['1'] + self.VarList, [constList[-1]] + it[0], self.Logger)
            
        #     nextRstAddConst.append([boundExpr])
        
        nextRstAddConst = []
        for it in nextRst:
            boundExpr = IceCaller.GenerateExpr(['1'] + self.VarList, it[0], self.Logger)
            nextRstAddConst.append([boundExpr])

        return nextRstAddConst

    def runLexicalMLearnInit(self, MDataDict, MDataDictV0, minRank=1, maxRank=3):
        effectSet = set()
        # print('[Debug]', 'MD', MDataDict, 'MD0', MDataDictV0)
        for idx in range(len(self.LexicalIDInDistribution)):
            targetDist = self.LexicalIDInDistribution[idx]
            traceName = self.LexicalID2Trace[idx]
            constraintNew = set(MDataDict[traceName][1])
            constraintOld = set(self.LexicalMDataDict[traceName][1])
            if len(constraintNew - constraintOld) == 0:
                continue
            else:
                effectSet.add(targetDist)
        # print('[Debug] effectSet:', effectSet)
        for it in effectSet:
            self.LexicalDistribution[it] = []
            self.LexicalDistributionV0[it] = []
            lastResult = self.LexicalDistributionResult[it]
            if lastResult == None:
                raise RuntimeError('Last Result should never be None.')
            self.LexicalDistributionResult[it] = []
            for idx in range(len(self.LexicalIDInDistribution)):
                if self.LexicalIDInDistribution[idx] == it:
                    traceName = self.LexicalID2Trace[idx]
                    self.LexicalDistribution[it].append(MDataDict[traceName])
                    self.LexicalDistributionV0[it].append(MDataDictV0[traceName])
            self.runLexicalMLearnCheck(it)

        self.LexicalMDataDict = MDataDict
        self.LexicalMDataDictV0 = MDataDictV0
        # print('[Debug]', 'MD', self.LexicalMDataDict, 'MD0', self.LexicalMDataDictV0)

        for tr in MDataDict.keys():
            if tr not in self.LexicalID2Trace:
                self.LexicalID2Trace.append(tr)

    def runLexicalMLearnGenerator(self, minRank=1, maxRank=3):
        # print('[Debug]', maxRank)
        for rank in range(minRank, maxRank+1):
            self.Logger.Log('[Info] Current rank is {}'.format(rank))
            self.LexicalDistribution = []
            self.LexicalDistributionV0 = []
            self.LexicalDistributionResult = []
            self.LexicalIDInDistribution = []
            self.LexicalUnsatNum = 0
            for _ in range(rank):
                self.LexicalDistribution.append(list([]))
                self.LexicalDistributionV0.append(list([]))
                self.LexicalDistributionResult.append(list([]))
            self.LexicalCurrentRank = rank
            yield from self.runLexicalMLearnGeneratorDFS(0, rank)
        yield None

    def runLexicalMLearnGeneratorDFS(self, now, rank):
        # self.Logger.Log('[Debug] ==================')
        # self.Logger.Log('[Debug] Current distribution is {}'.format(self.LexicalDistribution))
        # self.Logger.Log('[Debug] Current distribution0 is {}'.format(self.LexicalDistributionV0))
        # self.Logger.Log('[Debug] LexicalID2Trace: {}'.format(self.LexicalID2Trace))
        # self.Logger.Log('[Debug] distributionResult: {}'.format(self.LexicalDistributionResult))
        # self.Logger.Log('[Debug] DFS now: {}'.format(now))
        if now == len(self.LexicalID2Trace):            
            # self.Logger.Log('[Debug] Trying end.')
            
            finalResult = self.runLexicalFinalResult(rank)
            # import pdb; pdb.set_trace()
            if finalResult != None:
                yield finalResult
        else:
            for r in range(rank):
                # self.Logger.Log('[Debug] Trying rank-r: {}'.format(r))

                self.LexicalDistribution[r].append(self.LexicalMDataDict[self.LexicalID2Trace[now]])
                self.LexicalDistributionV0[r].append(self.LexicalMDataDictV0[self.LexicalID2Trace[now]])
                self.LexicalIDInDistribution.append(r)
                # self.Logger.Log('[Debug] Current distribution is {}'.format(self.LexicalDistribution))
                # self.Logger.Log('[Debug] Current distribution0 is {}'.format(self.LexicalDistributionV0))
                # self.Logger.Log('[Debug] LexicalIDInDistribution: {}'.format(self.LexicalIDInDistribution))

                #CheckSAT
                self.runLexicalMLearnCheck(r)
                if self.LexicalUnsatNum == 0:
                    yield from self.runLexicalMLearnGeneratorDFS(now+1,rank)
                # del self.LexicalDistribution[r][-1]
                self.runLexicalMLearnCheckPOP(r)
                del self.LexicalIDInDistribution[-1]
                # if len(self.LexicalDistribution[r]) == 0:
                #     break

    def runLexicalFinalResult(self, rank):
        for i in range(rank):
            if len(self.LexicalDistribution[i]) == 0:
                return None
        FinalResult = []
        for i in range(rank):
            mergeList = list(self.LexicalDistribution[i])
            for j in range(i + 1, rank):
                mergeList += self.LexicalDistributionV0[j]
            # print(mergeList)
            if self.__LexicalMLStrategy in ['single-best']:
                mergeList += [self.LexicalAllStateMData, self.LexicalSimpFailedMData]
                # print(mergeList)
                mergedData = self.dataMerge(mergeList)
                result = self.runLexicalMLearnCheckRaw(mergedData)
            elif self.__LexicalMLStrategy in ['CLearn-single-best']:
                mergedDataHard = self.dataMerge(mergeList)
                mergedDataSoft = self.dataMerge([self.LexicalAllStateMData, self.LexicalSimpFailedMData])
                result = self.runLexicalMLearnCheckRawHS(mergedDataHard, mergedDataSoft)
            else:
                raise RuntimeError('Unknown ML strategy.')
            if result['success']:
                A_List = result['Args']
                int_A_List = []
                for A in A_List:
                    lineA = []
                    for item in A:
                        lineA.append(int(item))
                    int_A_List.append(lineA)
                FinalResult.append(int_A_List)
            else:
                return None
        return FinalResult

    def runLexicalMLearnCheck(self, checkID):
        mergedData = self.dataMerge(self.LexicalDistribution[checkID])
        result = self.runLexicalMLearnCheckRaw(mergedData)

        if result['success']:
            A_List = result['Args']
            int_A_List = []
            for A in A_List:
                lineA = []
                for item in A:
                    lineA.append(int(item))
                int_A_List.append(lineA)
            self.LexicalDistributionResult[checkID].append(int_A_List)
            # return True
        else:
            self.LexicalDistributionResult[checkID].append(None)
            self.LexicalUnsatNum += 1
            # return False

    def runLexicalMLearnCheckRaw(self, mergedData):
        mergedData[1].sort()
        knowledgeKey = tuple(mergedData[1])
        if knowledgeKey in self.LexicalMLearnKnowledge.keys():
            return self.LexicalMLearnKnowledge[knowledgeKey]
        self.csvDataWriter(self.MLearnFile, mergedData)
        
        mLearn = MLearn(self.Logger, self.MLearnFile, add1=False)
        # result = mLearn.Learning(strategy='single-best')
        if self.MLearnStrategy == 'default':
            result = mLearn.Learning(strategy=self.__LexicalMLStrategy, target=self.MLearnTarget, ClusterNum = self.MLearnClusterNum)
        else:
            result = mLearn.Learning(strategy=self.MLearnStrategy, target=self.MLearnTarget, ClusterNum = self.MLearnClusterNum)

        self.LexicalMLearnKnowledge[knowledgeKey] = result
        # print('[Debug] mergedData:', mergedData)
        # print('[Debug] MLR:', result)
        return result
        
    def runLexicalMLearnCheckRawHS(self, mergedDataH, mergedDataS):
        mergedDataH[1].sort()
        realSoftDataList = list(set(mergedDataS[1]) - set(mergedDataH[1]))
        realSoftDataList.sort()
        knowledgeKey = (tuple(mergedDataH[1]), tuple(realSoftDataList))

        if knowledgeKey in self.LexicalMLearnKnowledge.keys():
            return self.LexicalMLearnKnowledge[knowledgeKey]
        mergedData = (mergedDataH[0], realSoftDataList + mergedDataH[1])
        self.csvDataWriter(self.MLearnFile, mergedData)
        softLen = len(realSoftDataList)
        
        mLearn = MLearn(self.Logger, self.MLearnFile, add1=False)
        # result = mLearn.Learning(strategy='single-best')
        if self.MLearnStrategy == 'default':
            result = mLearn.Learning(strategy=self.__LexicalMLStrategy, softLen=softLen, target=self.MLearnTarget, ClusterNum = self.MLearnClusterNum)
        else:
            result = mLearn.Learning(strategy=self.MLearnStrategy, softLen=softLen, target=self.MLearnTarget, ClusterNum = self.MLearnClusterNum)

        self.LexicalMLearnKnowledge[knowledgeKey] = result
        # print('[Debug] mergedData:', mergedData)
        # print('[Debug] MLR:', result)
        return result

    def runLexicalMLearnCheckPOP(self, checkID):
        # print('[Debug] === POP ===')
        # print('LexicalDistribution', self.LexicalDistribution)
        del self.LexicalDistribution[checkID][-1]
        del self.LexicalDistributionV0[checkID][-1]
        if len(self.LexicalDistributionResult[checkID]) == 0:
            raise RuntimeError('POP an empty distribution')
        else:
            lastone = self.LexicalDistributionResult[checkID][-1]
            # print('[DEBUG]', self.LexicalDistributionResult[checkID],'A')
            del self.LexicalDistributionResult[checkID][-1]
            # print('[DEBUG]', self.LexicalDistributionResult[checkID],'B')

            if len(self.LexicalDistributionResult[checkID]) == 0:
                if len(self.LexicalDistribution[checkID]) > 0:
                    self.runLexicalMLearnCheck(checkID)
                    # print('[DEBUG]', self.LexicalDistributionResult[checkID],'D')
                else:
                    if type(lastone) == type(None):
                        self.LexicalUnsatNum -= 1
                    return
            # print('[DEBUG]', self.LexicalDistributionResult[checkID],'C')
            nowlast = self.LexicalDistributionResult[checkID][-1]
            if type(nowlast) != type(None) and type(lastone) == type(None):
                self.LexicalUnsatNum -= 1
            elif type(nowlast) == type(None) and type(lastone) != type(None):
                raise RuntimeError('SAT Error happened when popping.')

            


    def runIceCaller(self, MList):
        iceCaller = IceCaller(self.Logger, self.TmpDir, self.TemplateBpl, self.IceLearner, posReuse = self.posReuse, negReuse = self.negReuse, impReuse = self.impReuse, balanceReuse = self.balanceReuse, paramsReuse = self.paramsReuse)
        iceCaller.GenerateConcreteBplFile(MList)
        result = iceCaller.ExecuteICE()
        if result['Result'] == 'Verified':
            self.Logger.Log('Termination proved!')
            for item in MList:
                self.Logger.Log('The bound of {} is: {}'.format(item[0],item[1]))
            self.Logger.Log('The loop invariant is: {}'.format(result['Invariant']))
        elif result['Result'] == 'Failed':
            self.Logger.Log('An error trace found with current bound!')
            for item in MList:
                self.Logger.Log('The bound of {} is: {}'.format(item[0],item[1]))
        else:
            raise ValueError('Unexpected result value')
        
        return result['Result']

    def specificRand(self, originalFunc):
        def retFunc():
            data = originalFunc()
            if 'Test:Eq' in self.Setting.keys():
                # print('CC')
                EqSet = set(self.Setting['Test:Eq'])
                shareVal = None
                for i in range(len(self.VarList)):
                    v = self.VarList[i]
                    if v in EqSet:
                        # print('AA')
                        if shareVal == None:
                            shareVal = data[i]
                        else:
                            data[i] = shareVal
            if 'Test:Sp' in self.Setting.keys():
                spFunc = self.Setting['Test:Sp']
                data = spFunc(data)
            # print(data)
            return data
        return retFunc
    
    def runRandTestLexical(self, TraceCEX, Testmode = 'rand', testOption = 'default', oncetimeout = None):
        self.TestID += 1
        if oncetimeout == None:
            oncetimeout = self.OnceTestTimeout
        if oncetimeout != None and oncetimeout < 0:
            self.Logger.Log('[Warning] Test timeout {}s. Skip!'.format(self.OnceTestTimeout))
            return []
        if TraceCEX == None:
            if Testmode == 'rand':
                if oncetimeout != None:
                    self.Logger.StartTimer('TEST_TO')
                rt = RandTester(self.Logger, self.VarList, self.ExecFile)
                randFunc = self.specificRand(rt.randFunction(lb=self.TestLB, ub=self.TestUB))
                testResult = rt.generateBoundLexical(randFunc, round=self.TestRound, duplicate=self.LexicalStrategy.startswith('Trace'), testOption=testOption)
                if oncetimeout != None:
                    timePass = self.Logger.CalcTimePass('TEST_TO')
                    oncetimeout -= timePass
                if len(testResult) == 0:
                    if type(self.TestLB) == list:
                        self.TestLB = map(lambda x: x-50, self.TestLB)
                    else:
                        self.TestLB -= 50

                    if type(self.TestUB) == list:
                        self.TestUB = map(lambda x: x+50, self.TestUB)
                    else:
                        self.TestUB += 50
                    self.TestRound += 10
                    self.Logger.Log('No data output from the test. Retest with LB = {}, UB = {}, R = {}'.format(self.TestLB, self.TestUB, self.TestRound))
                    testResult = self.runRandTestLexical(TraceCEX, Testmode, testOption, oncetimeout)
                return testResult
            else:
                raise NotImplementedError('Test mode {} not support yet.'.format(Testmode))
        else:
            if Testmode == 'rand':
                rt = RandTester(self.Logger, self.VarList, self.ExecFile)
                randFunc = self.specificRand(rt.randFunction(lb=self.TestNBLB, ub=self.TestNBUB, strategy='nearby', nearby=TraceCEX))
            
                testResult = rt.generateBoundLexical(randFunc, round=self.TestNBRound, duplicate=self.LexicalStrategy.startswith('Trace'), testOption=testOption)
                return testResult

            elif Testmode == 'target':
                rt = RandTester(self.Logger, self.VarList, self.ExecFile)
                testResult = rt.generateBoundLexical(rt.randFunction(lb=0, ub=0, strategy='nearby', nearby=TraceCEX), round=1, duplicate=self.LexicalStrategy.startswith('Trace'), testOption=testOption)    
                return testResult

            else:
                raise NotImplementedError('Test mode {} not support yet.'.format(Testmode))
                


    def runRandTest(self, TraceCEX = None, Testmode = 'rand', oncetimeout = None):
        self.TestID += 1
        if oncetimeout == None:
            oncetimeout = self.OnceTestTimeout
        if oncetimeout != None and oncetimeout < 0:
            outputFileName = os.path.join(self.TestRoundDir, 'TEST_{}_{}.csv'.format(self.TaskName, self.TestID))
            with open(outputFileName, 'w') as ow:
                outputLine = reduce(lambda x,y: '{},{}'.format(x,y), self.VarList+[self.RoundVar])
                ow.write(outputLine+'\n')
            self.Logger.Log('[Warning] Test timeout {}s. Skip!'.format(self.OnceTestTimeout))
            return
        if TraceCEX == None:
            if Testmode == 'rand':
                if oncetimeout != None:
                    self.Logger.StartTimer('TEST_TO')
                rt = RandTester(self.Logger, self.VarList, self.ExecFile)
                outputFileName = os.path.join(self.TestRoundDir, 'TEST_{}_{}.csv'.format(self.TaskName, self.TestID))
                randFunc = self.specificRand(rt.randFunction(lb=self.TestLB, ub=self.TestUB))
                rt.generateBound(randFunc, round=self.TestRound, duplicate=False, outputFile=outputFileName)
                if oncetimeout != None:
                    timePass = self.Logger.CalcTimePass('TEST_TO')
                    oncetimeout -= timePass
                if self.testNumCount(outputFileName) == 0:
                    if type(self.TestLB) == list:
                        self.TestLB = map(lambda x: x-50, self.TestLB)
                    else:
                        self.TestLB -= 50

                    if type(self.TestUB) == list:
                        self.TestUB = map(lambda x: x+50, self.TestUB)
                    else:
                        self.TestUB += 50
                    # self.TestRound += 10
                    self.Logger.Log('No data output from the test. Retest with LB = {}, UB = {}, R = {}'.format(self.TestLB, self.TestUB, self.TestRound))
                    self.runRandTest(TraceCEX, Testmode, oncetimeout)
            else:
                raise NotImplementedError('Test mode {} not support yet.'.format(Testmode))
        else:
            if Testmode == 'rand':
                rt = RandTester(self.Logger, self.VarList, self.ExecFile)
                outputFileName = os.path.join(self.TestRoundDir, 'TEST_{}_{}.csv'.format(self.TaskName, self.TestID))
                randFunc = self.specificRand(rt.randFunction(lb=self.TestNBLB, ub=self.TestNBUB, strategy='nearby', nearby=TraceCEX))
            
                rt.generateBound(randFunc, round=self.TestNBRound, duplicate=False, outputFile=outputFileName)
                # if self.testNumCount(outputFileName) == 0:
                #     print('ReTest...')
                #     self.TestLB -= 50
                #     self.TestUB += 50
                #     self.TestRound += 10
                #     self.runRandTest(TraceCEX, Testmode)
            elif Testmode == 'target':
                rt = RandTester(self.Logger, self.VarList, self.ExecFile)
                outputFileName = os.path.join(self.TestRoundDir, 'TEST_{}_{}.csv'.format(self.TaskName, self.TestID))
                rt.generateBound(rt.randFunction(lb=0, ub=0, strategy='nearby', nearby=TraceCEX), round=1, duplicate=False, outputFile=outputFileName)    
            else:
                raise NotImplementedError('Test mode {} not support yet.'.format(Testmode))
                
    def testNumCount(self, fileName):
        num = 0
        with open(fileName) as fopen:
            content = fopen.read()
            num = content.count('\n')
        return num - 1

    def getLastTest(self):
        return os.path.join(self.TestRoundDir, 'TEST_{}_{}.csv'.format(self.TaskName, self.TestID))

    @staticmethod
    def csvDataLoader(csvFile):
        if not os.path.exists(csvFile):
            return (None, [])
        csvFileReader = open(csvFile)
        lines = csvFileReader.readlines()
        cleanEmpty = lambda s: s.replace(' ','').replace('\t','').replace('\r','').replace('\n','')
        title = cleanEmpty(lines[0]).split(',')
        data = []
        for line in lines[1:]:
            cline = cleanEmpty(line)
            if cline == '':
                continue
            else:
                data.append(cline.split(','))

        csvFileReader.close()
        return (title, data)

    @staticmethod
    def csvDataWriter(csvFile, csvData):
        title = csvData[0]
        data = csvData[1]
        csvOutput = ''
        if title == None:
            raise ValueError('No title data!')
        csvFormat = lambda items: str(reduce(lambda x,y: '{},{}'.format(x,y), items)) + '\n'
        csvOutput += csvFormat(title)
        for item in data:
            # import pdb; pdb.set_trace()
            csvOutput += csvFormat(item)
        csvFileWriter = open(csvFile, 'w')
        csvFileWriter.write(csvOutput)
        csvFileWriter.close()
        
    def dataMakeFromErrorList(self, title, errorList):
        dataList = []
        # import pdb; pdb.set_trace()
        for e in errorList:
            dataLine = []
            for it in title:
                if it == self.RoundVar:
                    dataLine.append(e[1])
                elif not it in e[0].keys():
                    self.Logger.Log('Unknown var: {}'.format(it))
                    self.Logger.Log('Vars are: {}'.format(e[0].keys()))
                    raise RuntimeError('Unknown var in title when find an error.')
                else:
                    dataLine.append(e[0][it])
            dataList.append(dataLine)
        return (title, dataList)

    @staticmethod
    def mDictMerge2(dict1, dict2):
        newDict = {}
        for nk in dict1.keys():
            if nk in dict2.key():
                newDict[nk] = IceTerm.dataMerge([dict1[nk], dict2[nk]])
            else:
                newDict[nk] = IceTerm.dataMerge([dict1[nk]])
        for nk in dict2.key():
            if nk not in dict1.key():
                newDict[nk] = IceTerm.dataMerge([dict2[nk]])
        return newDict

    @staticmethod
    def dataMerge(dataList, duplicate = False):
        title = None
        dataLen = None
        data = []
        for item in dataList:
            itemTitle = item[0]
            if itemTitle != None:
                if title == None:
                    title = tuple(itemTitle)
                else:
                    if title != tuple(itemTitle):
                        raise ValueError('Title of data is not same.')

        duplicateSet = {}
        if title != None:
            dataLen = len(title)
        for item in dataList:
            itemData = item[1]
            for dataLine in itemData:
                tupleDataLine = tuple(dataLine)
                if not duplicate:
                    # print(tupleDataLine)
                    if tupleDataLine in duplicateSet.keys():
                        continue
                    duplicateSet[tupleDataLine] = True
                if dataLen == None:
                    dataLen = len(tupleDataLine)
                if dataLen != len(tupleDataLine):
                    print(tupleDataLine, title)
                    raise ValueError('Data length is not same.')
                data.append(tupleDataLine)
        
        return (title, data)
            

