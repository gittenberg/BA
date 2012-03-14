# -*- coding: utf-8 -*-
import imp
import os
import itertools as IT

STGC = imp.load_source("STGC", os.path.join("commonStg.py"))
STGG = imp.load_source("STGG", os.path.join("STGgenerator.py"))
LFG = imp.load_source("LFG", os.path.join("LanguageFileGenerator.py"))
PSC = imp.load_source("PSC", os.path.join("ParameterSetContainer.py"))
TS = imp.load_source("TS", os.path.join("TransitionSystem.py"))
CPS = imp.load_source("CPS", os.path.join("ComputeParameterSets.py"))
#LPS = imp.load_source("LPS", os.path.join("LocalParameterSet.py")) #TODO: experimentally commented out
AL = imp.load_source("AL", os.path.join("attractor_logic.py"))
TS = imp.load_source("TS", os.path.join("TransitionSystem.py"))
IGC = imp.load_source("IGC", os.path.join("inGraphChecker.py"))
ConP = imp.load_source("MP", os.path.join("ContextPreprocessor.py"))

import subprocess as SP
import networkx as nx #@UnresolvedImport
import itertools as IT
import sys
import time

class ModelContainer():
    def __init__(self, MainWindow=None):
        self._MainWindow = MainWindow
        self._print = True
        self._IG = None
        self._thresholds = dict()
        self._edgeLabels = dict()
        self._valueConstraints=dict() # über set_valueConstraints zu belegen.
        self._varMax = dict()
        self._dynamics = "asynchronous"
        self._unitary = True
        self._priorityClasses = dict()
        self._priorityTypes = dict()
        self._psc = None
        self._contexts = dict()
        self._NuSMVpath = None
        self._PRISMpath = None
        self._stgs = list()
        self._varIndex = dict()
        self._initialStates = list()
        self._initialRules = dict()
        # Es wird Zeit sich endlich auf genaue Edgelabels festzulegen:
        self._EDGELABELS = ["+","-","+-","mon+","mon-","obs+","obs-", "obs","free", "mon"]


    def initializePSC(self):
        '''Computes local parameter sets and creates PSC.'''
        
        self.message("initializePSC: is this method still up to date? compare it to ParameterSetup!")
        localParameterSets = dict()
        
        varsToDo = self.varnames()
        for var in self._valueConstraints:
            values = self._valueConstraints[var]
            localParameterSets[var] = CPS.compute_local_constraint_ParameterSets(self, var, self._EDGELABELS, values)
            varsToDo.remove(var)
            
        for var in varsToDo:
            localParameterSets[var] = CPS.compute_local_constraint_ParameterSets(self, var, self._EDGELABELS)
            
        self._psc = PSC.ParameterSetContainer(localParameterSets, mc=self)
        

    def hmsTime(self, seconds):
        '''Time formatting s --> h:m:s.'''
        if seconds < 60:
            return "%is" % int(seconds)
        else:
            minutes = seconds / 60.0
            if minutes < 60:
                return "%im"% int(minutes)
            else:
                hours = int(minutes) / 60
                remaining = int(60.0* (minutes/60.0 - hours))
                return "%ih%im"%(hours,remaining)

    def parameterSetup(self, settings):
        '''Settings are passed from GUI, to create parameter set pool.
        This is called every time the MainWindow's setting object is changed.                   
        (1) Setup IG.
        (2) Compute local parameter sets.
            - BFormulas
            - simplified
            - valueConstraint (and extendedValueConstraint)
            - only edge constraint
            - min/max filter
        (3) Create PSC.

        Parameters: settings
                        'interactions'
                            'edges'
                            'thresholds'
                            'labels'
                        'componentConstraints'
                            'simplified'
                            'valueConstraints'
                            'extendedValueConstraints'
                            'takeMin'
                            'takeMax'
                            'Bformulas'
                        'priorityClasses'
                        'priorityTypes'
                        'dynamics'
                        'unitary'

        Returns: success - True or False
        '''

        if self._psc:
            self.message("MC: parameterFitting(settings) was already called.","error")
            return
        
        IG = nx.DiGraph()
        IG.add_edges_from(settings['interactions']['edges'])
        self.set_IG(IG)
        self.set_dynamics(settings['dynamics'])
        self.set_unitary(settings['unitary'])

        self.set_thresholds(settings['interactions']['thresholds'])
        self.set_edgeLabels(settings['interactions']['labels'])
         
        self.set_priorityClasses(settings["priorityClasses"])
        self.set_priorityTypes(settings["priorityTypes"])

        localParameterSets = dict()
        varsToDo = self.varnames()

        # boolean formulas.
        for var in settings['componentConstraints']['Bformulas']:
            formula = settings['componentConstraints']['Bformulas'][var]
            sets = CPS.compute_local_boolean_ParameterSets(self, var, formula)
            if not sets:
                self.message("MC: Contradiction, there are no parameter sets for %s."%var,"results")
                return False
            localParameterSets[var] = sets
            self.message("computed " + str(len(sets)) + " local sets for " + var + " (Bformula)", "debug")
            varsToDo.remove(var)
        
        
        # simplified.
        for var in settings['componentConstraints']['simplified']:
            if var not in varsToDo:
                self.message("MC: %s cannot be defined by a formula and simplified. Remove one constraint."%var,"error")
                return False
            sets = CPS.compute_local_simplified_ParameterSets(self, var)
            if not sets:
                self.message("MC: Contradiction, there are no parameter sets for %s."%var,"results")
                return False
            localParameterSets[var] = sets
            self.message("computed " + str(len(sets)) + " local sets for " + var + " (simplified)", "debug")
            varsToDo.remove(var)
        
        # value constraints.
        vars = set(list(settings['componentConstraints']['valueConstraints']) + list(settings['componentConstraints']['extendedValueConstraints']))
        for var in vars:
            if var not in varsToDo:
                self.message("MC: %s is value constraint and simplified or defined by a formula. Remove all but one constraints."%var,"error")
                return False
            
            values = {}
            def __set_valueConstraints(context, vals):
                if context in values: 
                    # if values for a context are set more than once, take the last one and report a warning
                    self.message("contradictory value constraints for variable \"" + var + "\" at context \"" + str(context) + "\"\n Using values " + str(vals) ,"warning")
                values[context] = vals
            
            # at first merge extendedValueConstraints into valueConstraints
            if var in settings['componentConstraints']['extendedValueConstraints']:
                all_contexts = self.contexts(var)
                for context in settings['componentConstraints']['extendedValueConstraints'][var]:
                    vals = settings['componentConstraints']['extendedValueConstraints'][var][context]
                    # leerer Kontext bedeutet alle Kontexte (der leere Kontext ist in allen enthalten)s
                    # (Der Fall "values VA 1 3 4"  wird umgewandelt zu "values VA [] 1 3 4" 
                    if len(context)==0:
                        update_these = all_contexts
                    else:
                        print "s" # oder nimm alle Kontexte c, die den Kontext context enthalten:
                        update_these = [c for c in all_contexts if set(context).issubset(set(c))]
                    for con in update_these:
                        __set_valueConstraints(con, vals)
            
            # at last use "normal" value Constraints (these can overwrite extendeConstraints)
            if var in settings['componentConstraints']['valueConstraints']:
                for context in settings['componentConstraints']['valueConstraints'][var]:
                    __set_valueConstraints(context, settings['componentConstraints']['valueConstraints'][var][context])
            
            sets = CPS.compute_local_constraint_ParameterSets(self, var, self._EDGELABELS, values)
            if not sets:
                self.message("MC: Contradiction, there are no parameter sets for %s."%var,"error")
                return False
            localParameterSets[var] = sets
            self.message("computed " + str(len(sets)) + " local sets for " + var + " (value constrained)", "debug")
            varsToDo.remove(var)
            
        # only edge constraint.
        for var in varsToDo:
            sets = CPS.compute_local_constraint_ParameterSets(self, var, self._EDGELABELS)
            if not sets:
                self.message("MC: Contradiction, there are no parameter sets for %s."%var,"error")
                return False
            localParameterSets[var] = sets
            self.message("computed " + str(len(sets)) + " local sets for " + var + " (unconstrained)", "debug")

        # min/max filter.
        for var in settings['componentConstraints']['takeMin']:
            CPS.filter_localParameterSets(self, var, localParameterSets[var], ['Min'])
            if not localParameterSets[var]:
                self.message("MC: Contradiction, there are no parameter sets for %s."%var,"error")
                return False
        for var in settings['componentConstraints']['takeMax']:
            CPS.filter_localParameterSets(self, var, localParameterSets[var], ['Max'])
            if not localParameterSets[var]:
                self.message("MC: Contradiction, there are no parameter sets for %s."%var,"error")
                return False

            
        self._psc = PSC.ParameterSetContainer(localParameterSets)
        print "PSC created", self._psc.size()

        return True

    def pathsSetup(self, preferences):
        self.set_NuSMVpath(preferences["NuSMVpath"])
        self.set_PRISMpath(preferences["PRISMpath"])
        
    def parameterFitting(self, settings):
        '''Settings are passed from GUI, to perform various parameter fitting tasks.
        (1) CTL. (2) PCTL. (3) Extreme. (4) Attractor logic.'''
        
        if settings["CTLformula"] != "":
            if settings.has_key('search'):
                search = settings['search']
            else:
                search = 'exists'
            self.filter_byCTL(settings["CTLformula"], search)
            
        if settings["attractorLogic"] != "":
            self.set_initialStates()
            self.filter_byAL(settings["attractorLogic"])
            
        if settings["filterExtreme"]["use"]:
            search = settings["filterExtreme"]["search"]
            count = settings["filterExtreme"]["count"]
            allowFPs = settings["filterExtreme"]["allowFPs"]
            allowCyc =settings["filterExtreme"]["allowCyc"]
            self.set_initialStates()
            self.filter_extremeAttractors(search, count, allowFPs, allowCyc)
            
        if settings["PCTLformula"] != "":
            self.filter_byPCTL(settings["PCTLformula"])

    def message(self, string, category="debug"):
        if self._print:
            if self._MainWindow:
                self._MainWindow.log(string, category)
            else:
                print string
        
        
    def compute_constraint_parameterSets(self):
        '''
        calls compute_local_ParameterSets() or compute_local_simplified_ParameterSets() for each component.
        '''
        self.message("MC: compute_constraint_parameterSets() hat ausgedient. Verwende initializePSC().","error")

    def filter_localParameterSets(self, varname, conditions):
        self.message("MC: filter_localParameterSets(self, varname, conditions) nach CPS verschoben.","error")
        
    def set_IG(self, IG):
        if not self._IG == None: self.message("Warning: existing IG is overwritten.")

        contexts = dict()
        varnames = sorted(IG.nodes())
        for var in varnames:
            if len(var)<=1:
                self.message("Warning: Variable %s is too short for NuSMV variable declaration (2 chars needed)." % var)
            predSet = IG.predecessors(var)
            contexts[var] = {tuple():0}
            for level in range(1,len(predSet)+1):
                for subset in IT.combinations(predSet, level):
                    contextId = self.contextId(subset)
                    contexts[var][contextId] = 0

        self._contexts = contexts
        self._IG = IG.copy()

        varIndex = {}
        for i in range(len(varnames)) :
            varIndex[i] = varnames[i]
            varIndex[varnames[i]] = i
        self._varIndex = varIndex

    def get_stateSpaceSize(self):
        size = 1
        for var in self.varnames():
            size *= self.varMax(var)+1
        return size

    def set_initialStates(self, initialRules = None) :
        if initialRules :
            self.set_initialRules(initialRules)
        self._initialStates = self._generate_initialStates()

    def get_initialStates(self):
        return self._initialStates

    def _generate_initialStates(self):
        """
        Compute the initial states, following the rules given by self.initialRule().
        """
        # get the range of all values
        valuesRange = []
        for var in sorted(self.varnames()) :
            try:
                min, max = self.initialRule(var)
                valuesRange.append(range(min, max+1))
            except:
                valuesRange.append(range(self.varMax(var)+1))
        
        # compute initial states
        initialStates = []
        for p in IT.product(*valuesRange) : 
            initialStates.append(list(p))
        
        return initialStates

    def set_priorityClasses(self, prioClasses):
        '''prioClasses = {var:class, class:[var]}.'''
        self._priorityClasses = prioClasses.copy()

    def priorityClass(self, var):
        return self._priorityClasses[var]

    def set_priorityTypes(self, prioTypes):
        '''prioTypes = {class:dynamics} dynamics in ["asynchronous","synchronous"].'''
        self._priorityTypes = prioTypes.copy()

    def priorityTyp(self, var):
        return self._priorityTypes[var]

    def set_initialRules(self, rules):
        """
        Set the dictionary initial rules.
        
        Parameter:
            rules - rules[var] = min, max
        """
        self._initialRules = rules

    def initialRule(self, var):
        return self._initialRules[var]

    def get_dynamics(self):
        return self._dynamics

    def set_thresholds(self, thresholds):
        self._thresholds = thresholds.copy()
        for var in self._IG.nodes():
            Max = 1
            for suc in self.successors(var):
                Max = max(Max, self.threshold(var, suc))
            self._varMax[var] = Max

    def threshold(self, *args):
        if len(args)==2:
            return self._thresholds[(args[0],args[1])]
        elif type(args[0])==tuple:
            return self._thresholds[args[0]]
        else:
            return self._thresholds[tuple(args[0])]

    def set_edgeLabels(self, edgeLabels):
        '''Labels: +,-,+-,observable, obs+, obs-, free, not-, not+.'''
        self._edgeLabels = edgeLabels.copy()

    def set_valueConstraints(self, valueConstraints):
        '''valueConstraints: dict[var]=[value,..].'''
        if self._valueConstraints:
            self.message("MC: value constraints are overwritten.","warning")
            self._valueConstraints = valueConstraints
        varnames = self.varnames()
        if not varnames:
            self.message("MC: need IG before value constraints.","error")
            return
        for var in valueConstraints.keys():
            if not var in varnames:
                self.message("MC: %s is not in network. Skipped."%var,"error")
                continue
            self._valueConstraints[var] = valueConstraints[var] # removed a probably buggy list() here (Martin, 13/03/12)
                         

    def edgeLabel(self, (var1, var2)):
        '''edgeLabel in [+,-,+-,obs+,obs-,not+,not-,observable,free]'''
        return self._edgeLabels[(var1,var2)]

    def set_dynamics(self, dynamics):
        '''dynamics in ["asynchronous", "synchronous", "priorityClasses"]'''
        if not dynamics in ["asynchronous", "synchronous", "priorityClasses"]:
            self.message("Warning: dynamics must be \"asynchronous\", \"synchronous\" or \"priorityClasses\"\nSet to \"asynchronous\"")
            dynamics = "asynchronous"
        self._dynamics = dynamics

    def set_unitary(self, unitary):
        """unitary = True for unitary steps and unitary = False for non-unitary steps"""
        if not type(unitary)==bool:
            self.message("(MC) Warning: unitary must be True or False. Set to True", category="warning")
            unitary= True
        self._unitary = unitary

    def get_unitary(self):
        return self._unitary

    def get_stgs(self):
        return self._stgs

    def varIndex(self, key):
        return self._varIndex[key]

    def set_NuSMVpath(self, path):
        check = LFG.test_NuSMVpath(path)
        if check["working_version"]:
            self._NuSMVpath = path
        else:
            self.message("MC: set_NuSMVpath() called with invalid path=%s"%path,"error")
        
    def set_PRISMpath(self, path):
        self._PRISMpath = path

    def varnames(self):
        return self._IG.nodes()

    def contexts(self, varname):
        return self._contexts[varname].keys()

    def successors(self, varname):
        return self._IG.successors(varname)

    def predecessors(self, varname):
        return self._IG.predecessors(varname)

    def contextId(self, context):
        if context == [] or context == tuple(): return tuple()
        if type(context)==list:
            return tuple(sorted(context))
        elif type(context)==tuple:
            return tuple(sorted(list(context)))

    def modify_varMax(self, varMax):
        self._varMax.update(varMax)

    def varMax(self, var):
        return self._varMax[var]

    def max_number_of_sets(self): # Nach PSC.
        localSets = []
        for var in self.varnames():
            localSets.append((self.varMax(var)+1)**len(self.contexts(var)))
        return reduce(lambda x,y:x*y, localSets, 1)
        

    def compute_STG(self, parameterSet) :
        
        # erzeuge Zustandsuebergangsgraphen
        stg = STGG.generate_newSTG()
        
        # fuege Kanten (und implizit damit auch die Knoten) hinzu
        if self.get_dynamics() == 'synchronous' :
            STGG.set_edges_sync_int(self, stg, parameterSet)
            
        elif self.get_dynamics() == 'asynchronous' :
            STGG.set_edges_async_int(self, stg, parameterSet)
            
        elif self.get_dynamics() == 'priorityClasses' :
            STGG.set_edges_priCl_int(self, stg, parameterSet)
            
        else :
            self.message('ERROR: dynamics must be \"asynchronous\", \"synchronous\" or \"priorityClasses\"!',category="error")
            
        # fertig
        self._stgs.append(stg)

    def compute_STGs(self):
        count = 0
        start = time.time()
        for parameterSet in self._psc.get_parameterSets():
            if count % 1000 == 0 :
