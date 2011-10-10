"""
Methods to build and manipulate a STG.
@author: Eric Kadikowski
"""

import networkx as nx
import copy
import itertools as IT


def generate_newSTG() :
    """
    Returns an empty directed graph.
    """
    return nx.DiGraph()


def generate_statespace_str(mc) :
    # not in usage, instead, use generate_initialStates()
    # old: inhalt des statespaces sind strings
    statespace = []
    for i in range(mc.varMax(mc.varIndex(0)) + 1) :
        statespace.append(str(i))
    for i in range(1, len(mc.varnames())) :
        lowerBound = 0
        upperBound = len(statespace)
        extendValue = '0'
        statespace *= mc.varMax(mc.varIndex(i)) + 1
        for j in range(len(statespace)) :
            statespace[j] += extendValue
            lowerBound += 1
            if lowerBound == upperBound :
                lowerBound = 0
                extendValue = str(int(extendValue) + 1)
    return statespace # ["00","10","20","01","11","21"]


def generate_statespace_int(mc) :
    # not in usage, instead, use generate_initialStates()
    statespace = []
    for i in range(mc.varMax(mc.varIndex(0)) + 1) :
        statespace.append([i])
    for i in range(1, len(mc.varnames())) :
        lowerBound = 0
        upperBound = len(statespace)
        extendValue = 0
        cp = copy.deepcopy(statespace)
        for k in range(mc.varMax(mc.varIndex(i))) :
            statespace += copy.deepcopy(cp)
        for j in range(len(statespace)) :
            statespace[j].append(extendValue)
            lowerBound += 1
            if lowerBound == upperBound :
                lowerBound = 0
                extendValue += 1
    return statespace # [[0, 0], [1, 0], [0, 1], [1, 1], [0, 2], [1, 2]]


def generate_initialStates(mc) :
    """
    Compute the initial states, following the rules given by initialRules().
    """
    # get the range of all values
    valuesRange = []
    for var in sorted(mc.varnames()) :
        try:
            min, max = mc.initialRule()[var]
            valuesRange.append(range(min, max+1))
        except :
            valuesRange.append(range(mc.varMax(var)+1))
    
    # compute initial states
    initialStates = []
    for p in IT.product(*valuesRange) : 
        state = []
        for value in p :
            state.append(value)
        initialStates.append(state)
    
    return initialStates


def _toFavoredVal(i1, i2) :
    """
    Used for non-unitary dynamics.
    i1 is changed by plus/minus 1, so that it is closer to i2.
    """
    if i1 < i2 :
        return i1 + 1
    elif i1 > i2 :
        return i1 - 1
    else :
        return i1


def state_to_str(state) :
    """
    Convert a state of type [int] into a string,
    so that they can added as nodes to the STG
    e.g.: [0,0,1,0] --> '0010'
    """
    s = ''
    for val in state :
        s += str(val)
    return s


def _find_activePreds(mc, currState, var) :
    """
    Finds all predecessors which are above their threshold.
    """
    activePreds = ()
    for pred in sorted(mc.predecessors(var)) : # Achtung: Werte aus mc.predecessors() muessen entsprechend der Reihenfolge in parameterSet sortiert sein [alphabetisch]
        if currState[mc.varIndex(pred)] >= mc.threshold((pred, var)) :
            activePreds += pred,
    return activePreds


def _add_edge(currState, nextState, stg, statespace) :
    """
    Add one edge from the predecessor to the successor to the given STG.
    If the successor has not been visited yet, the successor is added to the statespace.
    """
    # add transition
    stg.add_edge(state_to_str(currState), state_to_str(nextState))
    
    # update statespace
    if nextState not in statespace and stg.out_degree(state_to_str(nextState)) == 0 :
        statespace.append(nextState)


