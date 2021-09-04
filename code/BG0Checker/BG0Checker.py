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

from BoogieAST.AST2SourceVisitor import AST2SourceVisitor #pylint: disable=import-error
from BoogieAST.ASTOperation import ASTOperation #pylint: disable=import-error
from BoogieAST.BoogieLexer import BoogieLexer #pylint: disable=import-error
from BoogieAST.BoogieParser import BoogieParser #pylint: disable=import-error

class BG0Checker:
    
    def __init__(self, logger, tmpDir, tempfile, vars, itvar):
        self.Logger = logger
        self.tmpDir = os.path.abspath(tmpDir)
        self.tempfile = os.path.abspath(tempfile)
        self.fileName = None
        self.projectDir = '/'.join(os.getcwd().split('/'))
        self.boogieDir = self.projectDir + '/ice/popl16_artifact/Boogie/Binaries'
        self.boogieArgs = ['/noinfer', '/contractInfer', 
            '/printAssignment', '/trace', '/printModel:4']
        self.Vars = vars
        self.itvar = itvar

        if self.Logger.SMTFile != None:
            self.boogieArgs.append('/proverLog:{}'.format(self.Logger.SMTFile))

        fileName = self.tempfile.split('/')[-1]
        if not os.path.exists(self.tmpDir):
            os.makedirs(self.tmpDir)
        outFile = os.path.join(self.tmpDir, fileName)
        self.fileName = outFile
        self.BG0CfileName = os.path.join(self.tmpDir, 'BG0C_' + fileName)

    def CleanTmpFiles(self):
        if os.path.exists(self.tmpDir) and os.path.isdir(self.tmpDir):
            shutil.rmtree(self.tmpDir)

    def ExecuteBG0C(self, BoundList = None):
        if BoundList != None:
            for b in BoundList:
                bv = b[1]
                try:
                    if int(bv) >= 1:
                        return True, None
                except ValueError:
                    continue
        self.GenerateConcreteBplFile()
        curDir = os.path.abspath('.')
        os.chdir(self.boogieDir)
        self.Logger.Log('[Debug] Boogie Dir: {}'.format(self.boogieDir))
        self.Logger.Log('[Debug] Boogie Cmd: {}'.format(reduce(lambda x,y: '{} {}'.format(x,y), ['mono', 'Boogie.exe'] + self.boogieArgs + [self.fileName])))
        process = subprocess.Popen(['mono', 'Boogie.exe'] + self.boogieArgs + [self.BG0CfileName],
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE)
        os.chdir(curDir)

        stdout, stderr = process.communicate()

        # print(stdout.decode())
        stdoutLines = stdout.decode().split('\n')


        if self.Logger.Stat:
            self.Logger.Stat_InvRefineNumList.append(0)
        self.Logger.Log(stdoutLines[-2])
        reMatcher = r'Boogie program verifier finished with (\d+) verified, (\d+) error(s)?'
        reResult = re.search(reMatcher, stdoutLines[-2])

        verifiedNum = int(reResult.group(1))
        errorNum = int(reResult.group(2))
        if errorNum == 0:
            self.Logger.Log('[info] Advanced Bound > 0 checked.')
            return True, None
        else: 
            valueDict = {}
            for v in self.Vars:
                rexpr = v + r'@0 -> \(?(- )?(\d+)\)?'
                # rexpr = r'oldx -> \(?(- )?(\d+)\)?'
                reM = re.search(rexpr, stdout.decode())
                # # Debug print start
                # if reM == None:
                #     print(self.Vars)
                #     print(stdout.decode())
                # # Debug print end
                if reM == None:
                    valueV = 0 # no influence var => default 0
                else:
                    valueV = int(reM.group(2))
                    if reM.group(1) != None:
                        valueV = -valueV
                valueDict[v] = valueV
            # print(stdout.decode())
            self.Logger.Log('[info] Advanced Bound > 0 checking failed with cex {}'.format(valueDict))
            return False, {'Result': 'Failed-BG0C', 'Counterexample': [(valueDict, 1)]}
    

    def GenerateConcreteBplFile(self):
        input_stream = antlr4.FileStream(self.fileName)
        lexer = BoogieLexer(input_stream)
        stream = antlr4.CommonTokenStream(lexer)
        parser = BoogieParser(stream)
        AST = parser.boogie_program()
        
        whileLoopPa = ASTOperation.FindNode(AST, Filter= lambda x: type(x) == BoogieParser.Structured_cmdContext and x.getChildCount() == 1 and type(x.getChild(0)) == BoogieParser.While_cmdContext)
        if len(whileLoopPa) != 1:
            raise RuntimeError('Find no or more than one while loop!')
        
        
        def toDel(node):
            if type(node) == BoogieParser.Func_declContext:
                return True
            return False
        
        ASTOperation.RemoveNode(AST, toDel)
        # while => assume
        whileLoop = whileLoopPa[0].getChild(0)
        whileLoopGuardExpr = whileLoop.guard().children[1]
        assumeCmd = ASTOperation.Assume_Cmd(parser, whileLoopGuardExpr)
        # repeat C times
        statementList = [assumeCmd, whileLoop.stmt_list().children[0]]

        whilePos = ASTOperation.ParentChildID(whileLoop, whileLoopPa[0])
        ASTOperation.RemoveChild(whileLoopPa[0], whilePos)

        ASTOperation.AddChild(whileLoopPa[0], statementList, whilePos)

        visitor = AST2SourceVisitor()
        visitor.visit(AST)
        # print(self.BG0CfileName)
        self.Logger.Log('[info] Write to BG0C file {}'.format(self.BG0CfileName))
        with open(self.BG0CfileName, 'w') as BG0CWriter:
             BG0CWriter.write(visitor.Output)

