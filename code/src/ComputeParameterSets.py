# -*- coding: utf-8 -*-
import imp, os
LPS = imp.load_source("LPS", os.path.join("LocalParameterSet.py"))


def compute_local_constraint_ParameterSets(MC, var, EDGELABELS, values={}):
    '''
    For a given variable all possible ParameterSets compatible 
    to the edge labels are computed.
    This is done very efficiently with a backtracking algorithm.
    
    parameters:
      MC:	    is needed to access functions of ModelContainer
      var:	    varname (string)
      values:	    optional. dict of possible values for each context
                    e.g. values[('VA','VB','VC')] =  [ 0,1, 3,4 ]
                    if a context is not specified, the variable's whole 
                    range (0 .. varMax) is assumed.
                    
    *** for details on backtracking, see backtracking()
    *** for details on Flags, see reject()
    '''
    
    contexts = sorted(MC.contexts(var), key=len)
    results = []
    max_depth = len(contexts)
    
    def preContexts(depth):
        '''
        yields* a tuple of regulator and the context without this regulator 
        for each regulator in the current context (current tree depth)
        (* see python genrators for more information about yield)
        '''
        currentContext = contexts[depth]
        for reg in currentContext:
            context_without_reg = MC.contextId( [r for r in list(currentContext) if r != reg] )
            yield (reg, context_without_reg)

    def possibleValues(depth):
        '''
        possible K values can be specified for each context. If not specified,
        a standard range 0 .. varMax is assumed. If specified but 
        '''
        context = contexts[depth]
        if context in values:
            if values[context]:
                return values[context]
            else:
                MC.message("(MC) warning: empty list of possible values for " + var + " during compute_constraint_ParameterSets().\nTake 0.." + MC.varMax(var) + " instead!","error")
        return range(MC.varMax(var)+1)
    
    def accept(depth, localSet):
        '''
        if all contexts have been set, this method checks whether a localSet
        validates its edge labels. To perform this efficiently, flags have already
        been added on the way down the tree. This is done in reject().
        
        accept() finally checks whether the correct flags have been set regarding all
        regulators and edge labels of var.
        
        returns True if all regulations (and so the localSet) are validated, otherwise False.
        '''
        if depth != max_depth:
            # not all contexts have been set.
            return False
            
        for (reg, x) in preContexts(max_depth-1):            
            # ALL regulations must be validated, so don't return True too early!
            edgeLabel = MC.edgeLabel((reg, var))
            
            assert(edgeLabel in EDGELABELS)
            
            if   edgeLabel == "+"    and not localSet.get_flag(reg,"inc"): return False
            elif edgeLabel == "obs+" and not localSet.get_flag(reg,"inc"): return False
            elif edgeLabel == "-"    and not localSet.get_flag(reg,"dec"): return False
            elif edgeLabel == "obs-" and not localSet.get_flag(reg,"dec"): return False
            elif edgeLabel == "+-"   and (not localSet.get_flag(reg,"dec") or not localSet.get_flag(reg,"inc")): return False
            elif edgeLabel == "obs"  and not localSet.get_flag(reg,"dec") and not localSet.get_flag(reg,"inc"): return False
            # all other edgeLabels don't require a validation, so:
        return True

    def reject(depth, localSet):
        '''
        During backtracking, for each new context reject() is called.
        It returns False if at least one regulation hurts consistency. 
        Flags for validation are also set in here.

        *** A few words on FLAGS:
        In each level of the computation tree a new context is given a k value.
        At this point (to be exact: at the beginning of the next call of backtracking)
        flags are set to gather information on the values that have been set.
        Typical flags are whether a regulation decreases (dec) or increases (inc)
        the components value. But we could also think of other flags, like
        for example "value is above 3 with this regulation". No matter what kind of 
        edgeLabel we want to implement, here we can add a flag for it.
        Now these flags are used at two points.
        First of all, the reject() method itself uses them to check consistency.
        Consistency stands for a "for all" property which should, if once hurt, 
        stop further branching. So if a wrong flag has been set (or has not been set)
        in the current step, consistency is hurt and backtracking is stopped.
        A good example is if the "dec" flag has been set, although its an edge 
        labeled with "+". Then monotony has been hurt.
        In each level of computation these flags are reset, since consistency 
        must be proven again in the next step. But to keep some of this information,
        a flag that has once been set is also given to the LocalParameterSet.
        The class itself stores these flags - if once set they won't be removed again.
        This is helpful to check validation since validation requires 
        "exists"-properties.
        So in the end, if all contexts were given values, accept() simply checks
        whether all validation flags to the corresponding edge labels have been set!
        ***
        '''
        if depth == 0:
            # no contexts have been set, so don't reject
            return False
        else:
            depth = depth-1 # (just a technical detail: depth-1 is the latest edited context!)
            latest_context = contexts[depth]
            
            for (reg, con_without_reg) in preContexts(depth):
                edgeLabel = MC.edgeLabel((reg, var))
                
                assert(edgeLabel in EDGELABELS)
                
                flags = []
                # flags are set here:
                if localSet[latest_context] > localSet[con_without_reg]:
                    flags.append("inc")
                if localSet[latest_context] < localSet[con_without_reg]:
                    flags.append("dec")
                
                # check consistency:
                # return True right away if consistency is hurt AT LEAST ONCE
                if   edgeLabel == "+"    and "dec" in flags: return True
                elif edgeLabel == "-"    and "inc" in flags: return True
                elif edgeLabel == "mon+" and "dec" in flags: return True
                elif edgeLabel == "mon-" and "inc" in flags: return True
                elif edgeLabel == "mon"  and "inc" in flags and "dec" in flags: return True
                # all other edgeLabels don't require consistency

                for flag in flags:        
                # save flags for validation
                    localSet.set_flag(reg, flag)
        return False
        
    
    def backtracking(depth, localSet):
        '''
        Core part of backtracking algorithm. 
        There has been great effort to make this algorithm look like Wikipedia's pseudo code !!!
        
        > http://en.wikipedia.org/wiki/Backtracking
        
        For details on FLAGS, see reject()'s documentation.
        
        First of all reject() checks, whether consistency has been hurt in the step before 
        (one level above in the tree). If so, branching is stopped right away 				(BOUND)
        Then accept checks, whether the set is already finished AND fulfills all
        validation requirements. If so, the set is saved.
        If the set wasn't accepted although we reached bottom, computation is also stopped.
        (unfortunately this query didn't fit into the reject/accept schema. This is beacause
        reject first has to set flags of the last step before accept may decide whether to save
        the Set or not)
        Finally the recursion step genreates new sets for each new possibleValue and calls 
        backtracking() on those again.														(BRANCH)
        '''       
        if reject(depth, localSet):
            # has consistency been hurt in the last step? 
            # if so, stop branching here!
            return 
        if accept(depth, localSet):	
            # is this set valid? 
            # if so, save it!
            results.append(localSet)
            return
        if depth == max_depth:
            # finished computation, but set wasn't accepted.
            return
        for k in possibleValues(depth):
            # foreach possible value generate a new Set.
            new_localSet = localSet.copy()
            new_localSet[contexts[depth]] = k
            # go deeper
            backtracking(depth+1, new_localSet)

    ps = LPS.LocalParameterSet()
    backtracking(0, ps)  
    return results

