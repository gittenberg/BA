import networkx
import math
import copy
import random
import heapq


class inGraphChecker():
    """provides methods to check TimeSeries directly in a State Transition Graph.
    Use :py:meth:`set_timeseries` to specify a timeseries and monotonicity matrix.
    :py:meth:`set_PS` can change the parameter set.

    .. note::

       These methods work only for **asynchronous** and **unitary** dynamics!

    Settings:
        By setting `self._useAstar` to `True` you can decide whether the new A* algorithm shall be enabled.
        Otherwise the stadnard DFS is used. In case of DFS, Python's internal recursion limit is enlarged 
        if it would not suffice for the recursive :py:meth:`DFS` to traverse the whole state space.
        If not wished, you can prohibit this behaviour using the ``allocateStack`` attribute.
        You can enforce the usage of the recursive or non-recursive version of DFS by setting
        ``self._recursive`` to `True` or `False` after initialization. Standardly the recursive version is used,
        but it switches to the non-recursive version if the state space is too large and ``allocateStack`` is set to False.
    
    Statistics:
        When the time series is specified, a statstics dictionary is generated which counts 
        how many parameter sets are rejected on which states of the time series.
        See the results in :py:meth:`get_statistics`
        
    :param IG: interaction graph
    :type IG: networkx.DiGraph
    :param thresholds: dictionary of thresholds: dict [edge (u,v)] => integer k
    :type thresholds: dict()
    :param ps: ParameterSet as nested dictionary: [string node] => [tuple of strings context] => integer k
    :type ps: dict of dict()
    :param allocateStack: allows the class to allocate more memory for the recursive DFS if needed. If it's set to False and a too large state space occurs, the non-recusive verson of DFS is used.
    :type allocateStack: boolean
    :param MainWindow: Reference to the MainWindow that contains a ``log`` function.
        """
        
    def __init__(self,IG, thresholds, ps, allocateStack=True, MainWindow = None):
        assert(type(IG) == type(networkx.DiGraph()) and IG.nodes())
        for e in IG.edges():
            assert(e in thresholds and type(thresholds[e]) == type(1) and thresholds[e]>=0)
        # no assert for parameter Set, so be careful!
        self._MainWindow = MainWindow
        self._IG = IG
        self._thresholds = thresholds
        self._ps = ps
        self._timeseries = None
        
        self._visited = dict()
        self._recursive=True
        self._useAstar = False
        self._statistics = None
        
        StSpSi = reduce(lambda a,b:a*b, self.getStateSpace(self._IG, self._thresholds).values())
        if StSpSi >= 1000:
            if allocateStack:
                self.SetRecursionLimit(StSpSi)
            else:
                self._recursive=False
                self.message("State space too large for recursion. The non-recursive version is used.","warning")

    def message(self,string, cat = "debug"):
    	if self._MainWindow:
    		self._MainWindow.log(string, cat)
    	else:
	        print string

    def reset_statistics(self):
        """clears the current statistics and adapts it to the current time series.
        The statistics are filled using :py:meth:`proofTimeSeries`."""
        self._statistics = dict(total=0, rejects = [0 for i in range(len(self._timeseries)-1)], accepts = 0)
        
    def get_statistics(self):
        """returns the statistics dictionary. ::

            # Example for a time series with 4 states:
            stats["total"]   = 1000
            stats["accepts"] =  800
            stats["rejects"] = [30, 70, 100] 

        :rtype: dict()"""
        return self._statistics

    def emptymonotonicityMatrix(self):
        """returns an appropriate all-False monotonicity matrix for the ``self._timeseries``.

        :rtype: list of dict[string node] => boolean"""
        m = []
        for i in range( len(self._timeseries)-1 ):
            m.append(dict( [ (v, False) for v in self._IG.nodes() ] ))
        return m
    
    def set_PS(self, ps):
        """sets a new ParameterSet (correctness is not checked).

        :param ps: ParameterSet as nested dictionary: [string node] => [tuple of strings context] => integer k
        :type ps: dict of dict()
        """
    
        self._ps = ps
        
    def set_timeseries(self, timeseries, monotonicity = list()):
        """sets a new timeseries and monotonicity. The time series must at least contain two states.
        See the assert block in the code for  syntax checks.

        This resets the statistics to 0.
        
        :param timeseries: list of states with each state being a dict[string node] => integer state
        :type timeseries: list of dict()
        :param monotonicity: list of monotonicity states with each state being a a dict of monotonicity flags, exactly: dict[string node] => boolean. The list must contain ``len(timeseries) - 1`` dicts, specifiying a monotonicity flag for each component on each state step! If not given, all False is assumed!
        :type monotonicity: list of dict()
        """
        # input check
        assert(len(timeseries)>1)
        for dic in timeseries:
            assert(type(dic) == type(dict()))
            for v in self._IG.nodes():
                assert(v in dic and type(dic[v]) == type(1))
        
        self._timeseries = timeseries
        self.reset_statistics()

        if not monotonicity:
            self._monotonicity = self.emptymonotonicityMatrix()
        else:
            # input check
            assert(len(monotonicity) == len(self._timeseries)-1)
            for dic in monotonicity:
                assert(type(dic) == type(dict()))
                for v in self._IG.nodes():
                    assert(v in dic and type(dic[v]) == type(True))
            self._monotonicity = monotonicity


    def dict2Tuple(self,dic):
        """transforms a state into a hashable tuple of ints, sorted by the nodes' names.

        :param dic: a state
        :type dic: dict[string node] => int k
        """
        return tuple([dic[v] for v in sorted(dic.keys())])
                

    def proofTimeSeries(self):
        """Proofs whether a path through the states of ``self._timeseries`` exists,
        regarding the monotonicity matrix.
        This is done by using the :py:meth:`DFS`[1] function for each step in the timeseries
        and returns False, as soon as one of theses steps is not possible (additionaly a message
        is printed).

        The function also collects statistics on how many PS are rejected in which step of the time series.

        [1] If ``self._useAstar`` is set to True, :py:meth:`Astar` is used instead of DFS.

        [2] Otherwise: If ``self._recursive`` is set to False, :py:meth:`DFS2` is used instead of DFS.

        :rtype: boolean
        """

        # as long as set_timeseries() was used, the timeseries and monotonicity matrix are correct.
        assert(len(self._timeseries)>1)

        self._statistics["total"] += 1
        for i in range(len(self._timeseries)-1):
            # clear visited list
            self._visited=dict()
            
            if (self._useAstar): # use Astar
                if not self.Astar(self._timeseries[i], self._timeseries[i+1], self._monotonicity[i]):
                    self._statistics["rejects"][i] += 1
                    return False
            else:               # use DFS, but still decide between the recursve and non recursive version
                if self._recursive:
                    if not self.DFS(self._timeseries[i], self._timeseries[i+1], self._monotonicity[i]):
                        self._statistics["rejects"][i] += 1
                        return False
                else:
                    if not self.DFS2(self._timeseries[i], self._timeseries[i+1], self._monotonicity[i]):
                        self._statistics["rejects"][i] += 1
                        return False
        # PS accepted
        self._statistics["accepts"] += 1
        return True

    def context(self, state, v):
        """given a State and a variable v, return the context of v.
        The context is a tuple of nodes sorted by the nodes' names.

        :param state: state (as dict)
        :type state: dict[string node] => integer k
        :rtype: tuple of strings"""
        omega = []
        for u in self._IG.predecessors(v):
            if state[u] >= self._thresholds[(u,v)]:
                omega.append(u)
        omega = tuple(sorted(omega))
        return omega

    def SetRecursionLimit(self,k):
        """Enlarges the maximum recursion depth to ``k``. Standardly it is set to 1000.
        If ``k`` is even above 10000, the memory limit for the recursion stack is raised to 512MB
        (instead of standardly 8MB). Additionally a waring is printed.

        Imports ``sys`` and ``resource`` .

        .. note:

           This is highly hardware dependent. Use it with care.

        :param k: maximum recursion depth
        :type k: int
        """
        self.message("max recursion limit raised to %i"%k, "debug")
        import sys
        if k > 10000:
            import resource
            self.message("""Recursion stack memory limit enlarged to 512MB (standardly 8 MB). This can lead to unexpected errors.""", "waring")
            # increase max stack size to 512MB (8MB standard)
            resource.setrlimit(resource.RLIMIT_STACK, (2**29,-1))
        sys.setrecursionlimit(k+1)

    def DFS(self, startState, targetState, monotonicity, recDepth=0):
        """classic depth first search from  ``startState`` to ``targetState`` with
        a **monotonicity heuristic** (see :py:meth:`MonoHeu`).
        Uses the ``self._visited`` dict to mark nodes that have already been visited.::
        
           DFS(start, target):
                if start == target
                    return True
                set_visited(start)
                neighbors = [neighbor states sorted by priority]
                for nextstate in neighbors:
                    if nextstate has already been visited:
                        continue
                    if DFS(nextstate, target):
                        return True
                return False
        
        :param startState,targetState: states
        :type startState,targetState: dict[string node] => integer k
        :param monotonicity: monotonicity flags as dict: if true for node v, v may only change monotonically!
        :type monotonicity: dict[string node] >= boolean
        :rtype: boolean
        """
     
        # found targetState: return True
        if startState == targetState:
            return True

        # otherwise: this state is visited for the first time:
        self._visited[self.dict2Tuple(startState)] = True

        neighbors = self.MonoHeu( startState, targetState, monotonicity)
        for state in neighbors:
            if self.dict2Tuple(state) in self._visited:
                # Neighbor has already been visited without finding the targetState:
                continue
            if self.DFS(state, targetState, monotonicity, recDepth+1):
                return True
        return False

    

    def DFS2(self, startState, targetState, monotonicity):
        """A non recursive version of DFS using a stack (list).
        What used to be a recursive call of :py:meth:`DFS` now leads to a push operation
        with the current state and all its neighbors given by :py:meth:`MonoHeu`.
        The list of neighbors is reversed when first put in, thus can
        be used like a stack too. The search will branch out from a state as long as
        the target hasn't been found and the neighbors list is not yet empty.
        If it is empty, this state is popped and finished.
        
        :param startState,targetState: states
        :type startState,targetState: dict[string node] => integer k
        :param monotonicity: monotonicity flags as dict: if true for node v, v may only change monotonically!
        :type monotonicity: dict[string node] >= boolean
        :rtype: boolean
        """
        stack = []

        # note: neighborList is reversed! So pop() return the best priority
        nei = self.MonoHeu(startState, targetState, monotonicity)
        nei.reverse()
        stack.append( (startState, nei) )

        while stack:

            #DEBUG
            #print "DFS2","\t",len(stack), "\t",len(self._visited)
            
            # get state and its neighbors from the stack
            #       (these 2 lines replace a "show" or "peek" command)
            currentState, neighbors = stack.pop()
            stack.append( (currentState,neighbors) )
            
            #DEBUG
            ####print "DFS2:",self.dict2Tuple(currentState), "neighbors =", [iGc.dict2Tuple(s) for s in neighbors]
            
            # found targetState: break and return True
            if currentState == targetState:
                return True

            # otherwise: this state is visited for the first time:
            self._visited[self.dict2Tuple(currentState)] = True

            # actual depth first search:
            # As long as this state still has neighbors to visit
            if neighbors:
                nextNeighbor = neighbors.pop()
                # Node has already been visited without finding the targetState:
                # don't push it onto the stack!
                if self.dict2Tuple(nextNeighbor) not in self._visited:
                    nextNeighborsNeighbors = self.MonoHeu(nextNeighbor, targetState, monotonicity)
                    nextNeighborsNeighbors.reverse()
                    stack.append( (nextNeighbor, nextNeighborsNeighbors))
            else:
                # There's no path from currentState to targetState, so pop it
                stack.pop()
            # fall back to main while loop
        return False



    def Astar(self, startState, targetState, monotonicity):
        """A best-first search from state `startState` to `targetState`. This algorithm does not
        need a monotoniticity heuristic - it always keep searching from the state that is nearest
        to the target. The method also uses the ``self._visited`` dict to mark nodes that have already been visited.::

            PriorityQ <- start
            while PriorityQ not empty:
                state = PriorityQ.pop() // returns state with
                                        // least distance to the target
                if state == target:
                    return True
                set_visited(state)
                for n in neighbors(state):
                    if n not yet visited:
                        PriorityQ.push (state) // key = |state - target|
                    
                
        :param startState,targetState: states
        :type startState,targetState: dict[string node] => integer k
        :param monotonicity: monotonicity flags as dict: if true for node v, v may only change monotonically!
        :type monotonicity: dict[string node] >= boolean
        :rtype: boolean
        """

        HEAP = []
        heapq.heappush(HEAP, (self.dist(startState,targetState), startState))

        while HEAP:
            
            (d,state) = heapq.heappop(HEAP)

            #print self.dict2Tuple(state), d,
            
            if state == targetState:
                #print "FINISH!!!"
                return True
            
            self._visited[self.dict2Tuple(state)] = True
            
            for v in self._IG.nodes():

                omega = self.context(state, v)
                nextState = state.copy()

                # switch case between increase or decrease:
                if self._ps[v][omega] > state[v]:      # 1. supposed to increase
                    nextState[v] += 1

                    if self.dict2Tuple(nextState) in self._visited:
                        #print ".",
                        continue
                    #print "!",
                    
                    # if this was a monotone transition:
                    if targetState[v] > state[v]:
                        heapq.heappush(HEAP, (d-1, nextState))
                        
                    # if not, but only if non-monotonicity trans. is allowed:
                    elif not monotonicity[v]:
                        heapq.heappush(HEAP, (d+1, nextState))
                        
                elif self._ps[v][omega] < state[v]:    # 2. decrease to decrease
                    nextState[v] -= 1

                    if self.dict2Tuple(nextState) in self._visited:
                        #print ".",
                        continue
                    #print "!",

                    # if this was a monotone transition:
                    if targetState[v] < state[v]:
                        heapq.heappush(HEAP, (d-1, nextState))
                        
                    # if not, but only if non-monotonicity trans. is allowed:
                    elif not monotonicity[v]:
                        heapq.heappush(HEAP, (d+1, nextState))
                        
                # 3. if self._ps[v][omega] == state1[v] then nothing to change!
            #print ""
            
        return False




        
    def dist(self, x, y):
        d = 0
        for v in x:
            d += abs(x[v]-y[v])
        return d



        
    def MonoHeu(self, startState, targetState, monotonicity):
        """Monotonicity heuristic used in :py:meth:`DFS` and :py:meth:`DFS2`.
        The heuristic choses monotonic transitions first in order to accelerate
        the search if the result is positive. It also regards the monotonicity flags, which can enforce
        monotonic transitions for each variable independently.
        
        Seen from a state ``startState``,
        all possible transitions are regarded and ordered by the fact whether the transition walks
        monotonically towards ``targetState`` or not! Output is an ordered list of neighbors.
        Thoses neighbors that trespass against a monotonicity rule are not taken into the list.
        
        :param startState,targetState: states
        :type startState, targetState: dict[string node] => integer k
        :param monotonicity: monotonicity flags as dict: if true for node v, v may only change monotonically!
        :type monotonicity: dict[string node] >= boolean
        :rtype: list of dicts.
        """
        # Order the allowed neighbors by priority: monotone transitions first!
        priority0 = list() # monotone transitions
        priority1 = list() # non-monotone ttransitions
        for v in startState:
            # context of this variable in state startState
            omega = self.context(startState, v)
            nextState = copy.copy(startState) 
            # switch case between increase or decrease:
            if self._ps[v][omega] > startState[v]:      # 1. supposed to increase

                nextState[v] = startState[v]+1

                # if this was a monotone transition:
                if targetState[v] > startState[v]:
                    priority0.append(nextState)
                # if not, but only if non-monotonicity trans. is allowed:
                elif not monotonicity[v]:
                    priority1.append(nextState)
                    
            elif self._ps[v][omega] < startState[v]:    # 2. decrease to decrease

                nextState[v] = startState[v]-1

                # if this was a monotone transition:
                if targetState[v] < startState[v]:
                    priority0.append(nextState)
                # if not, but only if non-monotonicity trans. is allowed:
                elif not monotonicity[v]:
                    priority1.append(nextState)
                    
            # 3. if self._ps[v][omega] == state1[v] then nothing to change!
            
        priority0.extend(priority1)
        return priority0
        
    def getStateSpace(self, IG, thresholds):
        """number of states for each node (maximum threhold +1)
    
        :param IG: interaction graph
        :type IG: networkx.DiGraph
        :param thresholds: dictionary of thresholds: dict [edge (u,v)] => integer k
        :type thresholds: dict()
        :rtype: dict[string] => int
        """
        return dict( [(v, 1+max(0,*[ thresholds[(v,u)] for u in IG.successors(v)]) ) for v in IG.nodes()] )
                      

