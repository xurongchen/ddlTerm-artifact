import os
import argparse
import re

tempfilePath = ''
projectDir = '/'.join(os.getcwd().split('/')[:-1])

boogieDir = projectDir + '/ice/popl16_artifact/Boogie/Binaries'
tmpfileDir = projectDir + '/tmp'

parser = argparse.ArgumentParser()

parser.add_argument("-f","-file",type=str,help='template bpl file to parse')

args = parser.parse_args()

class ICE_Term:
    ReList = [r'(.*)%M:(.*)%(.*)',r'(.*)%Decl:(.*)%(.*)',r'(.*)%Inv:(.*)%(.*)']
    def GenerateConcreteBplFile(self, tempfile, tmpDir, replaceList = []):
        fileOpen = open(tempfile)
        fileName = tempfile.split('/')[-1]
        
        if not os.path.exists(tmpDir):
            os.makedirs(tmpDir)
        outFile = os.path.join(tmpDir, fileName)
        outFileOpen = open(outFile, 'w')

        tempContent = fileOpen.readlines()
        fileOpen.close()
        for line in tempContent:
            for patternId in range(len(self.ReList)):
                pattern = self.ReList[patternId]
                result = re.search(pattern, line)
                if not result is None:
                    identifierI = result.group(2).replace(' ','')
                    subReplace = list(filter(lambda x: x[0]==identifierI, replaceList))
                    if patternId == 0:
                        print('match M for:{}'.format(identifierI))
                        formula = ''
                        for subId in range(len(subReplace)):
                            formula += ('' if subId == 0 else ' && ') + identifierI + ' > ' + subReplace[subId][1].replace(' ','')
                        outFileOpen.write(result.group(1) + formula + result.group(3))
                    elif patternId == 1:
                        print('match Decl for:{}'.format(identifierI))
                        args = ''
                        for subId in range(len(subReplace)):
                            rename = subReplace[subId][1].replace(' ','')
                            rename = rename.replace('+','$ADD$')
                            rename = rename.replace('-','$SUB$')
                            rename = rename.replace('*','$MUL$')
                            rename = rename.replace('div','$DIV$')
                            rename = 'ATTR$' + rename

                            args += ', ' + rename + ':int'
                        outFileOpen.write(result.group(1) + args + result.group(3))
                    else:
                        print('match Inv for:{}'.format(identifierI))
                        args = ''
                        for subId in range(len(subReplace)):
                            args += ', ' + subReplace[subId][1]
                        outFileOpen.write(result.group(1) + args + result.group(3))
                    
                    break
                else:
                    if patternId == len(self.ReList) - 1:
                        outFileOpen.write(line)
        outFileOpen.close()

ice_term = ICE_Term()
exampleTempFile = projectDir + '/SourceBench/BaseExamples/gcd_temp/gcd.bpl'
ice_term.GenerateConcreteBplFile(exampleTempFile, tmpfileDir, [('i', 'x'),('i', 'y')])
