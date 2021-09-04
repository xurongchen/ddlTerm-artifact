import os
import re
import subprocess
import shutil
from functools import reduce
import antlr4
from antlr4.Token import CommonToken
from antlr4.tree.Tree import TerminalNodeImpl
import sys
sys.path.append(os.path.abspath('code'))
from StateTrans import TraceStateTrans  #pylint: disable=import-error
from StateTrans.TraceStateTrans import * #pylint: disable=import-error

from BoogieAST.AST2SourceVisitor import AST2SourceVisitor #pylint: disable=import-error
from BoogieAST.ASTOperation import ASTOperation #pylint: disable=import-error
from BoogieAST.BoogieLexer import BoogieLexer #pylint: disable=import-error
from BoogieAST.BoogieParser import BoogieParser #pylint: disable=import-error

class BMCFinder:
    
    def __init__(self, logger, tmpDir, tempfile, vars, itvar):
        self.Logger = logger
        self.tmpDir = os.path.abspath(tmpDir)
        self.tempfile = os.path.abspath(tempfile)
        self.fileName = None
        self.projectDir = '/'.join(os.getcwd().split('/'))
        self.boogieDir = self.projectDir + '/ice/popl16_artifact/Boogie/Binaries'
        self.boogieArgs = ['/noinfer', '/contractInfer', '/liveVariableAnalysis:0', 
            '/printAssignment', '/trace', '/printModel:4', 
            # '/proverLog:tst.smt'
            '/errorLimit:10'
            ]

        self.Vars = vars
        self.itvar = itvar

        if self.Logger.SMTFile != None:
            self.boogieArgs.append('/proverLog:{}'.format(self.Logger.SMTFile))

        fileName = self.tempfile.split('/')[-1]
        if not os.path.exists(self.tmpDir):
            os.makedirs(self.tmpDir)
        outFile = os.path.join(self.tmpDir, fileName)
        self.fileName = outFile
        self.BMCfileName = os.path.join(self.tmpDir, 'BMC_' + fileName)

    def CleanTmpFiles(self):
        if os.path.exists(self.tmpDir) and os.path.isdir(self.tmpDir):
            shutil.rmtree(self.tmpDir)


    def AnalazyModel(self, model, bound, ret='default'):
        # print('[Debug] == model ==')
        # for line in model:
        #     print('[Debug]', line)
        modelDict = {}
        recordVars = set()
        var2modelName = {}
        for line in model:
            rexpr = r'(.*)? -> \(?(- )?(\d+)\)?'
            reM = re.search(rexpr, line)

            if reM == None:
                continue
            else:
                varName = reM.group(1)
                if varName.startswith(r'%lbl%'):
                    continue
                if '@' in varName:
                    realName = varName[:varName.find('@')]
                    recordVars.add(realName)
                else:
                    recordVars.add(varName)

                valueV = int(reM.group(3))
                if reM.group(2) != None:
                    valueV = -valueV
            modelDict[varName] = valueV
        
        for varName in recordVars:
            var2modelName[varName] = []
            if varName in modelDict.keys():
                var2modelName[varName].append(varName)
            varCnt = 0
            while True:
                cntName = '{}@{}'.format(varName, varCnt)
                if cntName in modelDict.keys():
                    var2modelName[varName].append(cntName)
                else:
                    if varCnt >= 5:
                        break
                varCnt += 1
        
        itJudger = self.itvar
        if itJudger not in recordVars:
            itJudger = self.itvar + '0'
            if itJudger not in recordVars:
                raise RuntimeError('Cannot find the itvar!')

        if ret == 'default':
            # record variable changes in the error path
            errorTrace = []
            # errorInput = None
            itChange = {}
            itNow = {}
            # Warning check of number of SSA vars
            for v in self.Vars + [itJudger]:
                if v not in var2modelName.keys():
                    var2modelName[v] = [v]
                    modelDict[v] = 0 # default = 0
                if len(var2modelName[v]) < bound:
                    self.Logger.Log('[Warning] SSA number of var is small than bound. Suppose not changing happend in loop. (VAR: {}, SSA: {}, UNROLL: {})'.format(v, len(var2modelName[v]), bound))

                elif bound == 0 and (len(var2modelName[v]) - 1) == 0 or (len(var2modelName[v]) - 1) % bound != 0:
                    self.Logger.Log('[Warning] Incorrect number when transform SSA model to unroll bound. (VAR: {}, SSA: {}, UNROLL: {})'.format(v, len(var2modelName[v]), bound))

            for v in self.Vars + [itJudger]:
                if len(var2modelName[v]) < bound:
                    itNow[v] = len(var2modelName[v]) - 1 
                    itChange[v] = 0
                    continue
                itNow[v] = 0
                if bound != 0:
                    itChange[v] = (len(var2modelName[v]) - 1) // bound
                else:
                    itChange[v] = 0
            # import pdb; pdb.set_trace()

            while modelDict[var2modelName[itJudger][itNow[itJudger]]] >= 0:
                valueState = []
                for v in self.Vars:
                    valueState.append(modelDict[var2modelName[v][itNow[v]]])
                    itNow[v] += itChange[v]
                errorTrace.append(tuple(valueState))
                if modelDict[var2modelName[itJudger][itNow[itJudger]]] == 0:
                    break
                itNow[itJudger] += itChange[itJudger]
            # print error trace
            self.Logger.Log('[Info] Error trace by BMC is {}'.format(self.Vars), level=5)
            for it in errorTrace:
                self.Logger.Log('[Info] => {}'.format(it), level=5)

            return errorTrace, errorTrace[0]
        elif ret == 'trace':
            TRVars = list(filter(lambda x: x.startswith('TR'), recordVars))
            itChange = {}
            itNow = {}
            errorInput = None
            # Warning check of number of SSA vars
            for v in TRVars:
                if len(var2modelName[v]) != bound:
                    self.Logger.Log('[Warning] Incorrect number when transform SSA model to unroll bound. (VAR: {}, SSA: {}, UNROLL: {})'.format(v, len(var2modelName[v]), bound))
            for v in self.Vars + [itJudger]:
                if v not in var2modelName.keys():
                    var2modelName[v] = [v]
                    modelDict[v] = 0 # default = 0
                if len(var2modelName[v]) < bound:
                    self.Logger.Log('[Warning] SSA number of var is small than bound. Suppose not changing happend in loop. (VAR: {}, SSA: {}, UNROLL: {})'.format(v, len(var2modelName[v]), bound))

                elif bound == 0 and (len(var2modelName[v]) - 1) == 0 or (len(var2modelName[v]) - 1) % bound != 0:
                    self.Logger.Log('[Warning] Incorrect number when transform SSA model to unroll bound. (VAR: {}, SSA: {}, UNROLL: {})'.format(v, len(var2modelName[v]), bound))
            for v in TRVars:
                itNow[v] = 0
                itChange[v] = 1
                
            for v in self.Vars + [itJudger]:
                if len(var2modelName[v]) < bound:
                    itNow[v] = len(var2modelName[v]) - 1 
                    itChange[v] = 0
                    continue
                itNow[v] = 0
                if bound != 0:
                    itChange[v] = (len(var2modelName[v]) - 1) // bound
                else:
                    itChange[v] = 0

            Tr = TraceStates(self.Vars) # pylint: disable=undefined-variable
            firstState = True

            while modelDict[var2modelName[itJudger][itNow[itJudger]]] >= 0:
                varState = []
                for v in self.Vars:
                    varState.append(modelDict[var2modelName[v][itNow[v]]])
                    itNow[v] += itChange[v]
                if firstState:
                    Tr.appendInitState(tuple(varState))
                    errorInput = varState
                    firstState = False
                else:
                    trInfo = []
                    for t in TRVars:
                        if modelDict[var2modelName[t][itNow[t]]] == 1:
                            trV = int(t[2:])
                            trInfo.append('L{}'.format(trV))
                        itNow[t] += itChange[t]
                    Tr.appendNextState(tuple(varState), tuple(trInfo))
                if modelDict[var2modelName[itJudger][itNow[itJudger]]] == 0:
                    break
                itNow[itJudger] += itChange[itJudger]

            return Tr, errorInput
        else:
            raise RuntimeError('Not supported ret type of BMCFinder')


    def ExecuteBMC(self, Bound, ret='default', timeout = None, timeoutMonitor = None):
        self.GenerateConcreteBplFile(Bound)
        curDir = os.path.abspath('.')
        os.chdir(self.boogieDir)
        self.Logger.Log('[Debug] Boogie Dir: {}'.format(self.boogieDir))
        # print('[Debug]', self.BMCfileName)
        self.Logger.Log('[Debug] Boogie Cmd: {}'.format(reduce(lambda x,y: '{} {}'.format(x,y), ['mono', 'Boogie.exe'] + self.boogieArgs + [self.BMCfileName])))
        Timer = []
        if timeout != None:
            Timer = [timeoutMonitor, '--foreground', '--kill-after', '1', str(int(timeout) + 1)]
        process = subprocess.Popen(Timer + ['mono', 'Boogie.exe'] + self.boogieArgs + [self.BMCfileName],
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE)
        os.chdir(curDir)

        stdout, stderr = process.communicate()

        # print(stdout.decode())
        stdoutLines = stdout.decode().split('\n')


        if self.Logger.Stat:
            self.Logger.Stat_InvRefineNumList.append(0)
        if len(stdoutLines) < 2:
            self.Logger.Log('[Info] Benchmark timeout!')
            return {'Result': 'BMC-Timeout'}
        self.Logger.Log(stdoutLines[-2])
        reMatcher = r'Boogie program verifier finished with (\d+) verified, (\d+) error(s)?'
        reResult = re.search(reMatcher, stdoutLines[-2])
        if reResult == None:
            self.Logger.Log('[Info] Benchmark timeout!')
            return {'Result': 'BMC-Timeout'}

        verifiedNum = int(reResult.group(1))
        errorNum = int(reResult.group(2))
        if errorNum == 0:
            self.Logger.Log('[Info] BMC verified the bound with unroll {}.'.format(Bound))
            return {'Result': 'NO_BMC_CEX', 'Unroll': Bound}
        else: 
            ModelList = []
            currentModel = []
            isModelCtx = False
            for line in stdoutLines:
                if line.startswith('*** MODEL'):
                    currentModel = []
                    isModelCtx = True
                elif line.startswith('*** END_MODEL'):
                    ModelList.append(currentModel)
                    isModelCtx = False
                elif isModelCtx:
                    currentModel.append(line)
            
            ErrorTRInfoList = []
            ErrorInputList = []
            for model in ModelList:
                trInfo, inputInfo = self.AnalazyModel(model, Bound, ret)
                ErrorInputList.append(inputInfo)
                if ret == 'default':
                    dictLenInfoList = []
                    for i in range(len(trInfo)):
                        varDict = {}
                        vid = 0
                        for v in self.Vars:
                            varDict[v] = trInfo[i][vid]
                            vid += 1
                        dictLenInfoList.append((varDict, len(trInfo) - i))
                    ErrorTRInfoList.append(dictLenInfoList)
                elif ret == 'trace':
                    ErrorTRInfoList.append(trInfo)
                else:
                    raise RuntimeError('Unsupported return type for BMC.')
            self.Logger.Log('[info] BMC failed with cex Num {} (Unroll = {})'.format(len(ErrorTRInfoList), Bound + 1))
            return {'Result': 'Failed-BMC', 'ErrorTrace': ErrorTRInfoList, 'ErrorInput': ErrorInputList, 'ReturnType': ret}
            
            
    

    def GenerateConcreteBplFile(self, ConstBound):
        # with open(self.fileName) as fopen:
        #     fileLines = fopen.readlines()
        # moreInfoVars = []
        # for lineId in range(len(fileLines)):
        #     line = fileLines[lineId]
        #     if 'invariant' in line:
        #         variables = line.replace(')', ',').replace('(', ',').split(',')
        #         for v in variables:
        #             v = v.strip()
        #             if v.startswith('TR'):
        #                 moreInfoVars.append(v)
        #             elif v.startswith(self.itvar) and not v.startswith('invariant') and not v in [self.itvar, self.itvar + '0']:
        #                 moreInfoVars.append(v)
        #     elif 'assert' in line:
        #         rbrace = line.rfind(')')
        #         # print(moreInfoVars)
        #         line = line[:rbrace] + reduce(lambda x,y: '{} && {} >= 0'.format(x,y), moreInfoVars, '') + line[rbrace:]
        #         fileLines[lineId] = line
        #         break
        # newCtx = reduce(lambda x,y: '{}{}'.format(x,y), fileLines, '')
        # input_stream = antlr4.InputStream(newCtx)
        input_stream = antlr4.FileStream(self.fileName)
        lexer = BoogieLexer(input_stream)
        stream = antlr4.CommonTokenStream(lexer)
        parser = BoogieParser(stream)
        AST = parser.boogie_program()
        
        whileLoopPa = ASTOperation.FindNode(AST, Filter= lambda x: type(x) == BoogieParser.Structured_cmdContext and x.getChildCount() == 1 and type(x.getChild(0)) == BoogieParser.While_cmdContext)
        if len(whileLoopPa) != 1:
            raise RuntimeError('Find no or more than one while loop!')
        # def contain(node, v):
        #     if type(node) == TerminalNodeImpl:
        #         return v == node.getSymbol().text
        #     for i in range(node.getChildCount()):
        #         if contain(node.getChild(i), v):
        #             # import pdb; pdb.set_trace()
        #             return True
        #     return False

        assertCtx = ASTOperation.FindNode(AST, lambda x: type(x) == BoogieParser.Assert_cmdContext)
        if len(assertCtx) != 1:
            raise RuntimeError('The number of assert is not 1.')
        assertCtx = assertCtx[0]
        # import pdb; pdb.set_trace()
        def toDel(node):
            if type(node) == BoogieParser.Func_declContext:
                return True
            # if type(node) == BoogieParser.Assert_cmdContext:
            #     return True
            return False
            # if not type(node) == BoogieParser.Label_or_cmdContext:
            #     return False
            # # import pdb; pdb.set_trace()
            # return contain(node, self.itvar)
        ASTOperation.RemoveNode(AST, toDel)
        
        # while => assume
        whileLoop = whileLoopPa[0].getChild(0)
        whileLoopGuardExpr = whileLoop.guard().children[1]
        assumeCmd = ASTOperation.Assume_Cmd(parser, whileLoopGuardExpr)
        # break => assume false
        whileStmts = whileLoop.stmt_list()
        breaks = ASTOperation.FindNode(whileStmts, lambda x: type(x) == BoogieParser.Break_cmdContext)
        breaksInStmts = list(map(lambda x: x.parentCtx.parentCtx, breaks))
        for stId in range(len(breaksInStmts)):
            for childId in range(len(breaksInStmts[stId].children)):
                if breaksInStmts[stId].children[childId] == breaks[stId].parentCtx:
                    assumeFalseCmd = ASTOperation.Assume_Cmd(parser, ASTOperation.Terminal_False())
                    breaksInStmts[stId].children[childId] = assumeFalseCmd
                    # print('[Debug] MATCH!')
                    # print(breaksInStmts[stId].getText())

                # print(breaksInStmts[stId].getText())

        # print(whileStmts.getText())
        # import pdb; pdb.set_trace()
        # repeat C times
        statementList = ([assumeCmd] + \
            whileLoop.stmt_list().children) * ConstBound + \
            [assumeCmd, assertCtx]
        # import pdb; pdb.set_trace()
        whilePos = ASTOperation.ParentChildID(whileLoop, whileLoopPa[0])
        ASTOperation.RemoveChild(whileLoopPa[0], whilePos)

        ASTOperation.AddChild(whileLoopPa[0], statementList, whilePos)

        visitor = AST2SourceVisitor()
        visitor.visit(AST)
        # print(self.BMCfileName)
        self.Logger.Log('[info] Write to BMC file {}'.format(self.BMCfileName))
        with open(self.BMCfileName, 'w') as BMCWriter:
             BMCWriter.write(visitor.Output)

        # import pdb; pdb.set_trace()