def filter_localParameterSets(MC, varname, localSets, conditions):
        ''' Deletes the local sets of varname that do not satisfy selected conditions.
        Currently Conditions are "Min","Max","AllValues"'''
        # An dieser Stelle können neue Bedingungen als Funktionen hinzugefügt werden.
        def Min(localSet):
            if 0 in values:
                return True
            return False

        def Max(localSet):
            if MC.varMax(varname) in values:
                return True
            return False

        def AllValues(localSet):
            if len(set(values)) == MC.varMax(varname)+1:
                return True
            return False

        # chose conditions.
        functions = []
        for name in conditions:
            if name == "Min": functions.append(Min)
            elif name == "Max": functions.append(Max)
            elif name == "AllValues": functions.append(AllValues)

        # find bad sets.
        count = 0        
        toRemove = []
        for localSet in localSets:
            values = localSet.values()
            for f in functions:
                if not f(localSet):
                    toRemove.append(localSet)
                    count += 1
                    break
                
        # remove bad sets.
        for kill in toRemove:
            localSets.remove(kill)
        MC.message("lFi: Deleted %i local sets of %s." % (count, varname))


def compute_local_simplified_ParameterSets(MC, var, tRange=[]):
    '''
    simplified components work as majority switches:
    If at least X activating* regulators are effective, the component is 
    switched on (to its varMax value). Otherwise it's switched off (value 0).
    X reaches from 1 (=> OR switch on resources) to 
    [number of regulators] (=> AND switch on resources) and 
    for each threshold X a ParameterSet is generated.
    
    This allows modeling a component with only [number of regulators]
    ParameterSets, which can be useful to analyze large networks.

    Parameters:
        MC - ModelContainer
        var - string
        tRange - [int..] considered Resource thresholds, if [] all possibilities.
    
    *** activating regulators:
    (also called resources, as in SMBionet articles)
    An activating regulation is a "+" edge that is active (means: above 
    threshold) or a "-" edge that is inactive. So only "+" and "-" labels 
    are allowed. This constraint is needed to interpret each edge either 
    as an activating or an inhibiting regulation.

    *** Note that while the number of sets is decreased enormously 
    (which means to a number linear in the number of regulators),
    strong simplifications have been done on the model, which might no longer 
    be compatible with a biological point of view. (here's an example: since a 
    component now works as a switch, it can only turn on all its outgoing
    regulations at once. Different thresholds on its outgoing edges are ignored)
    '''
    regulators = MC.predecessors(var)
    contexts_as_resources = {}  #  resource => realContext
    
    # translate contexts to resources:
    for con in MC.contexts(var):
        resources = []
        for reg in regulators:
            if   MC.edgeLabel((reg, var)) == "+" and reg in con:
                resources.append(reg)
            elif MC.edgeLabel((reg, var)) == "-" and reg not in con:
                resources.append(reg)
            elif MC.edgeLabel((reg, var)) not in ["+","-"]:
                MC.message("Fatal Error: only \"+\" and \"-\" edges allowed in simplified components. (" + var + ")","error")
        contexts_as_resources[MC.contextId(resources)] = con
    
    # if tRange==[], consider all thresolds.
    if not tRange:
        tRange = range(1,len(regulators)+1)

    results = []    
    for threshold in tRange: 
        # majority threshold from 0 (= all contexts take varMax) 
        # to [number of regulators] + 1 (all contexts take 0)
        lps = LPS.LocalParameterSet()
        for resource in contexts_as_resources:
            if len(resource) >= threshold:
                lps[contexts_as_resources[resource]] = MC.varMax(var)
            else:
                lps[contexts_as_resources[resource]] = 0
        results.append(lps)    
    return results


def compute_local_boolean_ParameterSets(MC, var, formula):
    '''Computes the unique parameter set described by formula.
    parameters:
        formula - boolean expression in Python syntax ['and','or','not','any','all']
    returns:
        [lps] - LocalParameterSet in list

    Pseudo code:
        for context of var:
            for regulator of var:
                if regulator in context:
                    add local variable with name regulators and value True
                else
                    add local variable with name regulators and value False

            lps[context] <- evaluate formula'''
    regulators = MC.predecessors(var)
    lps = LPS.LocalParameterSet()
    for con in MC.contexts(var):
        for reg in regulators:
            if reg in con:
                vars()[reg]=True
            else:
                vars()[reg]=False

        try:
            value = int(eval(formula))
        except:
            MC.message("CPS: cannot evalute %s in context %s for %s."%(formula,str(con),var),"error")
            return []
        
        lps[con] = value

    return [lps]
