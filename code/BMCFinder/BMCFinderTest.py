from BMCFinder import BMCFinder
from Logger import Logger #pylint: disable=import-error

# tmpDir = 'experiment/tmp'
# tempFile = 'experiment/bench/bench-CAV18Full/trex03_false-unreach-call_true-termination-modif.bpl'
# cc = BMCFinder(Logger(), tmpDir, tempFile, ['x1', 'x2', 'x3', 'd1', 'd2', 'd3'], 'i')

# # cc.GenerateConcreteBplFile(8)
# ret = cc.ExecuteBMC(9)
# print(ret)

# # ------
# tmpDir1 = 'experiment/tmp'
# tempFile1 = 'experiment/bench/benchmarks-Instrumented-Lexicographic/BradleyMannaSipma-ICALP2005-Fig1_true-termination.bpl'
# cc1 = BMCFinder(Logger(), tmpDir1, tempFile1, ['x', 'y', 'N'], 'i')
# ret = cc1.ExecuteBMC(4)
# print(ret)


# tmpDir1 = 'experiment/tmp'
# tempFile1 = 'experiment/bench/benchmarks-Instrumented-Lexicographic/BradleyMannaSipma-ICALP2005-Fig1_true-termination.bpl'
# cc1 = BMCFinder(Logger(), tmpDir1, tempFile1, ['x', 'y', 'N'], 'i')
# ret = cc1.ExecuteBMC(4, ret='trace')
# print(ret)

# ('AliasDarteFeautrierGonnord-SAS2010-counterex1a_false-no-overflow', ['n', 'b', 'x', 'y']), # Result: ?

# tmpDir1 = 'experiment/tmp'
# tempFile1 = 'experiment/bench/benchmarks-Instrumented-Lexicographic/AliasDarteFeautrierGonnord-SAS2010-counterex1a_false-no-overflow.bpl'
# cc1 = BMCFinder(Logger(), tmpDir1, tempFile1, ['n', 'b', 'x', 'y'], 'i')
# ret = cc1.ExecuteBMC(4, ret='trace')
# print(ret)

# ('Toulouse-BranchesToLoop-alloca_true-termination', ['x', 'y', 'z']), # Result: ?

tmpDir1 = 'experiment/tmp'
tempFile1 = 'experiment/bench/bench-CAV18Full/Toulouse-BranchesToLoop-alloca_true-termination.bpl'
cc1 = BMCFinder(Logger(), tmpDir1, tempFile1, ['x', 'y', 'z'], 'i')
ret = cc1.ExecuteBMC(10)
print(ret)