#                self._stgs = []  # TODO: Speichern anstatt ueberschreiben
                self.message("..already %i STGs in %.0f seconds computed" % (count, time.time() - start), category="debug")
            self.compute_STG(parameterSet)
            count += 1

#        step = 5000
#        for b in xrange(0, 10000, step) :
##            self._stgs = []
#            for i in xrange(b, b+step) :
#                if count % 1000 == 0 :
#                    print "..already %i STGs in %.0f seconds computed" % (count, time.time() - start)
#                self.compute_STG(self._parameterSets[i])
#                count += 1
            
        end = time.time()
        self.message("(MC) Computed %i STGs in %.0f seconds." % (count, end-start), category="results")

    def filter_byCTL(self, CTLspec, search="exists"):
        '''Adds indices to _filteredParametersIndexList for parameterSets that do not satisfy the CTL formula for all states (search="forAll") or for at least one state (search="exists").'''
        try:
            if not self._NuSMVpath:
                self.message("The path the to NuSMV is not set.", category="error")  
            else:
                self.message("Starting CTL model selection ...", category="debug")
                SMVpath = os.path.join(os.getcwd(),"temp.smv") # statt os.getcwd() stand frueher sys.path[0], was bei unit tests Probleme gemacht hat
    
                if search == "exists":
                    validation = "is false"
                    formula = "!("+CTLspec+")"
                elif search == "forAll":
                    validation = "is true"
                    formula = "("+CTLspec+")"
                else:
                    raise Exception("search should be exist or forAll!")
    
                counter = 0
                accepted = 0
                indexList = []
                initialSize = len(self._psc)
                self.startProgressBar()
                start = time.time()
                for i, parameterSet in enumerate(self._psc.get_parameterSets()):
                    fileString = LFG.generate_smv(self, parameterSet, formula)
                    tempFile = open("temp.smv", "w")
                    tempFile.write(fileString)
                    tempFile.close()
                    
                    cmd = self._NuSMVpath+" "+SMVpath
                    output = SP.Popen(cmd, shell=True, stdin=SP.PIPE, stdout=SP.PIPE, stderr=SP.STDOUT)
                    outputread = output.stdout.read()
                    if "ERROR" in outputread or not "This is NuSMV" in outputread:
                        raise Exception(outputread)
                    if validation in outputread:
                        accepted += 1
                        if accepted % 100 == 0:
                            sys.stdout.write("!")
                    else:
                        indexList.append(i)
                        
                    counter += 1
                    self.stepProgressBar(counter)
                    if counter % 500 == 0:
                        sys.stdout.write(".")
                end = time.time()
                finalSize = initialSize - len(indexList)
                self._psc.reject(indexList)
                self.message("\nFinished CTL model selection in %s. Parameter sets before/after: %i/%i" % (self.hmsTime(end-start), initialSize, finalSize), category="results")
        except TypeError, e:
            import traceback
            self.message(traceback.format_exc())
            if not self._psc:
                self.message('(MC.filter_byCTL) Warning: Parameter Set Container is empty.')            

    def filter_byPCTL(self, PCTLspec, search="exists"):
        '''Saves parameter sets that satisfy the PCTL formula for all states (search="forAll") or for at least one state (search="exists").'''
        try:
            if not self._PRISMpath:
                self.message("The path to PRISM is not given.")
            elif not PCTLspec:
                self.message("No PCTL spec given.")
            else:
                self.message("Starting PCTL model selection ...")
                PMpath = os.path.join(os.getcwd(),"temp.pm") # statt os.getcwd() stand frueher sys.path[0], was bei unit tests Probleme gemacht hat
    
                if search == "exists":
                    validation = "Result: false"
                    PCTLspec = "'!("+PCTLspec+")'"
                elif search == "forAll":
                    validation = "Result: true"
                    PCTLspec = "'"+PCTLspec+"'"
                
                counter = 0
                accepted = 0
                indexList = []
                initialSize = len(self._psc)
                self.startProgressBar()
                start = time.time()
                for i,parameterSet in enumerate(self._psc.get_parameterSets()):
                    tempFile = open("temp.pm", "w")
                    fileString = LFG.generate_pm(self, parameterSet)
                    tempFile.write(fileString)
                    tempFile.close()
                    cmd = self._PRISMpath+" "+PMpath+" -pctl "+PCTLspec+" -fixdl"
                    output = SP.Popen(cmd, shell=True, stdin=SP.PIPE, stdout=SP.PIPE, stderr=SP.STDOUT, close_fds=True)
                    
                    out = output.stdout.read()
                    
                    if validation in out:
                        accepted += 1
                        if accepted % 100 == 0:
                            sys.stdout.write("!")
                    else:
                        indexList.append(i)
                        
                    counter += 1
                    self.stepProgressBar(counter)
                    if counter % 500 == 0:
                        sys.stdout.write(".")
                end = time.time()
                self._psc.reject(indexList)
                finalSize = len(self._psc)
                self.message("\nFinished PCTL model selection in %s. Parameter sets before/after: %i/%i" % (self.hmsTime(end-start), initialSize, finalSize))
        except TypeError, e:
            import traceback
            self.message(traceback.format_exc())
            if not self._psc:
                self.message('(MC.filter_byPCTL) Warning: Parameter Set Container is empty.')

    def filter_parallelCTL(self, CTLspec, search="exists", processors=3):
        '''Saves parameter sets that satisfy the CTL formula for all states (search="forAll") or for at least one state (search="exists").'''
        try:
            from IPython.kernel import client
            if not self._NuSMVpath:
                self.message("The path the to NuSMV is not set.", category="error")
            else:
                self.message("Starting CTL model selection ...", category="debug")
    
                if search == "exists":
                    validation = "is false"
                    formula = "!("+CTLspec+")"
                elif search == "forAll":
                    validation = "is true"
                
                '''
                initialSize = 1
                for var in self._localParameterSets:
                    initialSize *= len(self._localParameterSets[var])
                '''
                initialSize = len(self._psc)
    
                start = time.time()
                os.system("ipcluster local -n %i &" % processors)
                mec = client.MultiEngineClient()
                fileStrings = [LFG.generate_smv(self, pSet, formula) for pSet in self._psc.get_parameterSets()]
                mec.scatter("fileStrings", fileStrings)
                ids = mec.get_ids()
                mec.scatter("engineId",ids)
                currentPath = os.getcwd() # statt os.getcwd() stand frueher sys.path[0], was bei unit tests Probleme gemacht hat
                command = self._NuSMVpath+" "+currentPath
                mec.push(dict(CTLspec=formula, CTLvalidation=validation, callCommand = command))
                mec.execute("import imp")
                mec.execute("import os")
                mec.execute("MECfunction = imp.load_source('MECfunction', os.path.join(os.pardir,os.pardir, 'Modul_ModelContainer','2_Source','MECfunction.py'))")
                mec.execute("results = MECfunction.checkPS(fileStrings, callCommand, CTLspec, CTLvalidation, engineId)")
                indexList =  mec.gather("results")
                mec.kill(controller=True)
                end = time.time()
    
                finalSize = initialSize - len(indexList)
                self._psc.reject(indexList)
                self.message("\nFinished CTL model selection in %s. Parameter sets before/after: %i/%i" % (self.hmsTime(end-start), initialSize, finalSize), category="results")
        except TypeError:
            import traceback
            self.message(traceback.format_exc())
            if not self._psc:
                self.message('(MC.filter_parallelCTL) Warning: Parameter Set Container is empty.')

    def filter_byAL(self, ALformula):
        '''.'''
        try:
            counter = 0
            accepted = 0
            indexList = []
            initialSize = len(self._psc)
            self.startProgressBar()
            start = time.time()
            for i, parameterSet in enumerate(self._psc.get_parameterSets()):
                ts = TS.TransitionSystem(self, parameterSet)
                if AL.evaluate(ALformula,ts,preprocessing = True):
                    accepted += 1
                    if accepted % 100 == 0:
                        sys.stdout.write("!")
                else:
                    indexList.append(i)
                
                counter += 1
                self.stepProgressBar(counter)
                if counter % 500 == 0:
                    sys.stdout.write(".")
            end = time.time()
            self._psc.reject(indexList)
            finalSize = len(self._psc)
            self.message("\nFinished AL  model selection in %s. Parameter sets before/after: %i/%i" % (self.hmsTime(end-start), initialSize, finalSize))
        except TypeError:
            import traceback
            self.message(traceback.format_exc())
            if not self._psc:
                self.message('(MC.filter_byAL) Warning: Parameter Set Container is empty.')

    def _acc2rej(self, accepted, length) :
        rejected = range(length)
        for i in accepted:
            rejected.remove(i)
        return rejected

    def filter_extremeAttractors(self, search, count, allowFPs, allowCyc) :
        """
        Filters the parameter sets with minimal/maximal number of attractors (with or without fixpoints). 
        
        Parameters:
            search - 'min' or 'max'
            count - 'states' or 'attrs'
            allowFPs - True or False
            allowCyc - True of False
        
        Pseudocode:
        filter_extremeAttractors(search, count, allowFPs, allowCyc) :
            if search == 'min' :
                compareTo = '<'
                extremeNumberOfAttractors = infinity
            else if search == 'max' :
                compareTo = '>'
                extremeNumberOfAttractors = -infinity
            else :
                print "Error"
                return

            enum(ts) <- Count states or attractors of ts, with fixpoints and/or cyclic attractos. 
        
            indices = list()
            for parameterSet in parameterSets :
                ts <- new TransitionSystem(self, parameterSet)
                numberOfAttractors <- enum(ts)
                if (numberOfAttractors compareTo extremeNumberOfAttractors) :
                    extremeNumberOfAttractors <- numberOfAttractors
                    indices <- [indice(parameterSet)]
                else if (numberOfAttractors == extremeNumberOfAttractors) :
                    indices.append(indice(parameterSet))
        
             self._psc.reject(rejectIndices)        
        """
        # decide what to search.
        if search == 'min' :
            op = '<'
            ex = float('inf')
        elif search == 'max' :
            op = '>'
            ex = float('-inf')
        else :
            self.message('Fex: TypeError: \"search\" must be either \'min\' or \'max\'.', "error")
            return

        # decide what to count.
        if count=="states":
            if allowFPs and allowCyc:
                enum=lambda tSys: tSys.states()
            elif allowFPs:
                enum=lambda tSys: tSys.fixpoints()
            elif allowCyc:
                enum=lambda tSys: tSys.states()-tSys.fixpoints()
        elif count=="attrs":
            if allowFPs and allowCyc:
                enum=lambda tSys: tSys.attrs()
            elif allowFPs:
                enum=lambda tSys: tSys.fixpoints()
            elif allowCyc:
                enum=lambda tSys: tSys.cAttrs()

        initialSize = len(self._psc)
        indices = list()
        self.startProgressBar()
        self.message("Fex: Starting filter.", "debug")
        start = time.time()
        for pos, parameterSet in enumerate(self._psc.get_parameterSets()) :
            if pos % 1000==0:
                sys.stdout.write('.')
            self.stepProgressBar(pos)
            ts = TS.TransitionSystem(self, parameterSet)
            val = enum(ts)
            if eval(str(val) + op + 'ex') :
                ex = val
                indices = [pos]
            elif val == ex :
                indices.append(pos)
        end = time.time()
        vector = self._acc2rej(indices, initialSize)
        self._psc.reject(vector)
        finalSize = len(self._psc)
        if allowFPs and not allowCyc:
            allow = "(FPs only)"
        elif not allowFPs and allowCyc:
            allow = "(cyclic attractors only)"
        else:
            allow = str()
        strings = (search,"attractors" if count=="attrs" else "attracting states", allow, ex, self.hmsTime(end-start), initialSize, finalSize)
        self.message("Fex: %s %s %s: %i. Computed in %s. Sets before/after: %i/%i." % strings, "result")

        # for unitTests.py return extreme value.
        return ex
 
    def get_transitionSystems(self):
        parameterSets = self._psc.get_parameterSets()
        for pSet in parameterSets:
            yield TS.TransitionSystem(self, pSet)

    def export_commonSTG(self, Type, filename, initialRules=None):
        if initialRules:
            self.set_initialRules(initialRules)
        self.set_initialStates()
        tslist = list(self.get_transitionSystems())
        if Type=="transitions":
            com = STGC.compute_commonStg1(tslist)
        elif Type=="SCC":
            com = STGC.compute_commonStg2(tslist) # FIXME: no effect?
        if com:
            nx.write_gml(com,filename)

    def export_singleSTG(self,pSid,Type,Isomorphy,localIGs,NNF,filename,initialRules):
        # TODO: localIGs
        # TODO: filename = Unterordner mit Dateien oder Dateiname filename+Suffix?
        # TODO: GML nested network?
        filename = str(filename)
        if not filename[-4:]==".gml":
            filename += ".gml"
        self.set_initialRules(initialRules)
        self.set_initialStates()
        
        found=False
        for i, pSet in enumerate(self._psc.get_parameterSets()):
            if i==pSid:
                found = True
                break
        if not found:
            self.message("MC: STG with index %i does not exist. Choose index between 0 and %i."%(pSid,i), "error")
            return
            
        ts = TS.TransitionSystem(self, pSet)
        ts.compute_destination()
        if Type=="SCC":
            ts.computeSCCDAG(Isomorphy,NNF)
            nx.write_gml(ts._sccdag._nxSCCDAG,filename)
            if NNF:
                filename = filename[-4:]+".nnf"
                han=open(filename,"w")
                han.write(ts._sccdag._nnfNN)
                han.close()
        elif Type=="allStates":
            nx.write_gml(ts.getDestinySTG(),filename)
        else:
            self.message("Choose either SCC Graph or Full State Graph.","error")

    def startProgressBar(self, Max=None):
        mw = self._MainWindow
        if mw:
            mw.progressBar.reset()
            mw.progressBar.setMinimum(0)
            if Max:
                #assert(type(Max) == int)
                mw.progressBar.setMaximum(Max)
            elif len(self._psc):
                mw.progressBar.setMaximum(len(self._psc))

    def stepProgressBar(self, step):
        if self._MainWindow:
            self._MainWindow.progressBar.setValue(step)

    def resetProgressBar(self):
        if self._MainWindow:
            self._MainWindow.progressBar.reset()
   
    def filter_byTimeSeries(self, timeseries, monotony):
        """See dcumentation of ``inGraphChecker`` for details"""

        assert(self._dynamics == "asynchronous" and self._unitary)

        # initialize class inGraphChecker without Parameter Set
        iGC = IGC.inGraphChecker(self._IG, self._thresholds, dict(), MainWindow = self._MainWindow)
        iGC.set_timeseries(timeseries, monotony)
        
        # if you want to use A* (Astar), set iGC._useAstar = True
        # iGC._useAstar = True

        self.message("Start filtering time series...","result")

        self.startProgressBar()
        start = time.time()
        rejectList = list()
        accepted = 0
        for pos, parameterSet in enumerate(self._psc.get_parameterSets()) :
            self.stepProgressBar(pos)
            iGC.set_PS(parameterSet)
            if iGC.proofTimeSeries():
                accepted += 1
            else:
                rejectList.append(pos)
	
        initialSize = len(self._psc)
        self._psc.reject(rejectList)
        finalSize = len(self._psc)
        end = time.time()
        
        # statistics ausgeben
        stats = iGC.get_statistics()#dict(total = 1000, accepts = 120, rejects = [31, 69, 224, 556]) #
        string = "Statistics of Filtering TimeSeries:\n"
        string += "States are formatted as (" + ",".join(v for v in sorted(timeseries[0])) + ")"
        string += "<table border=0><tr><td><b>state</b></td><td><b>rejected</b></td></tr>"
	string += "<tr><td>("+ ",".join(str(timeseries[0][v]) for v in sorted(timeseries[0])) + ")</td><td>" + "0" + "</td></tr>"        
        for i in range(len(stats["rejects"])):
        	string += "<tr><td>("+ ",".join(str(timeseries[i+1][v]) for v in sorted(timeseries[i+1])) + ") </td><td>"+ str(stats["rejects"][i]) + "</td></tr>"
        string += "<tr><td><b>accepts</b> </td><td>" + str(stats["accepts"]) + "</td></tr>"
        string += "<tr><td>total</td><td>" + str(stats["total"]) + "</td></tr></table>\n"
        self.message(string)
        self.message( "Accepted %i/%i in %s."%(finalSize, initialSize, self.hmsTime(end-start)), "result")



    def feasibility_byTimeSeries(self, timeseries, monotony):
        '''Return True if there is a parameter set that can reproduce the time series, otherwise False.'''
        assert(self._dynamics == 'asynchronous' and self._unitary)
        # 1.Initialisierungen
        igc = IGC.inGraphChecker(self._IG, self._thresholds, {})
        igc.set_timeseries(timeseries, monotony)
        
        # if you want to use A* (Astar), set iGC._useAstar = True
        # iGC._useAstar = True
                
        self.startProgressBar()

        # 2.Main-Loop
        start = time.time()
        for pos, parameterSet in enumerate(self._psc.get_parameterSets()):
            igc.set_PS(parameterSet)
            self.stepProgressBar(pos)
            if igc.proofTimeSeries():
                return True
        return False

    def filter_byContextPreprocessor(self, ts, monotony):
        '''global_problems, local_problems = self._MC.filter_byPreprocessor(ts, mon)'''
        #0.Initialisierungen
        initialSize = len(self._psc)
        rejectList = []
        problems = {}
        preprocessors = {}
        for i in range(len(ts)-1):
            s1 = ts[i]
            s2 = ts[i+1]
            mon = monotony[i]
            preprocessors[i] = ConP.Preprocessor(self, s1, s2, mon)
            for name in self.varnames():
                problems[(name, i)] = 0

        #1.Parameter Set Loop.
        self.startProgressBar()
        start = time.time()
        for pos, parameterSet in enumerate(self._psc.get_parameterSets()):
            #2.TimeSeries Loop.
            reject_pos = False
            for i in range(len(ts)-1):
                p_names = preprocessors[i].find_problem_names(parameterSet)
                if p_names:
                    reject_pos = True
                    for name in p_names:
                        problems[(name, i)] += 1
            if reject_pos:
                rejectList.append(pos)
            self.stepProgressBar(pos)
        end = time.time()
        self.message( "Preprocess rejected %i sets in %s."%(len(rejectList),self.hmsTime(end-start)), "message")

        #3.Inaktzeptable sets verwerfen
        start = time.time()
        self._psc.reject(rejectList)
        end = time.time()
        self.message( "Rejection in %s."%self.hmsTime(end-start), "debug")

        #4.Problem Auswertung
        global_problems = []
        local_problems = []
        for name, i in problems:
            if problems[(name,i)] > 0:
                local_problems.append((name, i, problems[(name,i)]))
            if problems[(name,i)] == initialSize:
                global_problems.append((name, i))

        return global_problems, local_problems

    def exist_reproducing_and_incompatible_psets(self, ts, monotony):
        '''exists_repr, exists_inc = exist_reproducing_and_incompatible_psets(self, ts, mon)'''
        
        #0.Initialisierungen
        preprocessors = {}
        for i in range(len(ts)-1):
            s1 = ts[i]
            s2 = ts[i+1]
            mon = monotony[i]
            preprocessors[i] = ConP.Preprocessor(self, s1, s2, mon)
        igc = IGC.inGraphChecker(self._IG, self._thresholds, {})
        igc.set_timeseries(ts, monotony)
                
        exists_reproducing_pset = False
        exists_incompatible_pset = False

        #1. ParameterSet Loop.
        for pos, parameterSet in enumerate(self._psc.get_parameterSets()):

            #2. Preprocessor.
            reject = False
            for i in range(len(ts)-1):
                if preprocessors[i].find_problem_names(parameterSet):
                    exists_incompatible_pset = True
                    reject = True

            #3. inGraphChecker
            if not reject:
                igc.set_PS(parameterSet)
                if igc.proofTimeSeries():
                    exists_reproducing_pset = True
                else:
                    exists_incompatible_pset = True

            # Abbruchbedingung: es gibt Parametermengen von beiden Typen
            if exists_reproducing_pset and exists_incompatible_pset:
                break

        return exists_reproducing_pset, exists_incompatible_pset
            
        

        

