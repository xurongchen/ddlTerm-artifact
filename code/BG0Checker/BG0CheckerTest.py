from BG0Checker import BG0Checker
from Logger import Logger #pylint: disable=import-error

tmpDir = 'experiment/tmp'
tempFile = 'experiment/bench/Chen1.02.bpl'
bc = BG0Checker(Logger(), tmpDir, tempFile, ['x'], 'i')

# cc.GenerateConcreteBplFile(8)
ret = bc.ExecuteBG0C()
print(ret)