def set_edges_sync_str(mc, stg, parameterSet) :
    # not in usage, instead, use set_edges_sync_int()
    """
    See set_edges_sync_int().
    
    statespace - the initial states as array of strings, e.g. ['00', '01'] 
    """
    def _find_activePreds(var) :
        activePreds = ()
        for pred in mc.predecessors(var) : # Achtung: Werte aus mc.predecessors() muessen entsprechend der Reihenfolge in parameterSet sortiert sein [alphabetisch]
            if int(currState[mc.varIndex(pred)]) >= mc.threshold((pred, var)) :
                activePreds += pred,
        return activePreds
    
    
    # Remove all nodes and edges from the graph 
    if len(stg.nodes()) > 0 :
        stg.clear()
    
    
    # Add edges to the graph
    statespace = list(mc.get_initialStates())
    while len(statespace) > 0 :
        for currState in statespace :

            # compute successor state
            nextState = currState[:]
            for i in range(len(currState)) :
                currVar = mc.varIndex(i)  # e.g. 'ERK'
                activePreds = _find_activePreds(currVar)
                if mc.get_unitary() :
                    nextState = nextState[0:i] + str(_toFavoredVal(int(currState[i]), parameterSet[currVar][activePreds])) + nextState[i+1:len(nextState)]
                else :
                    nextState = nextState[0:i] + str(parameterSet[currVar][activePreds]) + nextState[i+1:len(nextState)]
            
            # add transition
            stg.add_edge(currState, nextState)
            
            # update statespace
            statespace.remove(currState)
            if nextState not in statespace and stg.out_degree(nextState) == 0 :
                statespace.append(nextState)


def set_edges_sync_int(mc, stg, parameterSet) :
    """
    Add edges (and implicit the nodes also) to the given STG,
    beginning with the states given by initialStates (given by mc),
    following the rules given by the parameter set.
    The transitions are added synchronous and unitary or non-unitary (given by mc).
    Possible previous nodes and edges from the STG are not deleted.
    
    Parameter:
    mc - the ModelContainer (containing varIndex, unitary, tresholds, ect.)
    stg - the graph to complete (should be empty)
    parameterSet - e.g. {'RAF':{():0,('ERK',):1}, 'ERK':{():2, ('RAF',):0}}
    
    Pseudocode:
    statesToVisit <- initialStates    
    while statesToVisit is not empty :
        for currState in statesToVisit :
            if non-unitary :
                nextState = Bildwert(currState)
            if unitary :
                nextState = changeEachVarJustByOne(currState, Bildwert(currState))
            stg.add_edge(currState, nextState)
            statesToVisit.remove(currState)
            if nextState has not been visited yet (and is not in statesToVisit) :
                statesToVisit.append(nextState)
    
    In words:
    # Strategie:
    # Da im synchronen Fall jeder Zustand genau einen Nachfolgezustand besitzt,
    # wird einfach ueber die statesToVisit iteriert und jeweils eine Kante vom 
    # aktuellen Zustand zum Nachfolgezustand hinzugefuegt. Damit ist der 
    # aktuelle Zustand besucht/abgearbeitet und wird aus den statesToVisit
    # entfernt. Sollte der Nachfolgezustand nicht in statesToVisit enthalten
    # und auch noch nicht besucht/abgearbeitet sein, so wird er den
    # statesToVisit hinzugefuegt.
    """
    
#    # Remove all nodes and edges from the graph 
#    if len(stg.nodes()) > 0 :
#        stg.clear()
    
    # Add edges to the graph
    statesToVisit = list(mc.get_initialStates())
    while len(statesToVisit) > 0 :
        for currState in statesToVisit :
            
            # compute successor state
            nextState = list(currState)
            for pos in xrange(len(currState)) :
                currVar = mc.varIndex(pos)  # e.g. 'ERK'
                activePreds = _find_activePreds(mc, currState, currVar)
                if mc.get_unitary() :
                    nextState[pos] = _toFavoredVal(currState[pos], parameterSet[currVar][activePreds])
                else :
                    nextState[pos] = parameterSet[currVar][activePreds]
            
            # add transition
            stg.add_edge(state_to_str(currState), state_to_str(nextState))
            
            # update statesToVisit
            statesToVisit.remove(currState)
            if nextState not in statesToVisit and stg.out_degree(state_to_str(nextState)) == 0 :
                statesToVisit.append(nextState)
    

