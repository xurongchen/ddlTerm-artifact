import sys,os,random
sys.path.append(os.path.abspath('code'))
# print(sys.path)
from IceTerm import IceTerm #pylint: disable=import-error
from Logger import Logger #pylint: disable=import-error
from IceCaller.IceCaller import IceCaller #pylint: disable=import-error
import pickle
from functools import reduce

lgsFile = 'LeNLeMixed_TO60_Standard202108091350.lgs'
lgsExcel = 'LeNLeMixed_TO60_Standard202108091350.xlsx'


with open(lgsFile,'rb') as lf:
    logList = pickle.load(lf)

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
    ('ToM', lambda x: str(list(map(lambda y: y.Stat_BMCTimeList, x)))),
    ('ToT', lambda x: str(list(map(lambda y: y.Stat_TestTimeList, x)))),
    ('ToB', lambda x: str(list(map(lambda y: y.Stat_BoundTimeList, x)))),
    ('ToI', lambda x: str(list(map(lambda y: y.Stat_InvTimeList, x)))),
    ('FinalInv', lambda x: x[-1].Stat_FinalInv),
    ('FinalBound', lambda x: x[-1].Stat_FinalBound),
    ('SizeC', lambda x: x[0].Stat_CFileSize),
    ('SizeBpl', lambda x: x[0].Stat_BplFileSize),
    ('RoB:ICE', lambda x: len(list(filter(lambda t:t>0, reduce(lambda z,r: z+r, map(lambda y: y.Stat_InvTimeList, x), []))))),
    ('RoB:BMC', lambda x: len(list(filter(lambda t:t>0, reduce(lambda z,r: z+r, map(lambda y: y.Stat_BMCTimeList, x), []))))),
    ('RoB:CBC', lambda x: len(list(filter(lambda t:t>0, reduce(lambda z,r: z+r, map(lambda y: y.Stat_CBCTimeList, x), []))))),
]

Logger.Export2Excel(logList, attrMakers, lgsExcel)

