import os
import re
import subprocess
import shutil
from functools import reduce
import random

class IceCaller:
    
    @staticmethod
    def prettyInv(logger, invRaw):
        invRaw = invRaw.strip()
        invSplit = invRaw.split(' ')
        for i in range(len(invSplit)):
            it = invSplit[i]
            if it.startswith('ATTR$') or it.startswith('ATTM$'):
                # print(it)
                invSplit[i] = '({})'.format(IceCaller.TranslateExpr(it, logger))
        invM = reduce(lambda x,y: '{} {}'.format(x,y), invSplit)
        return invM

    # def __init__(self, logger, vars, tmpDir, tempfile, learner = 'dt_penalty', posReuse = '', negReuse = '', impReuse = '', balanceReuse = None, paramsReuse = {}):
    def __init__(self, logger, vars, tmpDir, tempfile, learner = 'dt_penalty', posReuse = 'test', negReuse = 'test', impReuse = '', balanceReuse = None, paramsReuse = {'max_abslute_size':3,'max_relative_size':10}):
        self.Logger = logger
        self.Vars = vars
        self.tmpDir = tmpDir
        self.tempfile = tempfile
        self.ReList = [r'(.*)%M:(.*)%(.*)',r'(.*)%Decl:(.*)%(.*)',r'(.*)%Inv:(.*)%(.*)']
        self.LexicalReList = [r'(.*)%FD%(.*)',r'(.*)%VD%(.*)',r'(.*)%BE%(.*)',r'(.*)%IC%(.*)',r'(.*)%BT%(.*)',r'(.*)%IT%(.*)']
        self.fileName = None
        self.projectDir = '/'.join(os.getcwd().split('/'))
        self.boogieDir = self.projectDir + '/ice/popl16_artifact/Boogie/Binaries'
        self.boogieArgs = ['/noinfer', '/contractInfer', '/mlHoudini:{}'.format(learner), 
            '/printAssignment', '/trace']
        
        if self.Logger.SMTFile != None:
            self.boogieArgs.append('/proverLog:{}'.format(self.Logger.SMTFile))

        fileName = self.tempfile.split('/')[-1]
        if not os.path.exists(self.tmpDir):
            os.makedirs(self.tmpDir)
        outFile = os.path.join(self.tmpDir, fileName)
        self.fileName = outFile

        self.PosReuse = posReuse
        self.NegReuse = negReuse
        self.ImpReuse = impReuse
        self.IfReuse = (posReuse != '' or negReuse != '' or impReuse != '')
        self.BalanceReuse = balanceReuse
        # self.BalanceReuse = None
        self.ParamsReuse = paramsReuse

    def CleanTmpFiles(self):
        if os.path.exists(self.tmpDir) and os.path.isdir(self.tmpDir):
            shutil.rmtree(self.tmpDir)

    @staticmethod
    def L2_Loss_Single(item):
        retVal = 0
        for it in item:
            retVal += it ** 2
        return retVal

    @staticmethod
    def L2_Loss_Double(item):
        retVal = 0
        for it in item[0]:
            retVal += it ** 2
        for it in item[1]:
            retVal += it ** 2
        return retVal

    def ICE_DataReuse(self, itVar='i', reuseSuffix='.rus'):
        if os.path.exists(self.fileName + reuseSuffix): # Always try to remove the reuse file
            os.remove(self.fileName + reuseSuffix)
        
        if not self.IfReuse or type(itVar) != str:
            return
        ReuseDict = {'Pos': [], 'Neg': [], 'Imp': []}
        self.ParamsReuse['max_abslute_size'] = min(len(self.Vars) + 1, self.ParamsReuse['max_abslute_size'])

        if 'test' in self.PosReuse or 'test' in self.NegReuse:
            TestReusePos, TestReuseNeg = self.ICE_DataReuseTest(itVar)

            TestReusePos.sort(key=lambda x: sum(map(abs, x)))
            TestReuseNeg.sort(key=lambda x: max(map(abs, x)))
            if 'test' in self.PosReuse:
                ReuseDict['Pos'].extend(TestReusePos)
            if 'test' in self.NegReuse:
                ReuseDict['Neg'].extend(TestReuseNeg)
        if 'ice' in self.NegReuse or 'ice' in self.ImpReuse:
            IceReuseNeg, IceReuseImp = self.ICE_DataReuseICE()
            if 'ice' in self.NegReuse:
                ReuseDict['Neg'].extend(IceReuseNeg)
            if 'ice' in self.ImpReuse:
                ReuseDict['Imp'].extend(IceReuseImp)
        # elif self.NegReuse:
        #     ReuseDict['Neg'], _ = self.ICE_DataReuseICE()
        # elif self.ImpReuse:
        #     _, ReuseDict['Imp'] = self.ICE_DataReuseICE()
        if ReuseDict['Pos'] != None and len(ReuseDict['Pos']) > 0:
            ReuseDict['Pos'] = list(set(ReuseDict['Pos']))
            if self.BalanceReuse == 'rand':
                random.shuffle(ReuseDict['Pos'])
            elif self.BalanceReuse == 'L2_sort':
                ReuseDict['Pos'].sort(key=IceCaller.L2_Loss_Single)
            elif self.BalanceReuse == 'L2_sort_R':
                ReuseDict['Pos'].sort(key=IceCaller.L2_Loss_Single, reverse=True)
            elif self.BalanceReuse == None:
                ...
            else:
                raise RuntimeError('Unsupported balance strategy.')
        if ReuseDict['Neg'] != None and len(ReuseDict['Neg']) > 0:
            ReuseDict['Neg'] = list(set(ReuseDict['Neg']))
            if self.BalanceReuse == 'rand':
                random.shuffle(ReuseDict['Neg'])
            elif self.BalanceReuse == 'L2_sort':
                ReuseDict['Neg'].sort(key=IceCaller.L2_Loss_Single)
            elif self.BalanceReuse == 'L2_sort_R':
                ReuseDict['Neg'].sort(key=IceCaller.L2_Loss_Single, reverse=True)
            elif self.BalanceReuse == None:
                ...
            else:
                raise RuntimeError('Unsupported balance strategy.')
        if ReuseDict['Imp'] != None and len(ReuseDict['Imp']) > 0:
            ReuseDict['Imp'] = list(set(ReuseDict['Imp']))
            if self.BalanceReuse == 'rand':
                random.shuffle(ReuseDict['Imp'])
            elif self.BalanceReuse == 'L2_sort':
                ReuseDict['Imp'].sort(key=IceCaller.L2_Loss_Double)
            elif self.BalanceReuse == 'L2_sort_R':
                ReuseDict['Imp'].sort(key=IceCaller.L2_Loss_Double, reverse=True)
            elif self.BalanceReuse == None:
                ...
            else:
                raise RuntimeError('Unsupported balance strategy.')

        if self.BalanceReuse != None and ReuseDict['Pos'] != None and ReuseDict['Neg'] != None:
            ReuseNum = min(len(ReuseDict['Pos']), len(ReuseDict['Neg'])) + 10
            ReuseDict['Pos'] = ReuseDict['Pos'][:ReuseNum] # pylint:disable=unsubscriptable-object
            ReuseDict['Neg'] = ReuseDict['Neg'][:ReuseNum] # pylint:disable=unsubscriptable-object
            if ReuseDict['Imp'] != None:
                ReuseDict['Imp'] = ReuseDict['Imp'][:ReuseNum] # pylint:disable=unsubscriptable-object


        posinfo = 'skip Pos' if type(ReuseDict['Pos']) == type(None) else '{} Pos'.format(len(ReuseDict['Pos']))
        neginfo = 'skip Neg' if type(ReuseDict['Neg']) == type(None) else '{} Neg'.format(len(ReuseDict['Neg']))
        impinfo = 'skip Imp' if type(ReuseDict['Imp']) == type(None) else '{} Imp'.format(len(ReuseDict['Imp']))
        self.Logger.Log('[Info] ICE reuse with {}, {} and {}.'.format(posinfo, neginfo, impinfo), level=0)
        with open(self.fileName + reuseSuffix, 'w') as rusWriter:
            for item in self.ParamsReuse:
                rusWriter.write('Parameter:{}={}\n'.format(item, self.ParamsReuse[item]))
            if not type(ReuseDict['Pos']) == type(None):
                for it in ReuseDict['Pos']: # pylint:disable=not-an-iterable
                    rusWriter.write('Pos:{}\n'.format(it))
            if not type(ReuseDict['Neg']) == type(None):
                for it in ReuseDict['Neg']: # pylint:disable=not-an-iterable
                    rusWriter.write('Neg:{}\n'.format(it))
            if not type(ReuseDict['Imp']) == type(None):
                for it in ReuseDict['Imp']: # pylint:disable=not-an-iterable
                    rusWriter.write('Imp:{}=>{}\n'.format(it[0],it[1]))

    def ICE_DataReuseRemakeData(self, newTitle, CanVarNum, olddata):
        varDict = {}
        newData = []
        for i in range(CanVarNum):
            varDict[newTitle[i]] = olddata[i]
            newData.append(olddata[i])

        varDictKey = list(varDict.keys())
        varDictKey.sort(key=len, reverse=True)

        for i in range(CanVarNum, len(newTitle)):
            titleStr = newTitle[i]
            for k in varDictKey:
                titleStr = titleStr.replace(k, '{}'.format(varDict[k]))
            rst = eval(titleStr)
            newData.append(rst)
        return tuple(newData)



    def ICE_DataReuseICE(self, dataSuffix='.data', implSuffix='.implications'):
        # print('[Debug] dataFile:', self.fileName + dataSuffix)
        # import pdb; pdb.set_trace()
        with open(self.fileName) as fopen:
            BPL_Lines = fopen.readlines()
        
        CanStr = None
        for line in BPL_Lines:
            if line.strip().startswith('invariant'):
                CanLPos = line.find('(')
                CanRPos = line.rfind(')')
                CanStr = line[CanLPos+1: CanRPos]
                break
        if CanStr == None:
            raise RuntimeError('Invariant candidate not found.')
        CanStr = CanStr.replace('mod','%').replace('div','//').replace(' ','')
        CanList = CanStr.split(',')
        CanVarNum = 0
        for it in CanList:
            hitFlag = False
            for failedCh in ['+','-','*','//','%']:
                if failedCh in it:
                    hitFlag = True
                    break
            if hitFlag:
                break
            CanVarNum += 1

        # print('[Debug] CanList is:', CanList)

        if not os.path.exists(self.fileName + dataSuffix):
            return [], []
        with open(self.fileName + dataSuffix) as dataReader:
            dataLines = dataReader.readlines()
        dataList = []
        for line in dataLines:
            line = line.strip()
            if line == '':
                break
            dataStr = line.split(',')
            dataList.append((self.ICE_DataReuseRemakeData(CanList, CanVarNum, tuple(map(int, dataStr[1:-1]))), dataStr[-1]))
        # import pdb; pdb.set_trace()
        NegReuseList = list(map(lambda x: x[0], filter(lambda x: x[1] == 'false', dataList)))
        # import pdb; pdb.set_trace()
        if not os.path.exists(self.fileName + implSuffix):
            return NegReuseList, []
        with open(self.fileName + implSuffix) as implReader:
            implLines = implReader.readlines()
        ImpReuseList = []
        for line in implLines:
            line = line.strip()
            if line == '':
                break
            it0, it1 = line.split(' ')
            it0, it1 = int(it0), int(it1)
            ImpReuseList.append((dataList[it0][0], dataList[it1][0]))
        # import pdb; pdb.set_trace()
        return NegReuseList, ImpReuseList

    def ICE_DataReuseTest(self, itVar='i', onlyFirst=True):
        with open(self.fileName) as fopen:
            BPL_Lines = fopen.readlines()
        
        CanStr = None
        for line in BPL_Lines:
            if line.strip().startswith('invariant'):
                CanLPos = line.find('(')
                CanRPos = line.rfind(')')
                CanStr = line[CanLPos+1: CanRPos]
                break
        if CanStr == None:
            raise RuntimeError('Invariant candidate not found.')
        CanStr = CanStr.replace('mod','%').replace('div','//').replace(' ','')
        CanList = CanStr.split(',')
        # print('[Debug] CanList is:', CanList)
        
        PosReuseList = []
        NegReuseList = []

        BoundsList = self.Logger.Stat_Now_Bound
        BoundsExprList = []
        BoundsNameList = []
        dimVal = 0
        # print('[Debug] BoundsList:', BoundsList)
        for dim in BoundsList:
            exprList = []
            for b in dim:

                exprList.append(b)
            BoundsExprList.append(exprList)
            if len(BoundsList) == 1:
                BoundsNameList.append(itVar)
            else:
                BoundsNameList.append('{}{}'.format(itVar, dimVal))
            dimVal += 1

        for testTrace in self.Logger.TestDataInfo:
            BoundsValList = []
            stateId = 0
            for stateInfo in testTrace:
                # print('[Debug] stateInfo:', stateInfo)
                varsName = list(stateInfo)
                if 'TR' in varsName:
                    varsName.remove('TR')
                varsName.sort(key=len,reverse=True)
                if len(BoundsValList) == 0:
                    # BoundsValList = []
                    for dim in BoundsExprList:
                        maxBound = -1
                        for be in dim:
                            # print(be)
                            if not self.Logger.Use_Lexical:
                                be = be[1]
                            for varName in varsName:
                                be = be.replace(varName, str(stateInfo[varName]))
                            vbe = eval(be)
                            if vbe > maxBound:
                                maxBound = vbe
                        BoundsValList.append(maxBound)
                else:
                    for i in reversed(range(len(BoundsValList))):
                        if BoundsValList[i] == 1:
                            maxBound = -1
                            for be in dim:
                                for varName in varsName:
                                    be = be.replace(varName, str(stateInfo[varName]))
                                vbe = eval(be)
                                if vbe > maxBound:
                                    maxBound = vbe
                            BoundsValList[i] = maxBound
                        else: 
                            BoundsValList[i] -= 1
                            break
                stateInfoPos = dict(stateInfo)
                stateInfoNeg = dict(stateInfo)
                for i in range(len(BoundsNameList)):
                    varsName.append(BoundsNameList[i])
                    stateInfoPos[BoundsNameList[i]] = BoundsValList[i]
                    stateInfoNeg[BoundsNameList[i]] = len(testTrace) - stateId - 1

                varsName.sort(key=len,reverse=True)
                
                stateVal_P = []
                stateVal_N = []
                for ca in CanList:
                    if ca.startswith('TR'):
                        trVal = int(ca[2:])
                        if stateInfo['TR'] != None and 'L{}'.format(trVal) in stateInfo['TR']:
                            stateVal_P.append(1)
                            stateVal_N.append(1)
                        else:
                            stateVal_P.append(0)
                            stateVal_N.append(0)
                    else:
                        caP = str(ca)
                        caN = str(ca)
                        for varName in varsName:
                            caP = caP.replace(varName, str(stateInfoPos[varName]))
                            caN = caN.replace(varName, str(stateInfoNeg[varName]))
                        vcaP = eval(caP)
                        vcaN = eval(caN)
                        stateVal_P.append(vcaP)
                        stateVal_N.append(vcaN)
                PosReuseList.append(tuple(stateVal_P))
                NegReuseList.append(tuple(stateVal_N))
                # print('[Debug] stateVal:', stateVal)
                # import pdb; pdb.set_trace()
                if onlyFirst:
                    break
                stateId += 1
        return PosReuseList, NegReuseList

    def ExecuteICE(self, timeout = None, timeoutMonitor = None):
        
        self.ICE_DataReuse()

        # import pdb; pdb.set_trace()
        curDir = os.path.abspath('.')
        os.chdir(self.boogieDir)
        self.Logger.Log('[Debug] Boogie Dir: {}'.format(self.boogieDir))
        command = ['mono', 'Boogie.exe'] + self.boogieArgs + [self.fileName]
        if timeout != None:
            command = [timeoutMonitor, '--foreground', '--kill-after', '1', str(int(timeout) + 1)] + command
            self.Logger.StartTimer('TOM@ICE')
        self.Logger.Log('[Debug] Boogie Cmd: {}'.format(reduce(lambda x,y: '{} {}'.format(x,y), command)))
        process = subprocess.Popen(command,
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE)
        os.chdir(curDir)

        # stdout, stderr = process.communicate()

        # # print(stdout.decode())
        # stdoutLines = stdout.decode().split('\n')
        stdoutLines = []
        nextIsInv = False
        invIt = 0
        while process.poll() == None:
            # print(process.returncode)
            if timeout != None and self.Logger.CalcTimePass('TOM@ICE') > timeout:
                process.kill()
                print('[Info] Process killed.')
                self.Logger.Log('[Info] Benchmark timeout!')
                return {'Result': 'Timeout'}
            line = process.stdout.readline().decode().strip()
            if line.startswith('\n') or line == '':
                continue
            stdoutLines.append(line)
            # print('[Debug:ICE] ', line)
            # if line.startswith('[Debug0]'):
            #     print(line)
            if line.startswith('[Debug]') or line.startswith('[Warning]') or line.startswith('[Info]') or line.startswith('[Error]'):
                self.Logger.Log(line)
            if line.startswith('Prover time = '):
                proverTime = float(line[len('Prover time = '):].strip())
                self.Logger.Log('[Info] => Prover Time: {}'.format(proverTime))
                if self.Logger.Stat:
                    self.Logger.Stat_ICEProverTimeTotal += proverTime
                    self.Logger.Stat_ICEProverTimeList.append(proverTime)

            if line.startswith('C5 Learner time = '):
                learnerTime = float(line[len('C5 Learner time = '):].strip())
                self.Logger.Log('[Info] => Learner Time: {}'.format(learnerTime))
                if self.Logger.Stat:
                    self.Logger.Stat_ICELearnerTimeTotal += learnerTime
                    self.Logger.Stat_ICELearnerTimeList.append(learnerTime)

            if nextIsInv:
                self.Logger.Log('[Info] Guess Inv #{}: {}'.format(invIt,line))
                if self.Logger.Stat and self.Logger.Stat_LogAllInv:
                    self.Logger.Stat_InvList.append(IceCaller.prettyInv(self.Logger, line))
                invIt += 1
                nextIsInv = False
            if line.startswith('{'):
                nextIsInv = True
        # import pdb; pdb.set_trace()
        if self.Logger.Stat:
            self.Logger.Stat_InvRefineNumList.append(invIt - 1)
        if len(stdoutLines) == 0:
            if timeout != None:
                self.Logger.Log('[Info] Benchmark timeout!')
                return {'Result': 'Timeout'}
            else:
                raise RuntimeError('No stdoutput!')  
        resultLine = stdoutLines[-1]
        invLine = stdoutLines[-4]
        self.Logger.Log(resultLine)
        reMatcher = r'Boogie program verifier finished with (\d+) verified, (\d+) error(s)?'
        reResult = re.search(reMatcher, resultLine)
        if reResult == None:
            reMatcher = r'Boogie program verifier exited with error detected at (.*):(.*)'
            reResult = re.search(reMatcher, resultLine)
            
            if reResult == None:
                if timeout != None and self.Logger.CalcTimePass('TOM@ICE') > timeout - 2:
                    # import pdb; pdb.set_trace()
                    self.Logger.Log('[Info] Benchmark timeout!')
                    return {'Result': 'Timeout'}
                self.Logger.Log('ICE Error Info:', level=0)
                self.Logger.Log('{}'.format(reduce(lambda x, y: '{}\n{}'.format(x, y), stdoutLines)), level=0)
                print('{}'.format(reduce(lambda x,y :'{}\n{}'.format(x, y), stdoutLines)))
                raise RuntimeError('ICE Runtime Error！')
            return {'Result': 'Failed-Simp', 'Error': list(reResult.group(2).split(','))}

        verifiedNum = int(reResult.group(1))
        errorNum = int(reResult.group(2))
        if errorNum == 0:
            return {'Result': 'Verified', 'Invariant': invLine}
        else: 
            return {'Result': 'Failed'}
    
    @staticmethod
    def TranslateExpr(varExpr, logger):
        return IceCaller.GenerateExpr([varExpr], [1], logger)
    
    @staticmethod
    def GenerateExpr(varList, coefficientList, logger):
        if len(varList) != len(coefficientList):
            logger.Log('varList: {};\n argList: {};'.format(varList, coefficientList))
            raise RuntimeError('var list length is different from arg.')
        varCoefficient = {}
        for i in range(len(varList)):
            var = varList[i]
            arg = coefficientList[i]
            if not (var.startswith('ATTR$') or var.startswith('ATTM$')):
                if var not in varCoefficient.keys():
                    varCoefficient[var] = arg
                else:
                    varCoefficient[var] += arg
                continue
            expr = var[5:]
            splitList = expr.split('$')

            coefficient = None
            flag = 1
            for it in splitList:
                if it == 'ADD':
                    if coefficient != None:
                        if '1' not in varCoefficient.keys():
                            varCoefficient['1'] = coefficient * flag * arg
                        else:
                            varCoefficient['1'] += coefficient * flag * arg
                    coefficient = None
                    flag = 1
                    continue
                elif it == 'SUB':
                    if coefficient != None:
                        if '1' not in varCoefficient.keys():
                            varCoefficient['1'] = coefficient * flag * arg
                        else:
                            varCoefficient['1'] += coefficient * flag * arg
                    coefficient = None
                    flag = -1
                    continue
                elif it == 'MUL':
                    continue
                elif it == 'DIV':
                    raise RuntimeError('DIV not support.')
                else:
                    try:
                        intvalue = int(it)
                        coefficient = intvalue
                    except ValueError:
                        varName = it
                        if coefficient == None:
                            coefficient = 1
                        if varName not in varCoefficient.keys():
                            varCoefficient[varName] = coefficient * arg * flag
                        else:
                            varCoefficient[varName] += coefficient * arg * flag
                        coefficient = None
                        flag = 1
            if coefficient != None:
                if '1' not in varCoefficient.keys():
                    varCoefficient['1'] = coefficient * flag * arg
                else:
                    varCoefficient['1'] += coefficient * flag * arg

        isFirst = True          
        strRet = ''
        for (k,v) in varCoefficient.items():
            if '_MOD_' in k:
                modSP = k.split('_MOD_')
                k = '{} % {}'.format(modSP[0],modSP[1])
            if '_DIV_' in k:
                divSP = k.split('_DIV_')
                k = '{} % {}'.format(divSP[0],divSP[1])
            if v == 0:
                continue
            elif v < 0 or isFirst:
                if k == '1':
                    strRet += '{}'.format(v)
                elif v == -1:
                    strRet += '-{}'.format(k)
                elif v == 1:
                    strRet += '{}'.format(k)
                else:
                    strRet += '{}*{}'.format(v,k)
            else:
                if k == '1':
                    strRet += '+{}'.format(v)
                elif v == 1:
                    strRet += '+{}'.format(k)
                else:
                    strRet += '+{}*{}'.format(v,k)
            isFirst = False
        if strRet == '':
            strRet = '0'
        return strRet

    @staticmethod
    def IsNumber(s):
        if not type(s) == str:
            raise RuntimeError('Only to judge a string object!')
        s = s.replace(' ','')
        for i in range(len(s)):
            if ord(s[i]) - ord('0') in range(0, 9) or ord(s[i]) == ord('-') and i == 0:
                continue
            else:
                return False
        return True
    
    @staticmethod
    def Expr2ATTRName(expr):
        rename = expr.replace(' ','')
        rename = rename.replace('+','$ADD$')
        rename = rename.replace('-','$SUB$')
        rename = rename.replace('*','$MUL$')
        # rename = rename.replace('div','$DIV$')
        rename = 'ATTR$' + rename
        return rename

    def GenerateITCode(self, lexRank, itVars, now, indent=0, indentIC=2):
        if now == 0:
            return indent * ' ' + '{} := {} - 1;\n'.format(itVars[now], itVars[now])
        rankingBound = ''
        firstRanking = True
        # import pdb; pdb.set_trace()
        for it in lexRank[now]:
            if firstRanking:
                rankingBound += '{} >= {}'.format(itVars[now], it)
                firstRanking = False
            else:
                rankingBound += ' && {} >= {}'.format(itVars[now], it)

        Content = indent * ' ' + 'if(' + itVars[now] + ' > 0){\n' + \
                (indent + indentIC) * ' ' + '{} := {} - 1;\n'.format(itVars[now], itVars[now]) + \
                indent * ' ' + '}\n' + \
                indent * ' ' + 'else{\n' + \
                self.GenerateITCode(lexRank, itVars, now-1, indent+indentIC, indentIC) + \
                (indent + indentIC) * ' ' + 'havoc {};\n'.format(itVars[now]) + \
                (indent + indentIC) * ' ' + 'assume({});\n'.format(rankingBound) + \
                indent * ' ' + '}\n'
        return Content


    # lexRank is a 2-dim list
    def GenerateConcreteBplFileLexicalTemplate(self, lexRank, itVar='i'):
        self.Logger.Stat_Now_Bound = lexRank
        itVars = []
        rankValue = len(lexRank)
        if rankValue == 1:
            itVars.append(itVar)
        else:
            for i in range(rankValue):
                itVars.append(itVar+'{}'.format(i))
        allLexical = []
        for i in range(len(lexRank)):
            # duplicate remove
            lexRank[i] = list(set(lexRank[i]))
            lexRank[i].sort(reverse=True)
            allLexical += lexRank[i]
        allLexical = list(set(allLexical))
        allLexical.sort(reverse=True)

        fileOpen = open(self.tempfile)
        outFileOpen = open(self.fileName, 'w')
        tempContent = fileOpen.readlines()
        fileOpen.close()

        for line in tempContent:
            for patternId in range(len(self.LexicalReList)):
                pattern = self.LexicalReList[patternId]
                result = re.search(pattern, line)
                if not result is None:
                    patternBefore = result.group(1)
                    patternAfter = result.group(2)
                    if patternId == 0: # FD
                        FD_Text = ''
                        for it in itVars:
                            FD_Text += ',{}:int'.format(it)
                        for it in allLexical:
                            if IceCaller.IsNumber(it):
                                continue
                            FD_Text += ',{}:int'.format(IceCaller.Expr2ATTRName(it))
                        # i in ATTM to i_x
                        ATTMList = re.findall(',(.*?):int', patternAfter)
                        ATTMListNew = []
                        for attm in ATTMList:
                            attm = attm.replace(' ','').replace('\t','')
                            items = attm.split('$')
                            if itVar in items:
                                for iv in itVars:
                                    nitems = [iv if x == itVar else x for x in items]
                                    ATTMListNew.append(reduce(lambda x,y: '{}${}'.format(x,y), nitems))
                            else:
                                ATTMListNew.append(reduce(lambda x,y: '{}${}'.format(x,y), items))
                        NewATTMStr = ''
                        for its in ATTMListNew:
                            NewATTMStr += ', ' + its + ':int'
                        NewATTMStr += '): bool;'
                       
                        newcontent = patternBefore + FD_Text + NewATTMStr
                    elif patternId == 1: #VD
                        VD_Text = ''
                        for it in itVars:
                            VD_Text += ',{}'.format(it)
                        newcontent = patternBefore + VD_Text + patternAfter
                    elif patternId == 2: #BE
                        BE_Ctx = ''
                        BE_First = True
                        for i in range(len(itVars)):
                            varName = itVars[i]
                            for it in lexRank[i]:
                                if BE_First:
                                    BE_First = False
                                    BE_Ctx += '{} >= {}'.format(varName, it)
                                else:
                                     BE_Ctx += ' && {} >= {}'.format(varName, it)
                        BE_Text = 'assume({});'.format(BE_Ctx)
                        newcontent = patternBefore + BE_Text + patternAfter
                    elif patternId == 3: #IC
                        IC_Text = ''
                        for it in itVars:
                            IC_Text += ',{}'.format(it)
                        for it in allLexical:
                            if IceCaller.IsNumber(it):
                                continue
                            IC_Text += ',{}'.format(it)

                        # i in ATTM to i_x
                        # ATTMList = re.findall(',(.*?)', patternAfter)
                        ATTMList = patternAfter.replace(');','').split(',')
                        ATTMList.remove('')
                        ATTMListNew = []
                        # print(ATTMList)
                        for attm in ATTMList:
                            attm = attm.replace('+',' + ').replace('-',' - ').replace('*',' * ')
                            items = attm.split(' ')
                            # print(items)
                            if itVar in items:
                                for iv in itVars:
                                    nitems = [iv if x == itVar else x for x in items]
                                    ATTMListNew.append(reduce(lambda x,y: '{} {}'.format(x,y), nitems))
                            else:
                                ATTMListNew.append(reduce(lambda x,y: '{} {}'.format(x,y), items))
                        NewATTMStr = ''
                        for its in ATTMListNew:
                            NewATTMStr += ', ' + its
                        NewATTMStr += ');'
                        
                        newcontent = patternBefore + IC_Text + NewATTMStr
                    elif patternId == 4: #BT
                        BT_Text = 'assert({} > 0);'.format(itVars[0])
                        newcontent = patternBefore + BT_Text + patternAfter
                    elif patternId == 5: #IT
                        # import pdb; pdb.set_trace()
                        IT_Text = self.GenerateITCode(lexRank, itVars, len(itVars)-1, patternBefore.count(' '))
                        if patternBefore.strip() == '':
                            patternBefore = ''
                        else:
                            patternBefore += '\n'
                        if patternAfter.strip() == '':
                            patternAfter = ''
                        else:
                            patternAfter = '\n' + patternAfter
                        newcontent = patternBefore + IT_Text + patternAfter

                    outFileOpen.write(newcontent + '\n')
                    break
                else:
                    if patternId == len(self.LexicalReList) - 1:
                        outFileOpen.write(line)
        outFileOpen.close()

    def GenerateConcreteBplFile(self, boundMList = []):
        self.Logger.Stat_Now_Bound = [boundMList]
        # duplicate remove
        boundMList = list(set(boundMList))
        boundMList.sort(reverse=True)
        fileOpen = open(self.tempfile)

        outFileOpen = open(self.fileName, 'w')

        tempContent = fileOpen.readlines()
        fileOpen.close()
        for line in tempContent:
            for patternId in range(len(self.ReList)):
                pattern = self.ReList[patternId]
                result = re.search(pattern, line)
                if not result is None:
                    identifierI = result.group(2).replace(' ','')
                    subReplace = list(filter(lambda x: x[0]==identifierI, boundMList))
                    # if not (identifierI, '0') in subReplace:
                    #     subReplace.append((identifierI, '0'))
                    if patternId == 0:
                        self.Logger.Log('match M for:{}'.format(identifierI))
                        formula = ''
                        for subId in range(len(subReplace)):
                            formula += ('' if subId == 0 else ' && ') + identifierI + ' >= ' + subReplace[subId][1].replace(' ','')
                        outFileOpen.write(result.group(1) + formula + result.group(3) + '\n')
                    elif patternId == 1:
                        self.Logger.Log('match Decl for:{}'.format(identifierI))
                        args = ''
                        for subId in range(len(subReplace)):
                            if IceCaller.IsNumber(subReplace[subId][1]):
                            # if subReplace[subId][1] == '1':
                                continue
                            rename = subReplace[subId][1].replace(' ','')
                            rename = rename.replace('+','$ADD$')
                            rename = rename.replace('-','$SUB$')
                            rename = rename.replace('*','$MUL$')
                            # rename = rename.replace('div','$DIV$')
                            rename = 'ATTR$' + rename

                            args += ', ' + rename + ':int'
                        outFileOpen.write(result.group(1) + args + result.group(3) + '\n')
                    else:
                        self.Logger.Log('match Inv for:{}'.format(identifierI))
                        args = ''
                        for subId in range(len(subReplace)):
                            if IceCaller.IsNumber(subReplace[subId][1]):
                                continue
                            args += ', ' + subReplace[subId][1]
                        outFileOpen.write(result.group(1) + args + result.group(3) + '\n')
                    
                    break
                else:
                    if patternId == len(self.ReList) - 1:
                        outFileOpen.write(line)
        outFileOpen.close()