def testrun1():
#    mc = ModelContainer()
#    IG = nx.DiGraph()
#    IG.add_edges_from([("A","B"),("A","C"),("B","C"),("B","A"),("C","A"),("C","B")])
#    mc.set_IG(IG)
#    mc.set_thresholds({("A","B"):2,("A","C"):1,("B","C"):2,("B","A"):1,("C","A"):2,("C","B"):1})
#    mc.set_edgeLabels({("A","B"):"free",("A","C"):"free",("B","C"):"free",("B","A"):"free",("C","A"):"free",("C","B"):"free"})
#    mc.compute_constraint_parameterSets()
#    mc.set_initialStates()
#    mc.initializePSC()
#    mc.filter_extremeAttractors(Type="max", allowFixpoints=False)
#    for pSet in mc._psc._parameterSets:
#        mc.compute_STG(pSet)
#    for i, stg in enumerate(mc._stgs):
#        print nx.info(stg)
#        nx.write_gml(stg, "stg%i.gml"%i)
    
    
    mc = ModelContainer()
    IG = nx.DiGraph()
    IG.add_edges_from([("vA","vB"),("vB","vC"),("vC","vB"),("vC","vD"),("vD","vC"),("vD","vA"),("vA","vC")])
    mc.set_IG(IG)
    mc.set_thresholds({("vA","vB"):1,("vB","vC"):1,("vC","vB"):1,("vC","vD"):1,("vD","vC"):1,("vD","vA"):1,("vA","vC"):1})
    mc.set_edgeLabels({("vA","vB"):"free",("vB","vC"):"free",("vC","vB"):"free",("vC","vD"):"free",("vD","vC"):"free",("vD","vA"):"free",("vA","vC"):"free"})
    mc.compute_constraint_parameterSets()
    mc.set_initialStates()
    mc.initializePSC()

    print "PSC:",len(mc._psc)
    state1 = {"vA":0, "vB":0,"vC":0,"vD":0}
    state2 = {"vA":1, "vB":0,"vC":0,"vD":0}
    state3 = {"vA":1, "vB":1,"vC":0,"vD":0}
    state4 = {"vA":0, "vB":1,"vC":1,"vD":0}
    state5 = {"vA":0, "vB":0,"vC":1,"vD":1}
    state6 = {"vA":0, "vB":0,"vC":0,"vD":1}
    timeSeries = [state1, state2, state3, state4, state5, state6, state1]

    noneMonotone = {"vA":False, "vB":False,"vC":False,"vD":False}
    monotonyMatrix = [noneMonotone]*6
    
    mc.filter_byTimeSeries(timeSeries, monotonyMatrix)

    print "PSC:",len(mc._psc)
    
    
#    ts = TS.TransitionSystem(mc, parameterSet)
#    ts.computeAttrInfos()
#    print ts.stg().nodes()
#    print ts.getAttrInfos()
#    print ts.attrs()
#    print ts.fixpoints()
#    print ts.cAttrs()
#    
#    print '\n---Attraktoren---'
#    ts._attrs = [('00','01','02'), ('12','22')]
#    for attr in ts._attrs :
#        print attr
#    
#    # Test AttrInfo.py
#    print '\n---Test AttrInfo.py---'
#    ts._aInfos = []
#    ts.computeAttrInfos()
#    for ai in ts.getAttrInfos() :
#        print ai.states('_2')
#        print ''
    
    

if __name__=="__main__":
    testrun1()
    print '\n..Done'
    
