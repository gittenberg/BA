"""
Class to build and manipulate a STG.
@author: Eric Kadikowski
"""

import networkx as nx #@UnresolvedImport
import itertools as IT

class STG() :

    def __init__(self) :
        self._stg = nx.DiGraph()


    def _add_edge(self, currState, nextState, stg, statespace) :
        """
        Add one edge from the predecessor to the successor to the given STG.
        If the successor has not been visited yet, the successor is added to the statespace.
        """
        # add transition
        stg.add_edge(self.state_to_str(currState), self.state_to_str(nextState))

        # update statespace
        if nextState not in statespace and stg.out_degree(self.state_to_str(nextState)) == 0 :
            statespace.append(nextState)


    def _find_activePreds(self, mc, currState, var) :
        """
        Finds all predecessors which are above their threshold.
        """
        activePreds = ()
        for pred in sorted(mc.predecessors(var)) : # Achtung: Werte aus mc.predecessors() muessen entsprechend der Reihenfolge in parameterSet sortiert sein [alphabetisch]
            if currState[mc.varIndex(pred)] >= mc.threshold((pred, var)) :
                activePreds += pred,
        return activePreds


    def _toFavoredVal(self, i1, i2) :
        """
        Used for unitary dynamics.
        i1 is changed by plus/minus 1, so that it is closer to i2.
        """
        if i1 < i2 :
            return i1 + 1
        elif i1 > i2 :
            return i1 - 1
        else :
            return i1


    def state_to_str(self, state) :
        """
        Convert a state of type [int] into a string,
        so that they can added as nodes to the STG
        e.g.: [0,0,1,0] --> '0010'
        """
        s = ''
        for val in state :
            s += str(val)
        return s


    def set_edges_sync(self, mc, parameterSet) :
        """
        Add edges (and implicit the nodes also) to the self._STG (should be empty),
        beginning with the states given by initialStates (given by mc),
        following the rules given by the parameter set.
        The transitions are added synchronous and unitary or non-unitary (given by mc).
        Possible previous nodes and edges from the STG are not deleted.
        
        Parameter:
        mc - the ModelContainer (containing varIndex, unitary, tresholds, ect.)
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
        
        # Add edges to the graph
        statesToVisit = list(mc.get_initialStates())
        while len(statesToVisit) > 0 :
            for currState in statesToVisit :
                
                # compute successor state
                nextState = list(currState)
                for pos in xrange(len(currState)) :
                    currVar = mc.varIndex(pos)  # e.g. 'ERK'
                    activePreds = self._find_activePreds(mc, currState, currVar)
                    if mc.get_unitary() :
                        nextState[pos] = self._toFavoredVal(currState[pos], parameterSet[currVar][activePreds])
                    else :
                        nextState[pos] = parameterSet[currVar][activePreds]
                
                # add transition
                self._stg.add_edge(self.state_to_str(currState), self.state_to_str(nextState))
                
                # update statesToVisit
                statesToVisit.remove(currState)
                if nextState not in statesToVisit and self._stg.out_degree(self.state_to_str(nextState)) == 0 :
                    statesToVisit.append(nextState)
        
    
    def set_edges_async(self, mc, parameterSet) :
        """
        Add edges (and implicit the nodes also) iterative to the self._STG (should be empty),
        beginning with the states given by initialStates (given by mc),
        following the rules given by the parameter set.
        The transitions are added asynchronous and unitary or non-unitary (given by mc).
        Possible previous nodes and edges from the STG are not deleted.
        
        Parameter:
        mc - the ModelContainer (containing varIndex, unitary, tresholds, ect.)
        parameterSet - e.g. {'RAF':{():0,('ERK',):1}, 'ERK':{():2, ('RAF',):0}}
        
        Pseudocode:
        statesToVisit <- initialStates    
        for currState in statesToVisit :
            if currentState is a fixpoint :
                stg.add_edge(currState, currState)
            else :
                for each position of currState :
                    if currState[position] != Bildwert(currState[position]) :
                        nextState <- currState
                        if non-unitary :
                            nextState[position] <- Bildwert(currState[position])
                        elif unitary :
                            nextState[position] <- changeVarJustByOne(currState[position], Bildwert(currState[position]))
                        stg.add_edge(currState, nextState)
                        if nextState has not been visited yet (and is not in statesToVisit) :
                            statesToVisit.append(nextState)
            statesToVisit.remove(currState)
        """
        
        statesToVisit = list(mc.get_initialStates())
        while len(statesToVisit) > 0 :
            for currState in statesToVisit :
                fixpoint = True
                
                # compute all possible next States
                for pos in xrange(len(currState)) :
    
                    # compute Bildwert
                    var = mc.varIndex(pos)
                    activePreds = self._find_activePreds(mc, currState, var)
                    favoredValue = parameterSet[var][activePreds]
                    
                    if currState[pos] != favoredValue :
                        # compute successor state
                        fixpoint = False
                        nextState = list(currState)
                        if mc.get_unitary() :
                            nextState[pos] = self._toFavoredVal(currState[pos], favoredValue)
                        else :
                            nextState[pos] = favoredValue
                        
                        # add transition
                        self._stg.add_edge(self.state_to_str(currState), self.state_to_str(nextState))
                        
                        # update statesToVisit
                        if self._stg.out_degree(self.state_to_str(nextState)) in [{}, 0] and nextState not in statesToVisit :
                            statesToVisit.append(nextState)
                
                # currentState is a fixpoint 
                if fixpoint :
                    # add transition
                    self._stg.add_edge(self.state_to_str(currState), self.state_to_str(currState))
                    
                # update statesToVisit
                statesToVisit.remove(currState)
    
    def set_edges_async_rec(self, mc, parameterSet) :
        """
        DEPRACTED.
        Is faster than set_edges_async(), but reaches maximum recursion depth when there are too many transitions. 
        
        Add edges (and implicit the nodes also) recursiv to the self._STG (should be empty),
        beginning with the states given by initialStates (given by mc),
        following the rules given by the parameter set.
        The transitions are added asynchronous and unitary or non-unitary (given by mc).
        Possible previous nodes and edges from the STG are not deleted.
        
        Parameter:
        mc - the ModelContainer (containing varIndex, unitary, tresholds, ect.)
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
            for i in xrange(len(currState)) :
                if currState[i] != currFavoredState[i] :
                    nextState = list(currState)
                    if mc.get_unitary() :
                        nextState[i] = self._toFavoredVal(currState[i], currFavoredState[i])
                    else :
                        nextState[i] = currFavoredState[i]
                    nextStates.append((nextState, mc.varIndex(i)))
            return nextStates
        
        def _add_edges(currState, currFavoredState) :
            # update statesToVisit
            statesToVisit.remove(currState)
            
            # add transition(s)
            if currState == currFavoredState :
                self._stg.add_edge(self.state_to_str(currState), self.state_to_str(currState)) # fixpoint
            else :    
                for (nextState, changedVar) in _possibleNextStates(currState, currFavoredState) :
                    # add transition and update statesToVisit
                    self._add_edge(currState, nextState, self._stg, statesToVisit)
                    
                    # add following edges recursive
                    if nextState in statesToVisit :
                        _add_edges_rec(nextState, currFavoredState, changedVar)
        
        def _add_edges_rec(currState, oldFavoredState, currVar) :
            # build currFavoredState ('Bildzustand')
            currFavoredState = list(oldFavoredState)
            for succ in mc.successors(currVar) :
                activePreds = self._find_activePreds(mc, currState, succ)
                currFavoredState[mc.varIndex(succ)] = parameterSet[succ][activePreds]
            
            # add edges (and nodes) to STG
            _add_edges(currState, currFavoredState)

        
        # Add edges to the graph
        statesToVisit = list(mc.get_initialStates())
        while len(statesToVisit) > 0 :
            
            # current State
            currState = statesToVisit[0]
            
            # compute favored state ('Bildzustand')
            currFavoredState = []
            for i in xrange(len(currState)) :
                currVar = mc.varIndex(i)
                activePreds = self._find_activePreds(mc, currState, currVar)
                currFavoredState.append(parameterSet[currVar][activePreds])
            
            # add transition(s) from current state to successor(s)
            _add_edges(currState, currFavoredState)
    
    
    def set_edges_priCl(self, mc, parameterSet) :
        """
        Add edges (and implicit the nodes also) to the self._STG (should be empty),
        beginning with the states given by statesToVisit (given by mc),
        following the rules given by the parameter set.
        The transitions are added synchronous or asynchronous, 
        depending on the priority classes and unitary or non-unitary (given by mc).
        Possible previous nodes and edges from the STG are not deleted.
        
        Parameter:
        mc - the ModelContainer (containing varIndex, unitary, tresholds, ect.)
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
            highestPriority = 'infinity'
            for pos in xrange(len(currState)) :
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
                    nextState[pos] = self._toFavoredVal(currState[pos], currFavoredState[pos])
                else :
                    nextState[pos] = currFavoredState[pos]
                nextStates.append((nextState, mc.varIndex(pos)))
            return nextStates
        
        def _add_edges(currState, currFavoredState) :
            # update statesToVisit
            statesToVisit.remove(currState)
            
            # add transition(s)
            if currState == currFavoredState :
                self._stg.add_edge(self.state_to_str(currState), self.state_to_str(currState)) # fixpoint
            else :
                highestPriority, highPrioVarPos = _highPrioVarPos(currState, currFavoredState)
                # add edge synchronous
                if mc.priorityTyp(highestPriority) == 'synchronous' :
                    nextState = list(currState)
                    for pos in highPrioVarPos :
                        if mc.get_unitary() :
                            nextState[pos] = self._toFavoredVal(currState[pos], currFavoredState[pos])
                        else :
                            nextState[pos] = currFavoredState[pos]
                    self._add_edge(currState, nextState, self._stg, statesToVisit)
                # add edges asynchronous
                elif  mc.priorityTyp(highestPriority) == 'asynchronous' :
                    for (nextState, changedVar) in _possibleNextStates(currState, currFavoredState, highPrioVarPos) :
                        # add edge
                        self._add_edge(currState, nextState, self._stg, statesToVisit)
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
                activePreds = self._find_activePreds(mc, currState, succ)
                currFavoredState[mc.varIndex(succ)] = parameterSet[succ][activePreds]
            
            # add edges (and nodes) to STG
            _add_edges(currState, currFavoredState)
    
        
        # Add edges to the graph
        statesToVisit = list(mc.get_initialStates())
        while len(statesToVisit) > 0 :
            
            # current State
            currState = statesToVisit[0]
            
            # compute favored state ('Bildzustand')
            currFavoredState = []
            for i in xrange(len(currState)) :
                var = mc.varIndex(i)
                activePreds = self._find_activePreds(mc, currState, var)
                currFavoredState.append(parameterSet[var][activePreds])
            
            # add transition(s) from current state to successor(s)
            _add_edges(currState, currFavoredState)


    def stg(self) :
        """
        Get the STG (nx.DiGraph).
        """
        return self._stg