def set_edges_async_int(mc, stg, parameterSet) :
    """
    Add edges (and implicit the nodes also) to the given STG,
    beginning with the states given by initialStates (given by mc),
    following the rules given by the parameter set.
    The transitions are added asynchronous and unitary or non-unitary (given by mc).
    Possible previous nodes and edges from the STG are removed.
    
    Parameter:
    mc - the ModelContainer (containing varIndex, unitary, tresholds, ect.)
    stg - the graph to complete
    parameterSet - e.g. {'RAF':{():0,('ERK',):1}, 'ERK':{():2, ('RAF',):0}}
    
    Pseudocode:
    statesToVisit <- initialStates    
    while statesToVisit is not empty :
        currState = statesToVisit[0]
        addTransitionsRec(currState, Bildwert(currState))

    def addTransitionsRec(currState, currBildwert) :
        statesToVisit.remove(currState)
        if fixpoint(currState) :
            stg.add_edge(currState, currState)
        else :
            for (nextState, changedVar) in possibleNextStates(currState, currBildwert) :
                stg.add_edge(currState, nextState)
                if nextState has not been visited yet (and is not in statesToVisit) :
                    statesToVisit.append(nextState)
                if nextState in statesToVisit :
                    addTransitionsRec(nextState, computeNextBildwert(currBildwert, changedVar))    
    """
    def _possibleNextStates(currState, currFavoredState) :
        nextStates = []
        for i in range(len(currState)) :
            if currState[i] != currFavoredState[i] :
                nextState = list(currState)
                if mc.get_unitary() :
                    nextState[i] = _toFavoredVal(currState[i], currFavoredState[i])
                else :
                    nextState[i] = currFavoredState[i]
                nextStates.append((nextState, mc.varIndex(i)))
        return nextStates
    
    def _add_edges(currState, currFavoredState) :
        # update statesToVisit
        statesToVisit.remove(currState)
        
        # add transition(s)
        if currState == currFavoredState :
            stg.add_edge(state_to_str(currState), state_to_str(currState)) # fixpoint
        else :    
            for (nextState, changedVar) in _possibleNextStates(currState, currFavoredState) :
                # add transition and update statesToVisit
                _add_edge(currState, nextState, stg, statesToVisit)
                
                # add following edges recursive
                if nextState in statesToVisit :
                    _add_edges_rec(nextState, currFavoredState, changedVar)
    
    def _add_edges_rec(currState, oldFavoredState, currVar) :
        # build currFavoredState ('Bildzustand')
        currFavoredState = list(oldFavoredState)
        for succ in mc.successors(currVar) :
            activePreds = _find_activePreds(mc, currState, succ)
            currFavoredState[mc.varIndex(succ)] = parameterSet[succ][activePreds]
        
        # add edges (and nodes) to STG
        _add_edges(currState, currFavoredState)

                
    # Remove all nodes and edges from the graph 
    if len(stg.nodes()) > 0 :
        stg.clear()
    
    # Add edges to the graph
    statesToVisit = list(mc.get_initialStates())
    while len(statesToVisit) > 0 :
        
        # current State
        currState = statesToVisit[0]
        
        # compute favored state ('Bildzustand')
        currFavoredState = []
        for i in range(len(currState)) :
            currVar = mc.varIndex(i)
            activePreds = _find_activePreds(mc, currState, currVar)
            currFavoredState.append(parameterSet[currVar][activePreds])
        
        # add transition(s) from current state to successor(s)
        _add_edges(currState, currFavoredState)


