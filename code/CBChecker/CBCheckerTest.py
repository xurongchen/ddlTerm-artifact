from CBChecker import CBChecker
from Logger import Logger #pylint: disable=import-error

tmpDir = 'experiment/tmp'
tempFile = 'experiment/bench/Chen1.02.bpl'
cc = CBChecker(Logger(), tmpDir, tempFile, ['x'], 'i')

# cc.GenerateConcreteBplFile(8)
ret = cc.ExecuteCBC(2)
print(ret)
