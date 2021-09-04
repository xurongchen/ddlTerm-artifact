import os
from IceCaller import IceCaller

projectDir = '/'.join(os.getcwd().split('/')[:-2])
tmpfileDir = projectDir + '/tmp'
exampleTempFile = projectDir + '/SourceBench/BaseExamples/gcd_temp/gcd.bpl'
ice_Term = IceCaller(tmpfileDir, exampleTempFile)
# ice_Term.CleanTmpFiles()
# ice_Term.GenerateConcreteBplFile([('i','x')])
# ice_Term.ExecuteICE()
# print('=' * 25)
ice_Term.GenerateConcreteBplFile([('i','x+y')])
r = ice_Term.ExecuteICE()
print(r['Invariant'])
# ice_Term.CleanTmpFiles()

