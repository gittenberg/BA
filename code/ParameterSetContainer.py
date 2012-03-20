# -*- coding: utf-8 -*-
import itertools as IT
import networkx as nx #@UnresolvedImport
import time, sys
import math
import copy

class ParameterSetContainer():
    def __init__(self, localSets, mc=None):
        self._MC = mc # this is only used for messaging - no dependency this way it seems
        
        #used and changed by parameterset management functions (reject etc.):
        self._localParameterSets = localSets
        self._rejectIndices = True # decides whether indices are accepted or rejected parameterSets
        self._filteredParametersIndexList = list() # indices of rejected or accepted parameter sets, depending on attribute rejectIndices
        self._maxParameterSets = 0 #quantity of all possible parameterSets
        
        #filled by analyze_functions:
        self._parameterValues = dict()    
        self._conflictsGraph = nx.Graph()
        self._parameterValuesCounts = dict() 
        self._parameterValuesStats = dict()
        self._contextOrderings = dict()
        self._localParameterSetsTranslator = dict()
        self._filteredLocalParametersIndexList = dict() # indices of local parameter sets (sorted by varname) that are still in the pool

        #attributes to support some functions:
        self._recentlyChanged = True #if True: container hasn't been recently analyzed -> analyze attributes are out of date
                                     #if False: attributes have already been updated using the newest parameter sets (gained by most recent filtering)
        self._checked = False        
        
        #calculate maxParameterSets:
        count = 1
        for var in self._localParameterSets:
            count *= len(self._localParameterSets[var])
        self._maxParameterSets = count #quantity of all possible parameterSets

    def __len__(self):
        size = self.size()
        if size>sys.maxint:
            self.message("PSC: length() can only return integers, size of PSC is long int. Use PSC.size().","error")
            return None
        return size

    def __nonzero__(self):
        '''For calling 'if not psc'.'''
        return self.size()>0

    def size(self):
        '''Returns number of acceptable parameter sets. May be of type long int.'''
        if self._rejectIndices:
            return self._maxParameterSets - len(self._filteredParametersIndexList)
        else:
            return len(self._filteredParametersIndexList)

    def message(self, string, category="debug"):
        mc = self._MC
        if mc:
            mc.message(string, category)
        else:
            print string

    def invert_filteredParametersIndexList(self):
        '''
        Inverts the filteredParamtersIndexList in place and inverts the flag.
        Therefore it iterates through filteredParametersIndexList, considers two neighboured indices and extends the new Index List by
        all indices between the neighbours.
        '''

        if not self._filteredParametersIndexList:
            new_indexList = range(self._maxParameterSets)
        else:
            new_indexList = []
            new_indexList.extend(range(self._filteredParametersIndexList[0]))
            while len(self._filteredParametersIndexList)>1:
                last_index = self._filteredParametersIndexList.pop(0)
                new_indexList.extend(range(last_index+1,self._filteredParametersIndexList[0]))
            new_indexList.extend(range(self._filteredParametersIndexList.pop(0)+1,self._maxParameterSets))
        self._filteredParametersIndexList = new_indexList
        self._rejectIndices = not self._rejectIndices

    
    def parameterSetGenerator(self):
        '''Yields the next valid parameter set constructed as a product of local sets.'''
        localSets = self._localParameterSets

        varLists = []
        for varname in localSets:
            setList = []
            for localSet in localSets[varname]:
                setList.append((varname, localSet))
            varLists.append(setList)
        varProduct = IT.product(*varLists)

        # used to be done by keepTrueSets():
        if not self._checked:
            self._checked = True

        for items in varProduct:
            parameterSet = dict(items)
            yield parameterSet

    
    def get_parameterSets(self):
        '''return generator object which includes all filtered parametersets'''       
        
        # In Reject-Mode: Return parSets that are not in indices.
        if self._rejectIndices : 
            if self._filteredParametersIndexList:
                current = 0    
                for (j, parSet) in enumerate(self.parameterSetGenerator()):
                    if current >= len(self._filteredParametersIndexList):
                        yield parSet
                    elif j == self._filteredParametersIndexList[current]:
                        current += 1
                    else:
                        yield parSet
            else:
                for parSet in self.parameterSetGenerator():
                    yield parSet


        # In Accept-Mode: Returns parSets that are in indices.
        else:  
            current = 0    
            for (j, parSet) in enumerate(self.parameterSetGenerator()):
                if current >= len(self._filteredParametersIndexList):
                    break 
                if j == self._filteredParametersIndexList[current]:
                    current +=1
                    yield parSet


    def reject(self, indexList):
        '''mark items from indexList as rejected indices by either including them in or excluding them from self._filteredParametersIndexList, depending on ._rejectIndices;
           also switch self._rejectIndices if the length of filteredParametersIndexList is bigger than half of the length of the list of all possible parameter sets and then
           invert filteredParametersIndexList'''        

        # translate indices from indexList to fit the real/complete list of parameterSets:
        if self._rejectIndices:
            self.invert_filteredParametersIndexList()
    
        realRejectedIndices = list()
        while indexList:
            realRejectedIndices.append(self._filteredParametersIndexList[indexList.pop()])
    
        realRejectedIndices.reverse()
        if self._rejectIndices:
            self.invert_filteredParametersIndexList()
        
                # OLD REJECT:       BAD :(
        #   Der folgende ist der Schritt der ewig dauert! 
        #   Ein Beispiel:
        #   Reject 944.960 von 944.960 sets dauerte 86 minuten!
        #			Das Filtern dieser 944.960 Sets nur etwa 5 minuten!
        #   mögliche Ursache: Quadratische Laufzeit durch remove?
        ##for realRejectedIndex in realRejectedIndices:
        ##   self._filteredParametersIndexList.remove(realRejectedIndex)
        #
        # NEW REJECT:
        #   Note that both lists, realRejectedIndices and _filteredParameterList
        #   are ordered ascending!
        #   Task: Kick those entries out of _filteredParameterList,
        #   that are found in realRejectedIndices!
        pos_in_rejectList = 0
        resulting_filteredList = []
        for pos in range(len(self._filteredParametersIndexList)):
            if      pos_in_rejectList >= len(realRejectedIndices) \
            or   realRejectedIndices[pos_in_rejectList] != self._filteredParametersIndexList[pos]:
                resulting_filteredList.append(self._filteredParametersIndexList[pos])                    
            else:
                pos_in_rejectList+=1
        self._filteredParametersIndexList = resulting_filteredList
        
        # check whether self._rejectIndices needs to be switched and invert self._filteredParametersIndexList if necessary:
        if len(self._filteredParametersIndexList) > 0.5*self._maxParameterSets:
            self.invert_filteredParametersIndexList()
        self._recentlyChanged = True

    def analyze_all(self, progressBar = None):
        '''Computes class attributes parameterValues, localParameterSets, contextOrderings, localParameterSetsTranslator
        and parameterValuesCounts in a faster way than using the local analyze_ functions (analyze_parameterValues,analyze_valueOrders,..)
        would.
        
        Using the optional argument "progressBar", a QProgressBar object can be passed which gets updated depending on the calculation progress.'''
        
        if self._recentlyChanged:
        
            self.message("(PSC) Starting complete analysis..")
            
            #initialization step:
            parameterValues = dict([(key,dict([(context,set()) for context in self._localParameterSets[key][0]])) for key in self._localParameterSets])
            parameterValuesCounts = dict([(key,dict([(context,dict()) for context in self._localParameterSets[key][0]])) for key in self._localParameterSets])
            parameterOrders = dict([(key,dict()) for key in self._localParameterSets])
            localParameterSets = dict([(key,list()) for key in self._localParameterSets])
            localParameterSetsTranslator = dict([(key,dict()) for key in self._localParameterSets])
            
            #dictionary of the form {varname: number}, keeps track of the number that needs to be attached 
            #to the name of the next local parameter set that belongs to varname:
            transValues = dict([(key,0) for key in self._localParameterSets])
            
            #keeps track of the number of already analyzed local parameter sets:
            locSetCount = 0
            
            
            #calculate the number of current local parameter sets:
            
            #if there has been a model check:
            if self._filteredLocalParametersIndexList != {}:
                maxSets = sum([len(self._filteredLocalParametersIndexList[varname]) for varname in self._localParameterSets])
            #otherwise use all local parameter sets:
            else:
                maxSets = sum([len(self._localParameterSets[varname]) for varname in self._localParameterSets])
                
            #used for updating the progress bar:
            
            #number of all parameter sets and sets already analyzed:
            numberParaSets = len(self)
            numberSetsDone = 0
            
            #how many percent of parameter sets have been analyzed and whats
            #the size of the steps in which the progress bar is updated:
            progressPercent = 0
            percentSteps = 1
     
            start = time.time()
            
            for parameterSet in self.get_parameterSets():
                 for varname in parameterSet:
    
                    #if all filtered local parameter sets have been found at least once just increase parameterValuesCounts for the last sets:
                    if locSetCount >= maxSets:                        
                        for context in parameterSet[varname]:
                            parameterValuesCounts[varname][context][parameterSet[varname][context]] += 1
                    
                    #else, if there is a chance of finding a new local parameter set:
                    else:
                        
                        #get index of the current local parameter set and check whether it has been found before:
                        locParSetIndex = self._localParameterSets[varname].index(parameterSet[varname])
                        if locParSetIndex in localParameterSets[varname]:
                            #if so, just increase the parameterValuesCounts of its contexts:
                            for context in parameterSet[varname]:
                                parameterValuesCounts[varname][context][parameterSet[varname][context]] += 1
                        
                        #else, if a new local parameter set has been found:      
                        else:
                            
                            #add its index to the known local parameter sets:
                            localParameterSets[varname].append(locParSetIndex)
                            locSetCount += 1
                            #generate a new entry in the translator:
                            transValues[varname] += 1
                            #print "translator:",self._localParameterSetsTranslator
                            localParameterSetsTranslator[varname][varname+"_"+str(transValues[varname])] = parameterSet[varname]
    
                            for context in parameterSet[varname]:
                                
                                #increase parameterValuesCounts of the new sets contexts and extend parameterValues if necessary:
                                if parameterSet[varname][context] in parameterValuesCounts[varname][context].keys():
                                    parameterValuesCounts[varname][context][parameterSet[varname][context]] += 1
                                else:
                                    parameterValuesCounts[varname][context][parameterSet[varname][context]] = 1
                                    parameterValues[varname][context].add(parameterSet[varname][context])                           
                 
                 #increase progress bar based on percentSteps:
                 if progressBar:
                     numberSetsDone += 1
                     if numberSetsDone >= numberParaSets*((progressPercent+percentSteps)/float(100)):
                         progressPercent += percentSteps
                         progressBar.setValue(progressPercent*0.5)
                         
            afterLoop = time.time()
            #print "(PSC) analyze main loop finished in %.0fs." % (afterLoop-start)
            self.message("(PSC) analyze main loop finished in "+str(math.floor(afterLoop-start))+"s","debug")
            
            #calculate percentages of parameterValues:
            parameterValuesStats = copy.deepcopy(parameterValuesCounts)
            
            for varname in parameterValuesCounts:
                for context in parameterValuesCounts[varname]:
                    
                    #sum of the counts of all possible values of the context:
                    countSum = sum(parameterValuesCounts[varname][context].values())
                    
                    for value in parameterValuesCounts[varname][context]:
                        parameterValuesStats[varname][context][value] = parameterValuesCounts[varname][context][value]/math.floor(countSum)
            
            self.message("parameterValuesStats:")
            for varname in parameterValuesStats:
                self.message(varname+":")
                for context in parameterValuesStats[varname]:
                    self.message("\t"+str(context))
                    for value in parameterValuesStats[varname][context]:
                        self.message("\t\t"+str(value)+" "+str(parameterValuesStats[varname][context][value]))
                    
                
            #set class attributes to new results
            
            #parameterValues needs to be set first in order to calculate orderings:
            self._parameterValues = parameterValues
            self.message("(PSC) building orderings..")
            for varname in self._localParameterSets.keys():
                parameterOrders[varname] = self.analyze_valueOrders(varname)
            self.message("(PSC) orderings finished.")
            
            #set remaining attributes:
            self._filteredLocalParametersIndexList = localParameterSets
            self._contextOrderings = parameterOrders
            self._parameterValuesCounts = parameterValuesCounts
            self._localParameterSetsTranslator = localParameterSetsTranslator
            self._parameterValuesStats = parameterValuesStats
            end = time.time()
            if progressBar:
                progressBar.setValue(100*0.5)
            #mark current parameter sets as completely analyzed:
            self._recentlyChanged = False
            #print "\n(PSC) Finished complete analysis in %.0fs." % (end-start)
            self.message("\n(PSC) Finished complete analysis in "+str(math.floor(end-start))+"s","debug")

                       
    def translateLocalParameterSets(self, locParaSetTuples):
        '''translates a list of tuples with structure (varname, local parameter set) into identifying strings for the given parameter sets by using self._localParameterSetsTranslator'''
        if type(locParaSetTuples) != list:
            locParaSetTuples = [locParaSetTuples]
        
        result = []
        #print "tuples:",locParaSetTuples
        for tuple in locParaSetTuples:
            for index in self._localParameterSetsTranslator[tuple[0]]:
                if self._localParameterSetsTranslator[tuple[0]][index]==tuple[1]:
                    result.append(index)
        if len(result)>1 or result==[]:
            return result
        else:
            return result[0]


    def analyze_parameterValues(self): 
        ''' Returns a dictionary of the form {varname : {context : set(parameterValues)}} '''
        parameterValues = {}
        for parameterSet in self.get_parameterSets():
            for varname in parameterSet:
                parameterValues[varname] = dict()
                for context in parameterSet[varname]:
                    parameterValues[varname][context] = set()

        # Fill structure
        for parameterSet in self.get_parameterSets():
            for key in parameterSet:
                for context in parameterSet[key]:
                    parameterValues[key][context].add(parameterSet[key][context])
                    
        ##Uncomment the following for verbose function
        #for key in self.varnames():
        #    for context in self.contexts(key):
        #        print "key, context, setOfValues = ", key, ",", context, ",", parameterValues[key][context]
        return parameterValues
    
    def analyze_valueOrders(self, varname):
        ''' Returns a dictionary of the form {(context, context): order} where order in ['=', '<', '<=', '>', '>=', '<>']'''
        if self._parameterValues.has_key(varname):

            localParameterSets = self.analyze_localParameterSets(varname)

            # replace previous line by following and rename below localParameterValues -> parameterValues[varname] to obtain old version:
            #parameterValues = self.analyze_parameterValues()
            parameterOrders = {}
            allContexts = list(self._parameterValues[varname].keys())

            # if varname has no predecessors:
            if len(allContexts) == 1:
                return dict()

            # if varname has at least one predecessor:
            else:
                unseenContexts = list(self._parameterValues[varname].keys())
                for context1 in allContexts:
                    unseenContexts.remove(context1)
                    for context2 in unseenContexts: # in order to halve calculation time
                        alwaysEqualTo = True
                        alwaysLessThan = True
                        alwaysGreaterThan = True
                        everLessThan = False
                        everGreaterThan = False
                        for localSet in localParameterSets:
                            if localSet[context1] == localSet[context2]:
                                alwaysLessThan = False
                                alwaysGreaterThan = False
                            if localSet[context1] < localSet[context2]:
                                alwaysEqualTo = False
                                everLessThan = True
                                alwaysGreaterThan = False
                            if localSet[context1] > localSet[context2]:
                                alwaysEqualTo = False
                                everGreaterThan = True
                                alwaysLessThan = False
                        if alwaysEqualTo:
                            parameterOrders[tuple((context1, context2))] = "="
                            parameterOrders[tuple((context2, context1))] = "="
                        elif alwaysGreaterThan:
                            parameterOrders[tuple((context1, context2))] = ">"
                            parameterOrders[tuple((context2, context1))] = "<"
                        elif alwaysLessThan:
                            parameterOrders[tuple((context1, context2))] = "<"
                            parameterOrders[tuple((context2, context1))] = ">"
                        elif not everLessThan:
                            parameterOrders[tuple((context1, context2))] = ">="
                            parameterOrders[tuple((context2, context1))] = "<="
                        elif not everGreaterThan:
                            parameterOrders[tuple((context1, context2))] = "<="
                            parameterOrders[tuple((context2, context1))] = ">="
                        else:
                            parameterOrders[tuple((context1, context2))] = "<>"
                            parameterOrders[tuple((context2, context1))] = "<>"
                return parameterOrders
        else:
            print "(Analyze value orders) Warning:", varname, "has no valid parameters, returning empty dict."
            return dict()

    def analyze_valueOrders_OLD_INTERPRETATION(self, varname):
        ''' Returns a dictionary of the form {(context, context): order} where order in ['=', '<', '<=', '>', '>='] '-' has been omitted from this version'''
        if self._parameterValues.has_key(varname):

            localParameterSets = self.analyze_localParameterSets(varname)
            localParameterValues = self._parameterValues[varname] 

            # replace previous line by following and rename below localParameterValues -> parameterValues[varname] to obtain old version:
            #parameterValues = self.analyze_parameterValues()
            parameterOrders = {}
            allContexts = list(self._parameterValues[varname].keys())
            # if varname has no predecessors:
            if len(allContexts) == 1:
                return dict()
            # if varname has at least one predecessor:
            else:
                #print "localParameterValues =", localParameterValues
                #print 'localParameterSets =', localParameterSets
                unseenContexts = list(self._parameterValues[varname].keys())
                for context1 in allContexts:
                    unseenContexts.remove(context1)
                    #print unseenContexts
                    for context2 in unseenContexts: # in order to halve calculation time
                        # check whether order relation is correctly implemented
                        # '=' only if sets are equal
                        equalParametersForAllLocalSets = True
                        for localSet in localParameterSets:
                            if localSet[context1] != localSet[context2]:
                                equalParametersForAllLocalSets = False
                        if equalParametersForAllLocalSets:
                            parameterOrders[tuple((context1, context2))] = "="
                            parameterOrders[tuple((context2, context1))] = "="
                        elif max(localParameterValues[context1]) <= min(localParameterValues[context2]):
                            parameterOrders[tuple((context1, context2))] = "<="
                            parameterOrders[tuple((context2, context1))] = ">="
                            # only if inequality is strict, overwrite order
                            if max(localParameterValues[context1]) < min(localParameterValues[context2]):
                                parameterOrders[tuple((context1, context2))] = "<"
                                parameterOrders[tuple((context2, context1))] = ">"
                        elif min(localParameterValues[context1]) >= max(localParameterValues[context2]):
                            parameterOrders[tuple((context1, context2))] = ">="
                            parameterOrders[tuple((context2, context1))] = "<="
                            # only if inequality is strict, overwrite order
                            if min(localParameterValues[context1]) > max(localParameterValues[context2]):
                                parameterOrders[tuple((context1, context2))] = ">"
                                parameterOrders[tuple((context2, context1))] = "<"
                        else: # still required?
                            parameterOrders[tuple((context1, context2))] = "<>"
                            parameterOrders[tuple((context2, context1))] = "<>"
                return parameterOrders
        else:
            print "(Analyze value orders) Warning:", varname, "has no valid parameters, returning empty dict."
            return dict()

    def analyze_parameterValuesCounts(self, varname, context, value):
        ''' Counts parameterSets in which parameterSet[varname][context] == value '''
        count = 0
        for parameterSet in self.get_parameterSets():
            if parameterSet[varname][context] == value:
                count += 1
        return count

    def analyze_localParameterSets(self, varname):
        ''' Returns [{context:parameterValue}] containing all context:parameterValues ('Schaltung') belonging to varname '''
        locParaSets = []
        for parameterSet in self.get_parameterSets():
            if parameterSet[varname] not in locParaSets:
                locParaSets.append(parameterSet[varname])
        return locParaSets

    def analyze_countLocalParameterSets(self, varname, localParameterSet):
        ''' Counts parameterSets in which parameterSet[varname] == localParameterSet '''
        count = 0
        for parameterSet in self.get_parameterSets():
            if parameterSet[varname] == localParameterSet:
                count += 1
        return count
    
    def analyze_strictestEdgeLabels(self, (predecessor, varname)): 
        '''To be used after model checking: checks whether filtered _parameterSets
        allow for stricter definition of edgeLabels from predecessor to varname.
        Labels: +, -, +-, obs+, obs-, free, not-, not+. (obs is never reached.)
        Pseudo code:
        for every wiring:
            for every context of varname:
                extend context by predecessor
                compare parameters in context and extended context
                remember whether there was a strictIncrease
                remember whether there was a strictDecrease
                remember whether the run of alwaysIncreases was broken
                remember whether the run of alwaysDecreases was broken
        assign new edgeLabels based on what has been remembered
        '''
        constant = True
        plus = True
        minus = True
        plusminus = True
        monplus = True
        monminus = True
        obs = True
        plusobs = True
        minusobs = True
        notplus = True
        notminus = True
        
        for wiring in self.analyze_localParameterSets(varname):
            alwaysIncreasing = True
            alwaysDecreasing = True
            everStrictlyIncreasing = False
            everStrictlyDecreasing = False
            for context in wiring:
                contextList = list(context)
                contextList.append(predecessor)
                extendedContext = tuple(sorted(set(contextList))) # set to uniquefy, sorted to make comparable, tuple so we have the right type
                if wiring[context] == wiring[extendedContext]: 
                    continue
                elif wiring[context] < wiring[extendedContext]:
                    everStrictlyIncreasing = True
                    alwaysDecreasing = False
                elif wiring[context] > wiring[extendedContext]:
                    everStrictlyDecreasing = True
                    alwaysIncreasing = False

            constant = constant and (not everStrictlyIncreasing and not everStrictlyDecreasing)
            plus = plus and (alwaysIncreasing and everStrictlyIncreasing)
            minus = minus and (alwaysDecreasing and everStrictlyDecreasing)
            plusminus = plusminus and (everStrictlyIncreasing and everStrictlyDecreasing)
            monplus = monplus and not (everStrictlyDecreasing)
            monminus = monminus and not (everStrictlyIncreasing)
            plusobs = plusobs and (everStrictlyIncreasing)
            minusobs = minusobs and (everStrictlyDecreasing)
            obs = obs and (everStrictlyIncreasing or everStrictlyDecreasing)
            notplus = notplus and (not (alwaysIncreasing and everStrictlyIncreasing))
            notminus = notminus and (not (alwaysDecreasing and everStrictlyDecreasing))
            
        if constant:
            strictestLabel = '=' # this means it is constant
        elif plus:
            strictestLabel = '+'
        elif minus:
            strictestLabel = '-'
        elif plusminus:
            strictestLabel = '+-'
        elif monplus:
            strictestLabel = 'mon+'
        elif monminus:
            strictestLabel = 'mon-'
        elif plusobs:
            strictestLabel = 'obs+'
        elif minusobs:
            strictestLabel = 'obs-'
        elif obs:
            strictestLabel = 'obs'
        elif notplus:
            strictestLabel = 'not+'
        elif notminus:
            strictestLabel = 'not-'
        else:
            strictestLabel = 'free' #self.edgeLabel((predecessor, varname))
        return strictestLabel

    def analyze_strictestEdgeLabelsAll(self, edges):
        ''' To be used after model checking: returns a {edge:edgeLabels} with strictest edgeLabels consistent with _parameterSets '''
        strictestEdgeLabels = {}
        for edge in edges:
            strictestEdgeLabels[edge] = self.analyze_strictestEdgeLabels(edge)
        return strictestEdgeLabels
    
          
    def get_conflictsGraph(self, progressBar = None):
        '''Saves the conflicts between local sets as a gml graph.'''
        if progressBar:
            progressBar.setValue(0)
        start = time.time()
        if self._recentlyChanged:
            self.message("conflicts graph: building Translator..")
            transValues = dict()
            for parameterSet in self.get_parameterSets():
                for varname in parameterSet:
                        if varname not in self._localParameterSetsTranslator.keys():
                            self._localParameterSetsTranslator[varname] = dict()
                            transValues[varname] = 1
                            self._localParameterSetsTranslator[varname][varname+"_"+str(transValues[varname])] = parameterSet[varname]    
                    
                        elif parameterSet[varname] not in self._localParameterSetsTranslator[varname].values():                    
                            transValues[varname] += 1
                            self._localParameterSetsTranslator[varname][varname+"_"+str(transValues[varname])] = parameterSet[varname]
            self.message("conflicts graph: Translator built.")
            step = time.time()
            #print "Time passed: %.0fs." % (step-start)
            self.message("Time passed: "+str(math.floor(step-start))+"s","debug")

        if progressBar:
            progressBar.setValue(20)
        self.message("conflicts graph: building compatible..")
        compatible = nx.Graph()
        for parameterSet in self.get_parameterSets():
            #indices = [index for index in self._localParameterSetsTranslator[varname].keys() for varname in self._localParameterSetsTranslator.keys()]
            
            locParSets = [(varname,parameterSet[varname]) for varname in parameterSet]
            indices = sorted(self.translateLocalParameterSets(locParSets),reverse = True)                
            
            while indices:
                source = indices.pop()
                for target in indices[::-1]:
                    compatible.add_edge(source, target)
        self.message("conflicts graph: compatible built.")

        step = time.time()
        self.message("Time passed: "+str(math.floor(step-start))+"s","debug")
        if progressBar:
            progressBar.setValue(50)
        #print compatible.edges()
        self.message("conflicts graph: starting complement step..")  
        conflicts = nx.complement(compatible)
        if progressBar:
            progressBar.setValue(75)
        self.message("conflicts graph: complement created.")
        step = time.time()
        self.message("Time passed: "+str(math.floor(step-start))+"s","debug")
        
        self.message("conflicts graph: removing redundant edges..")
        
        # Überflüssige Kanten entfernen.
        for edge in conflicts.edges():
            source = edge[0]
            target = edge[1]
            sourceSplit = source.split("_")
            sourceName = "_".join(sourceSplit[:len(sourceSplit)-1])
            targetSplit = target.split("_")
            targetName = "_".join(targetSplit[:len(targetSplit)-1])            

            if sourceName == targetName:
                conflicts.remove_edge(source, target)
        self.message("conflicts graph: redundant edges removed.")
        step = time.time()
        self.message("Time passed: "+str(math.floor(step-start))+"s","debug")
        if progressBar:
            progressBar.setValue(100*0.5)
        self._conflictsGraph = conflicts
            
        # Layout und speichern.
        '''#bugt bei mir grad noch rum, findet bestimmte Methode nicht:
        layout = nx.circular_layout(self._conflictsGraph, scale = 100)
        graphics = dict([(node, {"x":layout[node][0],"y":layout[node][1]}) for node in layout])
        nx.set_node_attributes(self._conflictsGraph, "graphics", graphics)
        nx.write_gml(self._conflictsGraph, filename)
        self.message("wrote "+filename)
        '''
        return self._conflictsGraph         

    def get_parameterValues(self):
        return self._parameterValues
    
    def get_localParameterSets(self):
        
        localParameterSets = dict()

        for varname in self._filteredLocalParametersIndexList:
            localParameterSets[varname] = list()
            for index in self._filteredLocalParametersIndexList[varname]:
                localParameterSets[varname].append(self._localParameterSets[varname][index])
        '''
        for varname in self._localParameterSetsTranslator:
            localParameterSets[varname] = list()
            for index in self._localParameterSetsTranslator[varname]:
                localParameterSets[varname].append(self._localParameterSetsTranslator[varname][index])
        '''
        return localParameterSets
    
    def get_contextOrderings(self):
        return self._contextOrderings
    
    def get_parameterValuesCounts(self):
        return self._parameterValuesCounts
