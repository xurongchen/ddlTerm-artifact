from time import time
from functools import reduce
import xlsxwriter

class Logger:

    def __init__(self, printLevel = 10):
        self.PrintLevel = printLevel

        self.SMTFile = None
        self.Use_Lexical = False
        # Stat Info
        self.Stat = False
        self.Stat_Result = 'Unknown'
        self.Stat_Name = None
        self.Stat_BoundRefineNum = 0
        # self.Stat_InvRefineTotalNum = 0
        # self.Stat_InvRefineMaxNum = 0
        self.Stat_InvRefineNumList = []
        self.Stat_InvTimeList = []
        self.Stat_CBCTimeList = []
        self.Stat_BG0CTimeList = []
        self.Stat_TotalTime = 0
        # self.Stat_BoundTotalTime = 0
        # self.Stat_BoundMaxTime = 0
        self.Stat_TestTimeList = [] # How much time used by test for each bound
        self.Stat_TestStateNumList = [] # How many program states generated by test
        self.Stat_BoundTimeList = [] # The generation time of each bound
        self.Stat_BoundStateNumList = [] # How many program states is used for bound learning
        self.Stat_CFileSize = None
        self.Stat_BplFileSize = None

        self.Stat_BMCTimeList = []

        self.Stat_ICEProverTimeTotal = 0
        self.Stat_ICEProverTimeList = []
        self.Stat_ICELearnerTimeTotal = 0
        self.Stat_ICELearnerTimeList = []

        self.Stat_FinalBound = None
        self.Stat_FinalInv = None

        self.Stat_LogAllBound = False
        self.Stat_LogAllInv = False

        self.Stat_BoundList = []
        self.Stat_InvList = []

        self.Stat_Timer = {}
        
        # for ICE speed up
        self.TestDataInfo = []
        # self.Stat_ICE_PosReuse = False
        # self.Stat_ICE_NegReuse = False
        # self.Stat_ICE_ImpReuse = False
        self.Stat_Now_Bound = None

    def Log(self, info, level = 1):
        if level <= self.PrintLevel:
            print(info)

    def LogStatistic(self, logAllBound = False, logAllInv = False):
        self.Stat = True
        # self.Stat_Name = taskName
        self.Stat_LogAllBound = logAllBound
        self.Stat_LogAllInv = logAllInv

    def FormatBound(self):
        if self.Use_Lexical:
            self.Stat_FinalBound = '{}'.format(self.Stat_FinalBound)
            for i in range(len(self.Stat_BoundList)):
                b = self.Stat_BoundList[i]
                self.Stat_BoundList[i] = '{}'.format(b)
        else:
            formatF0 = lambda x: '{} >= {}'.format(x[0],x[1])
            formatF1 = lambda x, y: '{} && {}'.format(x, y)
            if not self.Stat_FinalBound == None:
                self.Stat_FinalBound = reduce(formatF1, map(formatF0, self.Stat_FinalBound))
            for i in range(len(self.Stat_BoundList)):
                b = self.Stat_BoundList[i]
                if not b == None:
                    self.Stat_BoundList[i] = reduce(formatF1, map(formatF0, b))

    def LogSMTFile(self, smtFileName):
        self.SMTFile = smtFileName

    def StartTimer(self, name):
        self.Stat_Timer[name] = time()

    def CalcTimePass(self, name):
        return time() - self.Stat_Timer[name]

    @staticmethod
    def Export2Excel(loggers, attrMakers, outputFile):
        wb = xlsxwriter.Workbook(outputFile)
        ws = wb.add_worksheet()
        row = 0
        col = 0
        for a in attrMakers:
            ws.write(row, col, a[0])
            col += 1
        row += 1
        for l in loggers:
            col = 0
            for a in attrMakers:
                ws.write(row, col, a[1](l))
                col += 1
            row += 1
        wb.close()
