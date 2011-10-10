import networkx as nx
from operator import itemgetter

""" ZIEL
uebergangsgraph uebersichtlich darstellen, wobei dieser auf strongly connected components (SCCs)
reduziert wird. Attraktoren hervorheben. """
""" VORGEHEN
1. ueber eingebaute Methoden von networkx Attraktoren und SCCs finden und bestimmen.
2. SCCs, die nur aus einem Zustand bestehen, der kein Attraktor ist, werden in "SCC 0" verschoben.
> Ausgelagert nach TransitionSystem
3. uebergangsgraph vereinfachen > "SCCGraph":
    a) Vollwertige SCCs (also nicht SCC 0) werden zu einem Knoten zusammengefasst, der alle
       eingehenden und ausgehenden Kanten seiner Teilzustaende erhaelt.
       Der Graph besteht dann quasi aus SCCs und Zustaenden und natuerlich den Kanten dazwischen.
    b) Zustaende in SCC 0 eliminieren bzw. zu Kanten zwischen den SCCs vereinfachen.
       Eine Kante zwischen zwei SCCs besteht, wenn es einen Pfad zwischen den beiden SCCs gibt,
       der nicht durch andere SCCs fuehrt.
4. Layout fuer SCCGraph berechnen. Fuer n Attraktoren gibt es n+1 Ebene.
    a) Attraktoren auf Ebene 0 anordnen.
    b) Alle un-attraktiven SCCs mprit den erreichbaren Attraktoren labeln.
    c) Zustaende mit n erreichbaren Attraktoren auf Ebene n verschieben. Die Anordnung innerhalb einer
       Ebene entspricht der Anordnung der Attraktoren auf Ebene o.
       (Wenn auf Ebene 0 die Attraktoren 1, 2 und 3 liegen, dann ist die Anordnung auf Ebene 2
       [1,2]* [1,3]* [2,3]*     wobei in den eckigen Klammern die erreichbaren Attraktoren stehen.)

# TODO: Muss noch fertig beschrieben & kommentiert werden.
5. nested networks
6. Rueckgabe
    Zurueckgegeben wird ein dictionary. Je nachdem welche Flags beim Funktionsaufruf gesetzt wurden, sind
    darin folgende Eintraege enthalten:
    - In jedem Fall Eintrag "SCCDAG", der den networkx.DiGraph() mit den angeordneten SCCs enthaelt.
    - 2. Parameter==True: Eintrag "nested_networks_for_gml", der ein dictionary mit den networkx-Graphen fuer
      die Zustaende innerhalb der SCCs enthaelt. Dabei ist der key so gewaehlt, dass er dem Label des zugehoerigen
      SCCs im SCCDAG entspricht. Die Graphen sind "circular" angeordnet.
    - 3. Parameter==True: Eintrag "nested_networks_for_nnf", der einen String im NNF-Format enthaelt, welcher
      das nested network der SCCs mit den Zustaenden in ihnen repraesentiert.
"""






