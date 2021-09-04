from IceCaller import IceCaller #pylint: disable=import-error

A1 = 'ATTR$213$ADD$-2$MUL$X$SUB$y'
expr1 = IceCaller.TranslateExpr(A1)
print('{}: {}'.format(expr1, expr1 == '213-2*X-y'))


A2 = 'ATTR$EE$SUB$-2$MUL$X$SUB$y$ADD$-12'
expr2 = IceCaller.TranslateExpr(A2)
print('{}: {}'.format(expr2, expr2 == 'EE+2*X-y-12'))


expr3 = IceCaller.GenerateExpr([A1,A2], [2,-1])
print('{}'.format(expr3))

expr4 = IceCaller.GenerateExpr([A1], [2])
print('{}'.format(expr4))