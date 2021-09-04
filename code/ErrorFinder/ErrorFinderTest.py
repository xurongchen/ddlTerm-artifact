from ErrorFinder import ErrorFinder

ef = ErrorFinder.load('/home/ubuntu/Repository/ICE-Term/tmp/gcd.bpl', ['x','y'])

print(ef.getErrorInput())