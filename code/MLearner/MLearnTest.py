from MLearn import MLearn #pylint: disable=import-error

ml = MLearn('test.csv')
result = ml.Learning()
print(result)

ml1 = MLearn('test.csv')
result1 = ml1.Learning(target='LSM')
print(result1)