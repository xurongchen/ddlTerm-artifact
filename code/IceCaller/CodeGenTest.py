from IceCaller import IceCaller #pylint: disable=import-error
import sys
import os
sys.path.append(os.path.abspath('code'))

from Logger import Logger #pylint: disable=import-error

tmpDir = 'experiment/tmp'
tempFile = 'experiment/bench-test/lexical01/lexical01.bpl'
ic = IceCaller(Logger(), tmpDir, tempFile)

lexRank = [['x'], ['y'], ['x']]
ic.GenerateConcreteBplFileLexicalTemplate(lexRank)