def set_edges_priCl_int(mc, stg, parameterSet) :
    """
    Add edges (and implicit the nodes also) to the given STG,
    beginning with the states given by statesToVisit,
    following the rules given by the parameter set.
    The transitions are added synchronous or asynchronous, 
    depending on the priority classes and unitary or non-unitary (given by mc).
    Possible previous nodes and edges from the STG are removed.
    
    Parameter:
    mc - the ModelContainer (containing varIndex, unitary, tresholds, ect.)
    stg - the graph to complete
    parameterSet - e.g. {'RAF':{():0,('ERK',):1}, 'ERK':{():2, ('RAF',):0}}
    
    Pseudocode:
    statesToVisit <- initialStates    
    while statesToVisit is not empty :
        currState = statesToVisit[0]
        addTransitionsRec(currState, Bildwert(currState))

    def addTransitionsRec(currState, currBildwert) :
        statesToVisit.remove(currState)
        if fixpoint(currState) :
            stg.add_edge(currState, currState)
        else :
            if priorityTyp(highPrioVars(currState, currBildwert)) == 'synchronous' :
                if non-unitary :
                    nextState = computeBildwert(currState, highPrioVars)
                if unitary :
                    nextState = changeEachVarJustByOne(currState, computeBildwert(currState, highPrioVars))
                stg.add_edge(currState, nextState)
                if nextState has not been visited yet (and is not in statesToVisit) :
                    statesToVisit.append(nextState)
            else if priorityTyp(highPrioVars(currState, currBildwert)) == 'asynchronous' :
                for (nextState, changedVar) in _possibleNextStates(currState, currBildwert, highPrioVarPos, unitary) :
                    stg.add_edge(currState, nextState)
                    if nextState has not been visited yet (and is not in statesToVisit) :
                        statesToVisit.append(nextState)
                    if nextState in statesToVisit :
                        addTransitionsRec(nextState, computeNextBildwert(currBildwert, changedVar))    
    """
    def _highPrioVarPos(currState, currFavoredState) :
        # find vars with highest priority
        highPrioVarPos = []
        highestPriority = ''
        for pos in range(len(currState)) :
            if currState[pos] != currFavoredState[pos] :
                currPriority = mc.priorityClass(mc.varIndex(pos))
                if currPriority < highestPriority :
                    highPrioVarPos = [pos]
                    highestPriority = currPriority
                elif currPriority == highestPriority :
                    highPrioVarPos.append(pos)
        return highestPriority, highPrioVarPos
    
    def _possibleNextStates(currState, currFavoredState, highPrioVarPos) :
        nextStates = []
        for pos in highPrioVarPos :
            nextState = list(currState)
            if mc.get_unitary() :
                nextState[pos] = _toFavoredVal(currState[pos], currFavoredState[pos])
            else :
                nextState[pos] = currFavoredState[pos]
            nextStates.append((nextState, mc.varIndex(pos)))
        return nextStates
    
    def _add_edges(currState, currFavoredState) :
        # update statesToVisit
        statesToVisit.remove(currState)
        
        # add transition(s)
        if currState == currFavoredState :
            stg.add_edge(state_to_str(currState), state_to_str(currState)) # fixpoint
        else :
            highestPriority, highPrioVarPos = _highPrioVarPos(currState, currFavoredState)
            # add edge synchronous
            if mc.priorityTyp(highestPriority) == 'synchronous' :
                nextState = list(currState)
                for pos in highPrioVarPos :
                    if mc.get_unitary() :
                        nextState[pos] = _toFavoredVal(currState[pos], currFavoredState[pos])
                    else :
                        nextState[pos] = currFavoredState[pos]
                _add_edge(currState, nextState, stg, statesToVisit)
            # add edges asynchronous
            elif  mc.priorityTyp(highestPriority) == 'asynchronous' :
                for (nextState, changedVar) in _possibleNextStates(currState, currFavoredState, highPrioVarPos) :
                    # add edge
                    _add_edge(currState, nextState, stg, statesToVisit)
                    # add following edges recursive
                    if nextState in statesToVisit :
                        _add_edges_rec(nextState, currFavoredState, changedVar)
            # error
            else :
                print 'ERROR: Priority typ not specified.' 
    
    def _add_edges_rec(currState, oldFavoredState, var) :
        # build currFavoredState ('Bildzustand')
        currFavoredState = list(oldFavoredState)
        for succ in mc.successors(var) :
            activePreds = _find_activePreds(mc, currState, succ)
            currFavoredState[mc.varIndex(succ)] = parameterSet[succ][activePreds]
        
        # add edges (and nodes) to STG
        _add_edges(currState, currFavoredState)

                
    # Remove all nodes and edges from the graph 
    if len(stg.nodes()) > 0 :
        stg.clear()
    
    # Add edges to the graph
    statesToVisit = list(mc.get_initialStates())
    while len(statesToVisit) > 0 :
        
        # current State
        currState = statesToVisit[0]
        
        # compute favored state ('Bildzustand')
        currFavoredState = []
        for i in range(len(currState)) :
            var = mc.varIndex(i)
            activePreds = _find_activePreds(mc, currState, var)
            currFavoredState.append(parameterSet[var][activePreds])
        
        # add transition(s) from current state to successor(s)
        _add_edges(currState, currFavoredState)