if __name__ == "__main__":
   

    import randomGraphGenerator as rgg
    import time
    reload(rgg)

##    #Testgraph, 3 nodes, complete
##    G = networkx.DiGraph()
##    for i in range(3):
##        for j in range(3):
##            G.add_edge("V%i"%i, "V%i"%j)
##            
##    #th = rgg.randomThresholds(G)
##    th = {('V0', 'V1'): 2, ('V1', 'V2'): 1, ('V0', 'V0'): 1, ('V2', 'V1'): 1, ('V1', 'V1'): 3, ('V2', 'V0'): 1, ('V2', 'V2'): 2, ('V1', 'V0'): 2, ('V0', 'V2'): 2}
##    
##    #ps = rgg.randomPS(G,th)
##    #ps = {'V0': {('V0', 'V1'): 1, ('V1', 'V2'): 2, ('V0',): 1, ('V1',): 1, ('V0', 'V1', 'V2'): 1, ('V2',): 1, (): 2, ('V0', 'V2'): 2}, 'V1': {('V0', 'V1'): 0, ('V1', 'V2'): 2, ('V0',): 3, ('V1',): 3, ('V0', 'V1', 'V2'): 0, ('V2',): 0, (): 1, ('V0', 'V2'): 3}, 'V2': {('V0', 'V1'): 2, ('V1', 'V2'): 1, ('V0',): 0, ('V1',): 2, ('V0', 'V1', 'V2'): 2, ('V2',): 1, (): 0, ('V0', 'V2'): 2}}
##    # 3er rausnehmen:
##    ps = {'V0': {('V0', 'V1'): 1, ('V1', 'V2'): 2, ('V0',): 1, ('V1',): 1, ('V0', 'V1', 'V2'): 1, ('V2',): 1, (): 2, ('V0', 'V2'): 2}, 'V1': {('V0', 'V1'): 0, ('V1', 'V2'): 2, ('V0',): 3, ('V1',): 3, ('V0', 'V1', 'V2'): 0, ('V2',): 0, (): 1, ('V0', 'V2'): 3}, 'V2': {('V0', 'V1'): 2, ('V1', 'V2'): 1, ('V0',): 0, ('V1',): 2, ('V0', 'V1', 'V2'): 2, ('V2',): 1, (): 0, ('V0', 'V2'): 2}}
##
##    iGc = inGraphChecker(G,th, ps)
##
##    
##    #ts = rgg.randomTimeSeries(G,th,3)
##    ts = [{"V0":0, "V1":0,"V2":0}, {"V0":2, "V1":2,"V2":1}]
##    mon = rgg.randomMonotonyMatrix(ts, 0)
##
##    # Zeitreihe ausgeben
##    print "Time Series:"
##    for i in range(len(ts)):
##        if i!= 0:
##            print "  ",mon[i-1]
##        print "> ",ts[i]
##
##    iGc.set_timeseries(ts,[])
##
##    if iGc.proofTimeSeries():
##        print "\nTime Series accepted!"
##    else:
##        print "\nTime Series rejected!"


    #import matplotlib.pyplot as plt
    #networkx.draw(G)
    #plt.show()


    print "recursive DFS vs non-recursive DFS vs. A*"
    for i in range(3):
        n = random.randint(3,5)
        G = rgg.randomIG(n, 0.5)
        th = rgg.randomThresholds(G, 0.7)
        igc = 0
        igc2 = 0
        astar = 0
        times = dict(rec = 0, stack=0, astar=0)
        print "%i) test grap with %i nodes, state space = "%(i, n) + " x ".join(str(q) for q in rgg.getStateSpace(G,th).values())
        for i in range(20):
            ps = rgg.randomPS(G,th)
            iGc = inGraphChecker(G,th, ps)
            for i in range(10):
                ts = rgg.randomTimeSeries(G,th,random.randint(3,8))
                mon = rgg.randomMonotonyMatrix(ts, 0)
                iGc.set_timeseries(ts,mon)
                #print "TS:", [iGc.dict2Tuple(s) for s in ts]
                
                iGc._recursive=True
                t = time.time()
                if iGc.proofTimeSeries():
                    times["rec"] += time.time()-t
                    igc +=1
                #print ".",

                t = time.time()
                iGc._recursive=False
                if iGc.proofTimeSeries():
                    times["stack"] += time.time()-t
                    igc2 +=1
                #print ".",

                t = time.time()
                iGc._useAstar = True
                if iGc.proofTimeSeries():
                    times["astar"] += time.time()-t
                    astar +=1
                #print ".",
        print "\t DFS rec:  \tacc %i\tin %.4f sec"%(igc, times["rec"])
        print "\t DFS stack:\tacc %i\tin %.4f sec"%(igc2, times["stack"])
        print "\t Astar:    \tacc %i\tin %.4f sec"%(astar, times["astar"])
                    

##    G = rgg.randomIG2(8)
##    Gth = rgg.randomThresholds(G)
##    Gps = rgg.randomPS(G,Gth)
##    Gts = rgg.randomTimeSeries(G,Gth,3)
##    igc = inGraphChecker(G,Gth,Gps)
##    igc.set_timeseries(Gts)
##    
##    while not igc.proofTimeSeries():
##        Gts = rgg.randomTimeSeries(G,Gth,4)
##        Gps = rgg.randomPS(G,Gth)
##        igc.set_PS(Gps)
##        igc.set_timeseries(Gts)
##
##    from pprint import pprint
##    pprint(Gts)
##    igc._useAstar = True
##    print igc.proofTimeSeries()
