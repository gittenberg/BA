import networkx as nx
import imp
import os
STG = imp.load_source("STG", os.path.join("STG.py"))
AI = imp.load_source("AI", os.path.join("AttrInfo.py"))
SCCDAG = imp.load_source("SCCDAG", os.path.join("SCCDAG.py"))
DSTG = imp.load_source("DSTG", os.path.join("DestinySTG.py"))


# TODO: compute*() Methoden sollten private sein (um doppelte Aufrufe zu verhindern)!! (zB computeAttrInfos appended sonst doppelt)
class TransitionSystem() :  
    def __init__(self, mc, parameterSet) :
        self._mc = mc
        self._parameterSet = parameterSet
        self._stg = STG.STG()   # Vorsicht! self._stg enthaelt nur eine Instanz der Klasse STG.py. Auf den eigentlichen STG (nx.DiGraph) kann man mittels self._stg.stg() bzw. self.stg() zugreifen.
        self._computeSTG()      # Ohne stg() kann der Rest nicht berechnet werden (insbesondere self._attrs)!
        self._sccdag  = None
        self._attrs   = None
        self._sccs    = None    # (Knoten>SCC , SCC>[Knoten], [[SCC],...])
        self._destiny = None
        self._aInfos  = []

    def stg(self) :
        """
        Returns the STG (networkx.DiGraph).
        """
        return self._stg.stg()

    def sccs(self):
        if not self._sccs :
            self._sccs = self.scc_dicts() # (Knoten>SCC , SCC>[Knoten])
        return self._sccs[2]
    
    def scc2nodes(self) :
        if not self._sccs :
            self._sccs = self.scc_dicts() # (Knoten>SCC , SCC>[Knoten])
        return self._sccs[1]

    def _computeSTG(self) :

        if self._mc.get_dynamics() == 'synchronous' :
            self._stg.set_edges_sync(self._mc, self._parameterSet)

        elif self._mc.get_dynamics() == 'asynchronous' :
            self._stg.set_edges_async(self._mc, self._parameterSet)

        elif self._mc.get_dynamics() == 'priorityClasses' :
            self._stg.set_edges_priCl(self._mc, self._parameterSet)

        else :
            self._mc.message('ERROR: dynamics must be \"asynchronous\", \"synchronous\" or \"priorityClasses\"!')

    
    def attrs(self) :
        """
        Returns the number of attractors.
        """
        if not self._attrs :
             self._attrs = nx.attracting_components(self.stg())
        return len(self._attrs)

    def states(self) :
        """
        Returns the number of states in all attractors.
        """
        if not self._attrs :
             self._attrs = nx.attracting_components(self.stg())
        return reduce(lambda x, y: x + len(y), self._attrs, 0) # equivalent to sum([len(attr) for attr in self._attrs])

    def fixpoints(self) :
        """
        Returns the number of fixpoints.
        FIXED: [Fixpunkte == Attraktoren mit genau einem Zustand?] JA.
        """
        if not self._attrs :
             self._attrs = nx.attracting_components(self.stg())
        return len([fix for i,fix in enumerate(self._attrs) if len(self._attrs[i])==1])
    
    def cAttrs(self) :
        """
        Returns the number of cyclic attractors.
        FIXED: [cAttraktoren == Attraktoren mit mehr als einem Zustand?] JA.
        """
        if not self._attrs :
             self._attrs = nx.attracting_components(self.stg())
        return len([fix for i,fix in enumerate(self._attrs) if len(self._attrs[i])>1])


    def scc_dicts(self) :
        """
        bestimmt SCCs und gibt dictionary Knoten>SCC und SCC>[Knoten] zurueck
        SCCs, die nur aus einem Element bestehen, welches kein Attraktor (= nicht in attr)
        ist, werden in SCC 0 verschoben und tauchen in node2scc nicht auf
        """
        if not self._attrs :
             self._attrs = nx.attracting_components(self.stg())
        sccs=nx.strongly_connected_components(self.stg()) # erzeugt Liste SCC>[Knoten]
        node2scc={}
        scc2nodes={}
        attr_flattened=[item for sublist in [list(x) for x in self._attrs] for item in sublist]
        # Liste durchgehen und a) fuer jeden Knoten SCC und b) fuer jede SCC Knoten speichern
        for (i,nodes) in enumerate(sccs):
            for node in nodes:

                # pruefen, ob Knoten in trivialem SCC liegt und kein Attraktor ist
                if len(nodes)<=1 and (node not in attr_flattened):
                    scc_index=0 # in diesem Fall wird Knoten in SCC 0 verschoben
                else:
                    # ansonsten entspricht die SCC-Nummer dem Index+1
                    # +1, damit Index 0 fuer Sammlung trivialer SCCs zur Verfuegung steht
                    scc_index=i+1

                    node2scc[node]=scc_index # dictionary Knoten>SCC schreiben

                if scc_index not in scc2nodes: # pruefen, ob SCC bereits in dictionary SCC>[Knoten] vorhanden ist
                    scc2nodes[scc_index]=[] # ggf. Eintrag erstellen
                scc2nodes[scc_index].append(node) # und aktuellen Knoten hinzufuegen

        return(node2scc,scc2nodes,sccs)

    # Berechnet fuer jeden Zustand in self.stg() die Liste von Attraktoren, die erreicht werden koennen
    def compute_destination(self):
        if not self._attrs :
             self._attrs = nx.attracting_components(self.stg())
        reverseSTG=self.stg().reverse(copy=True) # STG umdrehen
        destiny = {}
        for id,attractor in enumerate(self._attrs): # jeden Attraktor als Start waehlen
            visited=[]
            to_visit=[]
            # TODO: Einrueckung falsch!!?? > Kann sein, allerdings wuesste ich nicht, warum?
            for node in attractor: # Zustaende im aktuellen Attraktor zum Besuchen vormerken
                to_visit.append(node)

            while len(to_visit)>0: # solange noch Zustaende zu besuchen sind
                node=to_visit[0]
                if node not in destiny: # ggf. einen Eintrag in _destiny fuer aktuellen Knoten erstellen
                    destiny[node]=[]
                destiny[node].append(id) # und Liste um aktuellen Attraktor erweitern

                visited.append(node) # dann Knoten als besucht speichern
                to_visit.remove(node)
                for edge in reverseSTG.edges(node): # und die Nachfolger
                    if edge[1] not in visited and edge[1] not in to_visit: # ggf.
                        to_visit.append(edge[1]) # zum Besuchen vormerken
        return destiny



    def computeSCCDAG(self,Isomorphy,NNF,GML=False) :
        if not self._attrs :
            self._attrs = nx.attracting_components(self.stg())
        if not self._sccs :
            self._sccs = self.scc_dicts() # (Knoten>SCC , SCC>[Knoten])
        if not self._destiny :
            self._destiny = self.compute_destination()
#        self._sccdag = SCCDAG(self.stg(), compute_nested_networks_for_gml, compute_nested_networks_for_nnf)
        self._sccdag = SCCDAG.SCCDAG(self.stg(), self._attrs, self._sccs, self._destiny, GML, NNF,Isomorphy)


    def getDestinySTG(self) :
        if not self._attrs :
            self._attrs = nx.attracting_components(self.stg())
        if not self._sccs :
            self._sccs = self.scc_dicts() # (Knoten>SCC , SCC>[Knoten])
        if not self._destiny :
            self._destiny = self.compute_destination()
        DestSTG=DSTG.DestinySTG(self.stg(), self._attrs, self._sccs, self._destiny)
        return DestSTG.getDestinySTG()

    def _computeAttrInfos(self) :
        if not self._attrs :
            self._attrs = nx.attracting_components(self.stg())
        for id, attr in enumerate(self._attrs) :
            self._aInfos.append(AI.AttrInfo(self._mc, id, attr))
    
    def getAttrInfos(self) :
        if len(self._aInfos) == 0 :
            self._computeAttrInfos()
        return self._aInfos