def _test_priorityClasses() :
    IG = nx.DiGraph()
    IG.add_edges_from([('G0', 'G1'), ('G1', 'G2'), ('G2', 'G3'), ('G3', 'G0')])
    test2 = MC.ModelContainer()
    test2.set_IG(IG)
    test2.set_thresholds({('G0', 'G1'):1, ('G1', 'G2'):1, ('G2', 'G3'):1, ('G3', 'G0'):1})
    test2.set_initialStates()
    test2.set_priorityClasses()
    test2.set_priorityTypes()
    test2.set_dynamics('priorityClasses') #priorityClasses
    test2.set_unitary(True)
    
    test2ParameterSet = {'G0':{():1, ('G3',):0}, 'G1':{():0, ('G0',):1}, 'G2':{():0, ('G1',):1}, 'G3':{():0, ('G2',):1}} 
    test2.compute_STG(test2ParameterSet)
    test2stg = test2.get_stgs()[0]

    print len(test2stg.nodes()), 'test2stg.nodes():', test2stg.nodes()
    print len(test2stg.edges()), 'test2stg.edges():', test2stg.edges()
    print ''
    
    
def _testset() :
    """
    just some tests
    """
    mc = MC.ModelContainer()
    IG = nx.DiGraph()
    IG.add_edges_from([("RAF","ERK"), ("ERK","RAF")])
    mc.set_IG(IG)
    mc.set_thresholds({("RAF","ERK"):1, ("ERK","RAF"):2})
    mc.set_initialStates()
    mc.set_dynamics("synchronous")
    
    # Test 1: unitary sync
    mc.set_unitary(True)
    parameterSet = {"RAF":{():0,("ERK",):1}, "ERK":{():0, ("RAF",):2}}
    mc.compute_STG(parameterSet)
    stg = mc.get_stgs()[-1]
    nodes = ['11', '10', '00', '01', '20', '21']
    edges = [('11', '20'), ('10', '00'), ('00', '00'), ('01', '10'), ('20', '11'), ('21', '21')]
    print 'test 1:'
    print ' ', stg.nodes()
    print ' ', stg.edges()
    if len(stg.nodes()) == len(nodes) and len(stg.edges()) == len(edges) :
        for node in stg.nodes() :
            nodes.remove(node)
        for edge in stg.edges() :
            edges.remove(edge)
    print ' ', len(nodes) == 0 and len(edges) == 0
    
    # Test 2: non-unitary sync
    mc.set_unitary(False)
    parameterSet = {"RAF":{():0,("ERK",):1}, "ERK":{():0, ("RAF",):2}}
    mc.compute_STG(parameterSet)
    stg = mc.get_stgs()[-1]
    nodes = ['11', '10', '00', '01', '20', '21']
    edges = [('11', '20'), ('10', '00'), ('00', '00'), ('01', '20'), ('20', '01'), ('21', '21')]
    print 'test 2:', stg.nodes() == nodes and stg.edges() == edges
    print ' ', stg.nodes()
    print ' ', stg.edges()
    
    # Test 3: unitary sync
    mc.set_unitary(True)
    parameterSet = {"RAF":{():0,("ERK",):1}, "ERK":{():2, ("RAF",):0}}
    mc.compute_STG(parameterSet)
    stg = mc.get_stgs()[-1]
    nodes = ['11', '10', '00', '01', '20', '21']
    edges = [('11', '00'), ('10', '20'), ('00', '10'), ('01', '00'), ('20', '21'), ('21', '11')]
    print 'test 3:', stg.nodes() == nodes and stg.edges() == edges
    print ' ', stg.nodes()
    print ' ', stg.edges()
    
    # Test 4: non-unitary sync
    mc.set_unitary(False)
    parameterSet = {"RAF":{():0,("ERK",):1}, "ERK":{():2, ("RAF",):0}}
    mc.compute_STG(parameterSet)
    stg = mc.get_stgs()[-1]
    nodes = ['11', '10', '00', '01', '20', '21']
    edges = [('11', '00'), ('10', '20'), ('00', '20'), ('01', '00'), ('20', '21'), ('21', '01')]
    print 'test 4:', stg.nodes() == nodes and stg.edges() == edges
    print ' ', stg.nodes()
    print ' ', stg.edges()

    # Test async
    mc.set_dynamics("asynchronous")
    # Test 5: unitary async
    mc.set_unitary(True)
    parameterSet = {"RAF":{():0,("ERK",):1}, "ERK":{():0, ("RAF",):2}}
    mc.compute_STG(parameterSet)
    stg = mc.get_stgs()[-1]
    nodes = ['11', '10', '00', '01', '20', '21']
    edges = [('11', '10'), ('11', '21'), ('10', '00'), ('00', '00'), ('01', '11'), ('01', '00'), ('20', '10'), ('20', '21'), ('21', '21')]
    print 'test 5:', stg.nodes() == nodes and stg.edges() == edges
    print ' ', stg.nodes()
    print ' ', stg.edges()
    
    # Test 6: non-unitary async
    mc.set_unitary(False)
    parameterSet = {"RAF":{():0,("ERK",):1}, "ERK":{():0, ("RAF",):2}}
    mc.compute_STG(parameterSet)
    stg = mc.get_stgs()[-1]
    nodes = ['11', '10', '00', '01', '20', '21']
    edges = [('11', '10'), ('11', '21'), ('10', '00'), ('00', '00'), ('01', '00'), ('01', '21'), ('20', '00'), ('20', '21'), ('21', '21')]
    print 'test 6:', stg.nodes() == nodes and stg.edges() == edges
    print ' ', stg.nodes()
    print ' ', stg.edges()
    
    # Test 7: unitary async
    mc.set_unitary(True)
    parameterSet = {"RAF":{():0,("ERK",):1}, "ERK":{():2, ("RAF",):0}}
    mc.compute_STG(parameterSet)
    stg = mc.get_stgs()[-1]
    nodes = ['11', '10', '00', '01', '20', '21']
    edges = [('11', '10'), ('11', '01'), ('10', '20'), ('00', '10'), ('01', '00'), ('20', '21'), ('21', '11')]
    print 'test 7:', stg.nodes() == nodes and stg.edges() == edges
    print ' ', stg.nodes()
    print ' ', stg.edges()
    
    # Test 8: non-unitary async
    mc.set_unitary(False)
    parameterSet = {"RAF":{():0,("ERK",):1}, "ERK":{():2, ("RAF",):0}}
    mc.compute_STG(parameterSet)
    stg = mc.get_stgs()[-1]
    nodes = ['11', '10', '00', '01', '20', '21']
    edges = [('11', '10'), ('11', '01'), ('10', '20'), ('00', '20'), ('01', '00'), ('20', '21'), ('21', '01')]
    print 'test 8:', stg.nodes() == nodes and stg.edges() == edges
    print ' ', stg.nodes()
    print ' ', stg.edges()

    print ''

    
