# -*- coding: utf-8 -*-
#===============================================================================
#  
#===============================================================================

# TODO: Alle Methoden testen.
# TODO: isFrozen(), maxValue()t, minValue(), robustness() funktionieren nur, wenn len(attr) != 0; states() may show unexpected behaviour.

class AttrInfo() :
    def __init__(self, mc, id, attr) :
        self._mc = mc
        self._id = id
        self._attr = attr
        if len(attr) == 0 :
            mc.message("Warning: Try to build AttrInfo(mc, id, attr), but attr is empty.")

    def __repr__(self):
        string = "Size: %i\n" % self.size()
        for var in self._mc.varnames():
            string += "%s min: %i max %i\n" % (var,self.minValue(var),self.maxValue(var))
        string += "Robustness: -"
        return string
        
    def isFrozen(self, var) :
        """
        Checks if var does not change its value (in all states of the attractor).
        """
        pos = self._mc.varIndex(var)
        val = self._attr[0][pos]
        for state in self._attr[1:] :
            if state[pos] != val :
                return False 
        return True
    
    def maxValue(self, var) :
        """
        Returns the maximum value of var (of all states of the attractor).
        """
        pos = self._mc.varIndex(var)
        maxVal = int(self._attr[0][pos])
        for state in self._attr[1:] :
            if int(state[pos]) > maxVal :
                maxVal = int(state[pos]) 
        return maxVal
    
    def minValue(self, var) :
        """
        Returns the minimum value of var (of all states of the attractor).
        """
        pos = self._mc.varIndex(var)
        minVal = int(self._attr[0][pos])
        for state in self._attr[1:] :
            if int(state[pos]) < minVal :
                minVal = int(state[pos]) 
        return minVal

    def size(self) :
        """
        Returns the number of states in the attractor.
        """
        return len(self._attr)
    
    def states(self, rule) :
        """
        Returns True if all states of the attractor follow the rule,
        otherwise False.
        
        Parameter:
        rule: String of the same size as the states. A number (0-9)
              at position i indicates that all states should have
              these value at position i also.
              For wildcards just use other chars, e.g. '_' or '*'.  
              Valid rules are e.g. '__0_10' or '***' (if the rule
              length match with the length of the states).
        
        Pseudocode:
        // Preprocessing:
        indices <- all positions where rule[position] is a number (int)
        
        // Run:
        for all states in attractor :
            for pos in indices :
                if state[pos] != rule[pos] :
                    return False
        return True
        """
        
        def _isInt(i) :
            try :
                int(i)
                return True
            except :
                return False
        
        # Preprocessing (extract necessary indices)
        indices = []
        for pos, var in enumerate(rule) :
            if _isInt(var) : indices.append(pos)

        # Run (check if all states follow the rule) 
        for state in self._attr :
            for pos in indices :
                if state[pos] != rule[pos] :
                    return False
        return True

    def robustness(self, destiny) : #TODO implement destiny
        '''destiny: das dictionary state: erreichbare Attraktoren.'''
        
        def _modState(state) :
            modStates = []
            for pos in range(len(state)) :
                modStates.append(state[0:pos] + str(int(state[pos]) + 1) + state[pos+1:])
                modStates.append(state[0:pos] + str(int(state[pos]) - 1) + state[pos+1:])
            return modStates
        
        back2self = 0.0
        All = 0.0 # geändert, weil "all" von python belegt ist.
        for state in self._attr :
            for modState in _modState(state) :
                if modState in destiny :
                    All += 1
                    if destiny[modState] == [self._id] :
                        back2self += 1
        return back2self/All
