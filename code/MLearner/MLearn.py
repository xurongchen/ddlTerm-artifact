import pandas as pd
import numpy as np
from scipy import optimize
from sklearn.cluster import KMeans
from queue import PriorityQueue
from functools import partial

class MLearn:
    ...
    def __init__(self, logger, learningInput='round.csv', add1 = True, trustedMax = 100):
        self.Logger = logger
        learningDataFrame = pd.read_csv(learningInput)
        if add1:
            learningDataFrame.insert(0, '1', 1)
        data = np.array(learningDataFrame.to_numpy())
        self.Vars = data[:,:-1]
        self.Round = data[:,-1]
        self.VarNum = self.Vars.shape[1]
        self.StateNum = self.Vars.shape[0]
        self.TrustedMax = trustedMax
        self.ConstScale = 1
        self.ConstScaleMAX = 100000000000000
        ...

    # def optimize_target(self, method='LSM_L2'):
    def optimize_target(self, method='LSM_L2'):
        def LSM_L2(A, Vars, Round):
            return (np.sum((np.dot(Vars,A) - Round) ** 2) / Vars.shape[0] + np.sum(A ** 2)) / self.ConstScale
        def LSM(A, Vars, Round):
            return (np.sum((np.dot(Vars,A) - Round) ** 2) / Vars.shape[0]) / self.ConstScale
        def L2(A, Vars, Round):
            return np.sum(A ** 2) / self.ConstScale
        def L2_LittleLSM(A, Vars, Round):
            return (np.sum(A ** 2) + 0.05 * np.log(1 + np.sum((np.dot(Vars,A) - Round) ** 2) / Vars.shape[0])) / self.ConstScale

        if method == 'LSM_L2':
            return LSM_L2
        elif method == 'LSM':
            return LSM
        elif method == 'L2':
            return L2
        elif method == 'L2_LittleLSM':
            return L2_LittleLSM

        return None

    def bounds(self, btype='noBound'):
        if btype == 'noBound':
            CLB = np.array([-np.inf] * self.VarNum).T
            CUB = np.array([np.inf] * self.VarNum).T
            ConstBound = optimize.Bounds(CLB, CUB)
            return ConstBound
        
        return None

    def stdOptimize(self, target='LSM_L2', bound='noBound', initArgs=None, opVars=None, opRounds=None):
        if type(opVars) == type(None):
            opVars = self.Vars
        if type(opRounds) == type(None):
            opRounds = self.Round
        
        A0 = np.array([0] * self.VarNum).T
        if initArgs != None:
            A0 = initArgs
        LC = optimize.LinearConstraint(opVars, opRounds, np.inf)
        return optimize.minimize(self.optimize_target(target), A0, args=(opVars, opRounds), bounds=self.bounds(bound), constraints=(LC,))

    def Learning(self, strategy='CLearn-best', target='LSM_L2', bound='noBound', initArgs=None, softLen=None, ClusterNum=10):
        # print('[Debug] MLearning variables: {}'.format(self.Vars))
        # print('[Debug] ClusterNum:', ClusterNum)
        if strategy == 'CLearn-best':
            self.Logger.Log('[Info] M strategy: CLearn-best')
            baseLearner = partial(self.RefinedLearning, target=target, bound=bound, initArgs=None, strategy='best')
            A_Int_List = self.ClusterLearning(baseLearner, (self.Vars, self.Round), ClusterNum=ClusterNum)
            if type(A_Int_List) == type(None):
                return {'success': False, 'message': 'No suitable representation.'}
            return {'success': True, 'Args': A_Int_List}
        elif strategy == 'CLearn-single-best':
            self.Logger.Log('[Info] M strategy: CLearn-single-best')
            baseLearner = partial(self.SingleLearning, target=target, bound=bound, initArgs=None, strategy='best')
            A_Int_List = self.ClusterLearning(baseLearner, (self.Vars, self.Round), softLen = softLen, ClusterNum=ClusterNum)
            if type(A_Int_List) == type(None):
                return {'success': False, 'message': 'No suitable representation.'}
            return {'success': True, 'Args': A_Int_List}
        elif strategy == 'single-best':
            self.Logger.Log('[Info] M strategy: single-best')
            A_Int_List = self.SingleLearning((self.Vars, self.Round), target, bound, initArgs)
            if type(A_Int_List) == type(None):
                return {'success': False, 'message': 'No single representation.'}
            return {'success': True, 'Args': A_Int_List}
        elif strategy == 'best':
            A_Int_List = self.RefinedLearning((self.Vars, self.Round), target, bound, initArgs)
            return {'success': True, 'Args': A_Int_List}
        elif strategy == 'roundOld':
            NumUnsolved = self.StateNum
            VarsUnsolved = self.Vars
            RoundsUnsolved = self.Round
            A_Int_List = []
            while NumUnsolved > 0:
                result = self.stdOptimize(target, bound, initArgs, VarsUnsolved, RoundsUnsolved)
                if not result.success:
                    return {'success': False, 'message': result.message}
                A_Float = result.x
                A_Int = np.round(A_Float)
                Result_Int = np.dot(VarsUnsolved, A_Int) - RoundsUnsolved
                newNumUnsolved = 0
                newVarsUnsolved = np.array([])
                newRoundsUnsolved = np.array([])
                for i in range(len(Result_Int)):
                    if Result_Int[i] < 0:
                        if newNumUnsolved == 0:
                            newVarsUnsolved = np.array([VarsUnsolved[i]])
                            newRoundsUnsolved = np.array([RoundsUnsolved[i]])
                        else:
                            newVarsUnsolved = np.concatenate((newVarsUnsolved, np.array([VarsUnsolved[i]])), axis=0)
                            newRoundsUnsolved = np.concatenate((newRoundsUnsolved, np.array([RoundsUnsolved[i]])), axis=0)
                        newNumUnsolved += 1
                if newNumUnsolved == NumUnsolved:
                    self.Logger.Log('[Info] No decreasing number of unsolved program states using ROUND. Try ABS_CELL...')
                    A_Int = np.ceil(np.abs(A_Float)) * np.sign(A_Float)
                    Result_Int = np.dot(VarsUnsolved, A_Int) - RoundsUnsolved
                    newNumUnsolved = 0
                    newVarsUnsolved = np.array([])
                    newRoundsUnsolved = np.array([])
                    for i in range(len(Result_Int)):
                        if Result_Int[i] < 0:
                            if newNumUnsolved == 0:
                                newVarsUnsolved = np.array([VarsUnsolved[i]])
                                newRoundsUnsolved = np.array([RoundsUnsolved[i]])
                            else:
                                newVarsUnsolved = np.concatenate((newVarsUnsolved, np.array([VarsUnsolved[i]])), axis=0)
                                newRoundsUnsolved = np.concatenate((newRoundsUnsolved, np.array([RoundsUnsolved[i]])), axis=0)
                            newNumUnsolved += 1
                    if newNumUnsolved == NumUnsolved:
                        return {'success': False, 'message': 'No decreasing number of unsolved program states!'}
                NumUnsolved = newNumUnsolved
                VarsUnsolved = newVarsUnsolved
                RoundsUnsolved = newRoundsUnsolved
                A_Int_List.append(A_Int)
            return {'success': True, 'Args': A_Int_List}

        else:
            raise NotImplementedError('Unsupported learning strategy for M.')

    # Single learning is used in lexical method, which only return a satisfied result or None.
    # This method may be not completed
    def SingleLearning(self,dataSet, target='LSM_L2', bound='noBound', initArgs=None, strategy='best'):
        self.Logger.Log('[Info] MLearn Size = {}'.format(dataSet[0].shape[0]))
        if dataSet == None:
            raise RuntimeError('Dataset is None!')
        fArg = self.argLearn(dataSet, target, bound, initArgs)
        if type(fArg) == type(None):
            return None
        if self.TrustedMax != None:
            for v in fArg:
                if abs(v) > self.TrustedMax:
                    return None
        if strategy == 'best':
            iArg, N, _ = self.getBestIntArg(fArg, dataSet[0], dataSet[1], target)
        elif strategy == 'round':
            # Try ROUND:
            N = 0
            iArg = self.argsRound(fArg)
            result = np.dot(dataSet[0], iArg) - dataSet[1]
            for it in result:
                if it >= 0:
                    N = N + 1
        if N < dataSet[0].shape[0]:
            return None
        return [iArg]

    # Refined learning is a new learn method: dataSet is a 2-tuple with (VARS:list, ROUNDS:list)
    def RefinedLearning(self, dataSet, target='LSM_L2', bound='noBound', initArgs=None, strategy='best'):
        self.Logger.Log('[Info] MLearn Size = {}'.format(dataSet[0].shape[0]))
        if dataSet == None:
            return []
        fArg = self.argLearn(dataSet,target,bound,initArgs)
        if type(fArg) == type(None):
            return None
        if strategy == 'best':
            iArg, _, _ = self.getBestIntArg(fArg, dataSet[0], dataSet[1], target)
        elif strategy == 'round':
            # Try ROUND:
            iArg = self.argsRound(fArg)
        else:
            raise RuntimeError('Unknown strategy in MLearn.')
        retSAT, retUNSAT = self.dataSetSplit(dataSet, iArg)
        if strategy == 'round':   
            if retUNSAT == None:
                return [iArg]
            if retSAT == None:
                self.Logger.Log('[Info] No decreasing number of unsolved program states using ROUND. Try ABS_CELL...')
                iArg = self.argsAbsCell(fArg)
                retSAT, retUNSAT = self.dataSetSplit(dataSet, iArg)
        
        if retUNSAT == None:
            return [iArg]
        if retSAT == None:
            self.Logger.Log(dataSet)
            self.Logger.Log(fArg)
            raise RuntimeError('MLearn RE: No decreasing number of unsolved program states.')
        argsUNSAT = self.RefinedLearning(retUNSAT, target, bound, initArgs)

        leftSAT = retSAT
        for arg in argsUNSAT:
            solved, _ = self.dataSetSplit(dataSet, arg)
            leftSAT = self.dataSetDiff(leftSAT, solved)
            if leftSAT == None:
                return argsUNSAT
        return argsUNSAT + self.RefinedLearning(leftSAT, target, bound, initArgs)

    def argLearn(self, dataSet, target='LSM_L2', bound='noBound', initArgs=None):
        while True:
            try:
                result = self.stdOptimize(target, bound, initArgs, dataSet[0], dataSet[1])
                if not result.success:
                    self.Logger.Log('[Warning] MLearn: {}'.format(result.message))
                    if self.ConstScaleMAX < self.ConstScale:
                        return None
                    if result.message == 'Inequality constraints incompatible':
                        return None
                    elif result.message == 'Iteration limit reached':
                        self.ConstScale *= 100
                        continue
                    elif result.message == 'Singular matrix E in LSQ subproblem':
                        self.ConstScale *= 100
                        continue
                    elif result.message == 'Positive directional derivative for linesearch':
                        self.ConstScale *= 100
                        continue
                    raise RuntimeError('MLearn RE: {}'.format(result.message))
                # return {'success': False, 'message': result.message}
                break
            except OverflowError:
                self.Logger.Log('[Warning] MLearn: Overflow!')
                return None
        return result.x

    def argsRound(self, A_Float):
        return np.round(A_Float)

    def argsAbsCell(self, A_Float):
        return np.ceil(np.abs(A_Float)) * np.sign(A_Float)
        
    # cut is an int_arg
    def dataSetSplit(self, dataSet, cut):
        Result_Int = np.dot(dataSet[0], cut) - dataSet[1]

        NumSolved = 0
        VarsSolved = np.array([])
        RoundsSolved = np.array([])

        NumUnsolved = 0
        VarsUnsolved = np.array([])
        RoundsUnsolved = np.array([])
        for i in range(len(Result_Int)):
            if Result_Int[i] >= 0:
                if NumSolved == 0:
                    VarsSolved = np.array([dataSet[0][i]])
                    RoundsSolved = np.array([dataSet[1][i]])
                else:
                    VarsSolved = np.concatenate((VarsSolved, np.array([dataSet[0][i]])), axis=0)
                    RoundsSolved = np.concatenate((RoundsSolved, np.array([dataSet[1][i]])), axis=0)
                NumSolved += 1
            else:
                if NumUnsolved == 0:
                    VarsUnsolved = np.array([dataSet[0][i]])
                    RoundsUnsolved = np.array([dataSet[1][i]])
                else:
                    VarsUnsolved = np.concatenate((VarsUnsolved, np.array([dataSet[0][i]])), axis=0)
                    RoundsUnsolved = np.concatenate((RoundsUnsolved, np.array([dataSet[1][i]])), axis=0)
                NumUnsolved += 1
        
        retSAT = (VarsSolved, RoundsSolved)
        retUNSAT = (VarsUnsolved, RoundsUnsolved)
        if NumSolved == 0:
            retSAT = None
        if NumUnsolved == 0:
            retUNSAT = None
        
        return retSAT, retUNSAT

    def dataSetDiff(self, dataSetA, dataSetB):
        sA = set()
        numA = dataSetA[0].shape[0]
        for i in range(numA):
            # print(dataSetA)
            varsT = tuple(dataSetA[0][i])
            roundT = dataSetA[1][i]
            sA.add((varsT,roundT))

        sB = set()
        numB = dataSetB[0].shape[0]
        for i in range(numB):
            varsT = tuple(dataSetB[0][i])
            roundT = dataSetB[1][i]
            sB.add((varsT,roundT))

        sD = sA - sB
        NumLeft = 0
        VarsLeft = np.array([])
        RoundsLeft = np.array([])
        sDList = list(sD)
        for i in range(len(sDList)):
            if NumLeft == 0:
                VarsLeft = np.array([list(sDList[i][0])])
                RoundsLeft = np.array([sDList[i][1]])
            else:
                VarsLeft = np.concatenate((VarsLeft, np.array([list(sDList[i][0])])), axis=0)
                RoundsLeft = np.concatenate((RoundsLeft, np.array([sDList[i][1]])), axis=0)
            NumLeft += 1

        if NumLeft == 0:
            return None
        return (VarsLeft, RoundsLeft)

    def getBestIntArg(self, A_Float, Vars, Round, target):
        N,L,A_Int =  self.getBestIntArgDFS(A_Float, Vars, Round, 0, target)
        # print(A_Int, N, L)
        return A_Int, N, L


    def getBestIntArgDFS(self, A, Vars, Round, idx, target):
        if idx == len(A):
            passNum = 0
            result = np.dot(Vars, A) - Round
            for it in result:
                if it >= 0:
                    passNum = passNum + 1
            loss = self.optimize_target(target)(A, Vars, Round)
            # print(passNum,loss,'DFS')
            
            return passNum, loss, A
        LA = np.array(A)
        RA = np.array(A)
        LA[idx] = np.floor(LA[idx])
        RA[idx] = np.ceil(RA[idx])
        LNum, LLoss, LBA = self.getBestIntArgDFS(LA, Vars, Round, idx+1,target)   
        RNum, RLoss, RBA = self.getBestIntArgDFS(RA, Vars, Round, idx+1,target)   
        if LNum > RNum or (LNum == RNum and LLoss < RLoss):
            return LNum, LLoss, LBA
        return RNum, RLoss, RBA

    def multiselectionRefineLearning(self, dataSet, target='LSM_L2', bound='noBound', initArgs=None, strategy='best'):
        ...

    # baseLearningFunc should have only one arg: dataset!
    def ClusterLearning(self, baseLearningFunc, dataset, ClusterNum = 10, MinimalMultiple = 5, softLen=None):
        defaultClusterNum = ClusterNum
        VARS = dataset[0]
        ROUNDS = dataset[1]

        if softLen == None:
            caseNum = len(ROUNDS)
        else:
            caseNum = softLen

        if caseNum // MinimalMultiple <= defaultClusterNum:
            defaultClusterNum = caseNum // MinimalMultiple
        if defaultClusterNum == 0:
            defaultClusterNum = 1
        self.Logger.Log('[Info] Cluster to {} groups.'.format(defaultClusterNum))
        # kmeans = KMeans(n_clusters=defaultClusterNum, random_state=0, n_jobs=1).fit(VARS[:caseNum])
        kmeans = KMeans(n_clusters=defaultClusterNum, random_state=0).fit(VARS[:caseNum])
        # print(kmeans.labels_)
        # TODO: SHOW THE PIC RESULT OF KMEANS HERE！！！
        # caseNum = len(ROUNDS)
        SubDatasets = [[np.array([]), np.array([])]] * defaultClusterNum
        SubDatasetsLen = [0] * defaultClusterNum
        for idx in range(caseNum):
            labelId = kmeans.labels_[idx]
            if SubDatasetsLen[labelId] == 0:
                SubDatasets[labelId] = [np.array([VARS[idx]]), np.array([ROUNDS[idx]])]
            else:
                SubDatasets[labelId][0] = np.concatenate((SubDatasets[labelId][0], np.array([VARS[idx]])), axis = 0)
                SubDatasets[labelId][1] = np.concatenate((SubDatasets[labelId][1], np.array([ROUNDS[idx]])), axis = 0)
            SubDatasetsLen[labelId] += 1

        for labelId in range(defaultClusterNum):
            if SubDatasetsLen[labelId] == 0:
                continue
            for idx in range(caseNum, len(ROUNDS)):
                SubDatasets[labelId][0] = np.concatenate((SubDatasets[labelId][0], np.array([VARS[idx]])), axis = 0)
                SubDatasets[labelId][1] = np.concatenate((SubDatasets[labelId][1], np.array([ROUNDS[idx]])), axis = 0)
                SubDatasetsLen[labelId] += 1

        ResultSet = set()
        for lb in range(defaultClusterNum):
            if SubDatasetsLen[lb] == 0:
                continue
            SubResult = baseLearningFunc(SubDatasets[lb])
            if SubResult == None:
                continue
            SubResultSet = set(map(tuple, SubResult))
            ResultSet = ResultSet | SubResultSet

        sortedResultCandidates = list(ResultSet)
        sortedResultCandidates.sort(key = MLearn.BoundSet.CalcLoss)
        self.Logger.Log('[Info] Candidates: {}'.format(sortedResultCandidates))

        pq = PriorityQueue()
        pq.put(MLearn.BoundSet(unsolvedID = set(range(len(VARS)))))
        while not pq.empty():
            front = pq.get()
            nextElems = front.makeNextSet(sortedResultCandidates, VARS, ROUNDS)
            if len(nextElems) > 0:
                if nextElems[0].checkCoverage():
                    self.Logger.Log('[Info] Selected candidates: {}'.format(nextElems[0].Bounds))
                    return nextElems[0].Bounds
                for e in nextElems:
                    pq.put(e)
        return None # No solution found!
        # raise RuntimeError('No result found!')

    class BoundSet:

        @staticmethod
        def CalcLoss(B):
            # print(np.sum(np.array(list(B))** 2))
            return np.sum(np.array(list(B))** 2 + 0.001)

        def __init__(self, loss = 0, bounds = [], nextbound = 0, unsolvedID = set()):
            self.Loss = loss
            self.Bounds = bounds
            self.NextBound = nextbound
            self.UnsolvedID = unsolvedID

        # BoundList must be sorted!
        def makeNextSet(self, BoundList, Vars, Rounds):
            # print(BoundList)
            if self.NextBound == len(BoundList):
                return []
            return [self.makeNextSetAddBound(BoundList[self.NextBound], Vars, Rounds), self.makeNextSetSkip()]
        
        def makeNextSetAddBound(self, Bound, Vars, Rounds):
            unsolvedID = self.UnsolvedID
            solvedID = set()
            for u in unsolvedID:
                if np.dot(Vars[u], Bound) >= Rounds[u]:
                    solvedID.add(u)
            return MLearn.BoundSet(self.Loss + MLearn.BoundSet.CalcLoss(Bound), self.Bounds + [Bound], self.NextBound + 1, unsolvedID - solvedID)

        def makeNextSetSkip(self):
            return MLearn.BoundSet(self.Loss, self.Bounds, self.NextBound + 1, self.UnsolvedID)

        def checkCoverage(self):
            return len(self.UnsolvedID) == 0
        
        def __lt__(self, other):
            if self.Loss < other.Loss:
                return True
            elif self.Loss > other.Loss:
                return False
            return len(self.Bounds) <= len(other.Bounds)