if __name__=="__main__"  :
    """
    just for testing
    """
    
    _testset()
    #_test_priorityClasses()
    
    test = MC.ModelContainer()
    IG = nx.DiGraph()
    IG.add_edges_from([("VA","VB"),("VD","VA"),("VB","VD"),("VD","VC"),("VC","VB")])
    test.set_IG(IG)
    test.set_thresholds({("VA","VB"):1,("VD","VA"):2,("VB","VD"):1,("VD","VC"):1,("VC","VB"):1})
    test.set_edgeLabels({("VA","VB"):"+",("VD","VA"):"-",("VB","VD"):"+",("VD","VC"):"-",("VC","VB"):"free"})
    test.set_dynamics("synchronous")
    test.set_unitary(True)
    test.set_initialStates()
    test.compute_constraint_parameterSets()
    test_parameterSets = test._parameterSets
    
    test.compute_STG(test_parameterSets[0])
    
    stg = test.get_stgs()[0]
#    print 'stg.nodes():', stg.nodes()
#    print 'stg.edges():', stg.edges()
#    for var in test.varnames() :
#        print var, ':', test.varIndex(var)
#    print ''
    
    
    
    mc = MC.ModelContainer()
    IG = nx.DiGraph()
    IG.add_edges_from([("RAF","ERK"), ("ERK","RAF")])
    mc.set_IG(IG)
    mc.set_thresholds({("RAF","ERK"):1, ("ERK","RAF"):2})
    mc.set_initialRules({})
    mc.set_unitary(False)
    mc.set_dynamics("synchronous")
    mc.set_initialStates()
    mc_parameterSet = {"RAF":{tuple():0,("ERK",):1}, "ERK":{():2, ("RAF",):0}}
    
    params = test._parameterSets
#    for param in params :
#        stg = test.compute_unitary_syncStg(param)
#        print ''
#        print 'stg.nodes():', stg.nodes()
#        print 'stg.edges():', stg.edges()
        

    
    
    print '\n..Done'
