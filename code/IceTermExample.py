from IceTerm import IceTerm #pylint: disable=import-error
import random, os 

if not os.path.abspath('.').split('/')[-1] == 'ICE-Term':
    raise EnvironmentError('Please check out to dir ICE-Term.') 

random.seed(1)
it = IceTerm('gcd', 'tmp', 'SourceBench/BaseExamples/gcd_temp/gcd.bpl', 'SourceBench/BaseExamples/gcd/gcd.o', ['x', 'y'], 'test')

it.checkTermination()

