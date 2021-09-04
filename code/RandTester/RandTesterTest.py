from RandTester import RandTester #pylint: disable=import-error

rt = RandTester(['x','y'],'./gcd.o')
rt.generateBound(rt.randFunction(lb=-100,ub=100),round=50,duplicate=False,outputFile='bound1.csv')
rt.generateBound(rt.randFunction(lb=-3,ub=3,strategy='nearby',nearby=(10,10)),round=2,duplicate=False,outputFile='bound2.csv')
rt.generateBound(rt.randFunction(lb=-100,ub=100),mode='number',number=100,duplicate=False,outputFile='bound3.csv')