class SCCDAG() :

    def __init__(self, stg, attrs, sccs, destiny, compute_nested_networks_for_gml, compute_nested_networks_for_nnf, Isomorphy) :
        self._stg = stg
        self._attrs = attrs
        self._sccs = sccs
        self._Isomorphy = Isomorphy
        self._destiny = destiny
        self._compute_nested_networks_for_gml = compute_nested_networks_for_gml
        self._compute_nested_networks_for_nnf = compute_nested_networks_for_nnf
        self._nxSCCDAG = nx.DiGraph()
        self._gmlNN    = []    # nested networks als gml-Files
        self._nnfNN    = ''    # ~ als Nested Network File
        self._compute_SCCDAG()
        
    def getNxSCCDAG(self) :
        return self._nxSCCDAG
    
    def getGmlNN(self) :
        return self._gmlNN
    
    def getNnfNN(self) :
        return self._nnfNN

    # sortiert Attraktor-Dictionary um und gibt dictionary Knoten>Attraktor zurueck
    def _attractor_dict(self):
        node2attr={}
        # Liste durchgehen und fuer jeden Knoten den Attraktor speichern
        for (i,nodes) in enumerate(self._attrs):
            for node in nodes:
                node2attr[node]=i
    
        return node2attr

    
    
    # Berechnet Koordinaten fuer hierarchische Anordnung der Knoten in H. Attraktoren aus attrnodes werden dabei als Basis verwendet.
    # Gibt Koordinaten und erreichbare Attraktoren zurueck.
    def _lay_mobile(self,H,attrnodes):
        """ PRINZIP
        Das Layout soll wie folgt aufgebaut werden:
        Auf Ebene 0 befinden sich die Attraktoren.
        Auf Ebene 1 befinden sich alle SCCs, von denen aus man genau einen Attraktor erreichen kann.
        Auf Ebene 2 befinden sich alle SCCs, von denen aus man genau zwei Attraktoren erreiche kann usw.
        Insgesamt gibt es bei n Attraktoren also n+1 Ebene.
        
        Die Attraktoren auf Ebene 0 werden nach aufsteigendem Index sortiert.
        Die SCCs auf den anderen Ebenen werden nach den erreichbaren Attraktoren sortiert.
        Wenn auf Ebene 0 die Attraktoren 1, 2 und 3 liegen, dann ist die Anordnung auf Ebene 2
                [1,2]* [1,3]* [2,3]*
        wobei in den eckigen Klammern die erreichbaren Attraktoren stehen.
        """
    
        err_attr_liste={}
        # dictionary soll folgende Struktur erhalten:
        #    Ebene 0 > { Attraktor1 > [],
        #            Attraktor2 > [],
        #                Attraktor3 > [],
        #                ...},
        #    Ebene 1 > { SCC1 > [Attraktor1],
        #            SCC2 > [Attraktor1],
        #                SCC3 > [Attraktor3],
        #                ...},
        #    Ebene 2 > { SCC4 > [Attraktor1, Attraktor2],
        #                SCC5 > [Attraktor1, Attraktor3],
        #                ...},
    
        for i in range(0,len(attrnodes)+1): # Fuer alle moeglichen Ebenen
            err_attr_liste[i]={} # ein vorerst leeres dictionary eintragen.
    
        for node in H.nodes(): # Dann alle Knoten durchgehen.
            if node in attrnodes: # Wenn es sich um einen Attraktor handelt
                err_attr_liste[0][node]=[] # soll er sofort eingetragen werden.
            # In der Liste der erreichbaren Attraktoren wuerde eigentlich der Knoten/Attraktor selbst stehen, dann
            # wuerden Ebene 0 und 1 aber schlecht zu unterscheiden sein.
    
            else: # Fuer alle Nicht-Attraktoren
                erreichbar=nx.shortest_path(H,node) # werden also die erreichbaren Attraktoren/SCCs gesucht.
    
                err_attr=[] # Liste fuer erreichbare Attraktoren.
                for attr in attrnodes: # Dann wird fuer alle Attraktoren geprueft,
                    if attr in erreichbar: # ob sie in der Liste der erreichbaren Knoten sind.
                        err_attr.append(attr) # Und wenn ja, dann werden sie der Liste der erreichbaren Attraktoren hinzugefuegt.
    
                ebene=len(err_attr) # ueber die Anzahl der erreichbaren Attraktoren wird die Ebene berechnet.
                # Und der Knoten in der entsprechenden Ebene mit der Liste der erreichbaren Attraktoren gespeichert.
                err_attr_liste[ebene][node]=err_attr
    
    
        # Reihenfolge fuer 0. Ebene: Nach Attraktor-Id = key sortieren und Reihenfolge speichern.
        reihenfolge=sorted(err_attr_liste[0])
        
        lay={} # dictionary fuer Koordianten
        attr_strings={} # dictionary fuer String der erreichbaren Attraktoren
        for ebene in err_attr_liste.keys(): # Fuer jede Ebene
            for (i,node) in enumerate(reihenfolge): # alle Knoten in zuvor bestimmter Reihenfolge durchgehen.
                lay[node]={"x":i*100,"y":ebene*-100} # und x Koordinate nach Reihenfolge; y-Koordinate nach Ebene bestimmen.
                
                attr_string=""
                # Fuer alle erreichbaren Attraktoren:
                for attractor in err_attr_liste[ebene][node]:
                    if attr_string!="": attr_string+=", " # Komma anhaengen, wenn schon Attraktoren im String stehen
                    attr_string+=str(attractor) # Attraktor an String anhaengen
                attr_strings[node]=attr_string
    
            # Reihenfolge fuer die naechste Ebene bestimmen.
            # (Also nicht Ebene 0, weil Ebene 0 fuer keine Ebene die naechste ist.)
            reihenfolge=[]
            if ebene+1 in err_attr_liste: # (Und nur, wenn es noch eine weitere Ebene gibt.)
                # Fuer die Bestimmung der Reihenfolge wird nach der Liste der erreichbaren Attraktoren sortiert.
                items=err_attr_liste[ebene+1].items()
                items.sort(key=itemgetter(1))
                for it in items:
                    reihenfolge.append(it[0])
    
        return (lay,attr_strings)
    
    








    # Hauptfunktion
    def _compute_SCCDAG(self):
        """
        Attraktoren und SCCS umbenennen;
        - in sccs befinden sich triviale SCCs, die nur ein Element haben, welches kein Attraktor ist in SCC 0
        - in node2scc tauchen nur nicht-triviale SCCs auf
        """
        attractors=self._attractor_dict()
        node2scc=self._sccs[0] # Knoten>SCC
        scc2nodes=self._sccs[1] #SCC>[Knoten]


        """
        Einige Listen und dictionarys, die immer wieder gebraucht werden
        """
        # Liste fuer neue SCCs bzw. Attraktoren (nach 1. Vereinfachung)
        new_sccnodes=[]
        new_attrnodes=[]
        # Attribute
        node_attribute_size={}
        node_attribute_basin={}
        node_attribute_isoclass={}
        edge_lenght_attributes={}
        edge_probability_attributes={}



        """
        SCCs zu einem gemeinsamen Knoten zusammenfassen
        a) STG klonen, damit der Ausgangsgraph erhalten bleibt (SCCGraph1)
        b) Fuer jede nichttriviale SCC werden alle Vorgaenger und Nachfolger aller enthaltenen Knoten betrachtet.
        c) Alle Knoten (und damit implizit alle eingehenden und ausgehenden Kanten) der SCC werden geloescht.
        d) Neue Kanten von den Vorgaengern zum neuen Knoten und vom neuen Knoten zu den Nachfolgern werden hinzugefuegt. Name des neuen Knotens: "SCC IndexInSCCListe"
        
        Zwischendurch: Isoclass-, Basin- und Size-Attribute schreiben.
        """


        # a)
        SCCGraph1=nx.DiGraph()
        for edge in self._stg.edges():
            SCCGraph1.add_edge(edge[0],edge[1])


        isoclasses=[]


        for id in scc2nodes.keys():
            if id!=0:

                """
                ISOCLASS
                Fuer jede SCC Liste der bereits vorhanden Iscoclasses durchgehen.
                Wenn mit Muster-Subgraph Isometrie besteht: SCC zur Isoclass hinzufuegen.
                Wenn keine Isoclass gefunden werden konnte: Neue erstellen und aktuelle SCC als Muster merken.
                """
                if self._Isomorphy:
                    in_isoclass=False
                    for (key,muster) in enumerate(isoclasses):
                        G=self._stg.subgraph(scc2nodes[muster])
                        H=self._stg.subgraph(scc2nodes[id])
                        if nx.is_isomorphic(G,H):
                            in_isoclass=True
                            node_attribute_isoclass["SCC "+str(id)]=key
                            break
                    if not in_isoclass:
                        isoclasses.append(id)
                        node_attribute_isoclass["SCC "+str(id)]=isoclasses.index(id)

                """
                SIZE
                """
                node_attribute_size["SCC "+str(id)]=len(scc2nodes[id])



                pres=[] # Vorgaenger fuer aktuelle SCC
                succs=[] # Nachfolger ~
                is_attractor=False # Merken, ob SCC Attraktor-Knoten beinhaltet


                for node in scc2nodes[id]:
                    if node in attractors: is_attractor=True

                    # b)
                    pres+=SCCGraph1.predecessors(node)
                    succs+=SCCGraph1.successors(node)
                    
                    # c)
                    SCCGraph1.remove_node(node)
                    if node in pres: pres.remove(node)
                    if node in succs: succs.remove(node)

                # d)
                SCCGraph1.add_node("SCC "+str(id))
                for pre in pres:
                    SCCGraph1.add_edge(pre,"SCC "+str(id))
                for succ in succs:
                    SCCGraph1.add_edge("SCC "+str(id),succ)


                """
                Fuer spaeter merken, welche der neuen Knoten Attraktoren bzw. SCCs sind.
                BASIN: Wenn SCC Attraktor beinhaltet: Anzahl der Zustaende, deren destiny genau die SCC ist
                """
                new_sccnodes.append("SCC "+str(id))
                if is_attractor==True:
                    new_attrnodes.append("SCC "+str(id))
                    node_attribute_basin["SCC "+str(id)]=len([x for x in self._destiny if self._destiny[x]==[attractors[node]]])
                else:
                    node_attribute_basin["SCC "+str(id)]=0





        """
        Zustaende aus SCC 0 eliminieren und zu Kanten zwischen SCCs vereinfachen
       GEDANKE
        Graph besteht jetzt, bildlich gesprochen, aus "grossen SCCs", "kleinen Zustaenden" (-> SCC 0) und den Kanten dazwischen.
        Um ihn noch uebersichtlicher zu gestalten sollen die Kanten zwischen den Zustaenden und zwischen SCC und Zustand in Kanten
        zwischen SCCs aufgeloest werden. Dabei "verschwinden" die Zustaende aus SCC 0.
        
        PRINZIP
        Leeren Graph erstellen (SCCGraph2).
        Ausgehend von jedem moeglichen SCC:
            - a) RekursionsAnfang: direkte Nachfolger in Liste der zu durchsuchenden Knoten speichern
            - b) RekursionsAnker: So lange zu durchsuchende Knoten vorhanden
                c) einen Knoten als durchsucht merken
                pruefen, ob Knoten in SCC 0 oder nicht
                - d) wenn nein: Kante zwischen AusgangsSCC und anderem SCC hinzufuegen
                - e) wenn ja: Nachfolger zum Durchsuchen merken, wenn nicht bereits durchsucht

        Zwischendurch: edgeLength-Attribute schreiben.
            x) Knoten, die gerade ausserhalb des Start-SCCs liegen haben Pfadlaenge 1.
            y) Wenn die Nachfolger eines Knotens a betrachtet werden, ist die Pfadlaenge zu ihnen die von a+1.
        """


        SCCGraph2=nx.DiGraph()

        for start_scc in new_sccnodes:
            SCCGraph2.add_node(start_scc)
            path_length={} # von start_scc ausgehende Pfadlaengen


            done=[] # bereits besuchte Knoten
            done.append(start_scc)

            todo=[] # Knoten, die noch besucht werden muessen
            for edge in nx.edges(SCCGraph1,start_scc):
                todo.append(edge[1]) # a) RAnfang: direkte Nachfolger zum Besuchen vormerken
                path_length[edge[1]]=1 # x)


            while len(todo)>0: # b) RAnker
                if todo[0] not in done:

                    new_path_length=path_length[todo[0]]+1 # y)

                    done.append(todo[0]) # c)

                    if todo[0] in new_sccnodes: # Nichttriviale SCC?
                        # d)
                        SCCGraph2.add_edge(start_scc,todo[0])
                        edge_lenght_attributes[(start_scc,todo[0])]=new_path_length-1
                        if (start_scc,todo[0]) not in edge_probability_attributes:
                            edge_probability_attributes[(start_scc,todo[0])]=0
                        edge_probability_attributes[(start_scc,todo[0])]+=1

                    else:
                        # e) Nachfolger zum Durchsuchen merken
                        for edge in nx.edges(SCCGraph1,todo[0]):
                            if (edge[1] not in done) and (edge[1] not in todo):
                                todo.append(edge[1])
                                
                                # Pfadlaenge zwischen SCC und Zustand speichern
                                if edge[1] not in path_length:
                                    path_length[edge[1]]=new_path_length

                todo.remove(todo[0]) # c)


        """
        Layout und erreichbare Attraktoren berechnen
        """
        foo=self._lay_mobile(SCCGraph2,new_attrnodes) # erzeugt dictionary Knoten>Koordianten und Knoten>Label
        lay=foo[0] # Knoten>{"x":x-Koordinate,"y":y-Koordiante}
        erreichbare_attrs=foo[1] # Knoten>erreichbare Attraktoren als String



        """
        Nested Networks: Je nachdem, ob Flags gesetzt sind...
        a) GML
            i) Fuer alle SCCs den Teilgraph auf zugehoerigen Zustaenden waehlen.
            ii) Labels verteilen.
            iii) circular_layout anwenden.
            Rueckgabe als Liste von nx.Digraphs
        b) NNF
            SCCs durchgehen und jeweils
            i) als Knoten in Haupt-Graph eintragen
            ii) nested Teilgraph waehlen und dessen Kanten in Untergraph eintragen
            iii) Kanten des SCCs eintragen
            Rueckgabe als String, der in (.nnf-)Datei geschrieben werden kann
        """
        # a)
        if self._compute_nested_networks_for_gml==True:
            nested_networks={}
            for id in scc2nodes.keys():
                if id!=0:
                    # i)
                    nested_networks["SCC "+str(id)]=self._stg.subgraph(scc2nodes[id])

                    # ii)
                    labels={}
                    for node in nested_networks["SCC "+str(id)].nodes():
                        labels[node]=str(node)
                    nx.set_node_attributes(nested_networks["SCC "+str(id)],"label",labels)

                    # iii)
                    sub_lay=nx.circular_layout(nested_networks["SCC "+str(id)],scale=100)
                    for node in sub_lay:
                        sub_lay[node]={"x":sub_lay[node][0],"y":sub_lay[node][1]}
                    nx.set_node_attributes(nested_networks["SCC "+str(id)],"graphics",sub_lay)

            # iiii)
            self._gmlNN=nested_networks

        # b)
        if self._compute_nested_networks_for_nnf==True:
            string_sccnodes=""
            string_nestedgraphs=""
            string_edges_between_sccs=""
            for id in scc2nodes.keys():
                if id!=0:
                    # i)
                    string_sccnodes+="SCCDAG    SCC"+str(id)+"\n"

                    # ii)
                    sccnodes=self._stg.subgraph(scc2nodes[id])
                    for edge in sccnodes.edges():
                        string_nestedgraphs+="SCC"+str(id)+"    "+str(edge[0])+"    pp    "+str(edge[1])+"\n"

            # iii)
            for edge in SCCGraph2.edges():
                string_edges_between_sccs+="SCCDAG    "+str(edge[0]).replace(" ","")+"    im    "+str(edge[1]).replace(" ","")+"\n" # TODO: im???

            self._nnfNN=string_sccnodes+string_nestedgraphs+string_edges_between_sccs



        """
        a) Attribut Label schreiben
        b) Attribute zuweisen
        c) "Rueckgabe"
        """
        # a)
        node_attribute_labels={}
        for node in SCCGraph2.nodes():
            if node in new_attrnodes: node_attribute_labels[node]="A / "+str(node)
            else: node_attribute_labels[node]=str(node)

        nx.set_node_attributes(SCCGraph2,"graphics",lay)
        nx.set_node_attributes(SCCGraph2,"accessibleAttractors",erreichbare_attrs)
        nx.set_node_attributes(SCCGraph2,"size",node_attribute_size)
        if self._Isomorphy: nx.set_node_attributes(SCCGraph2,"isoclass",node_attribute_isoclass)
        nx.set_edge_attributes(SCCGraph2,"edgeLength",edge_lenght_attributes)
        nx.set_edge_attributes(SCCGraph2,"probability",edge_probability_attributes)
        nx.set_node_attributes(SCCGraph2,"label",node_attribute_labels)
        nx.set_node_attributes(SCCGraph2,"basin",node_attribute_basin)

        self._nxSCCDAG=SCCGraph2
