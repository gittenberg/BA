import networkx as nx



class DestinySTG() :

    def __init__(self, stg, attrs, sccs, destiny) :
        self._stg = stg
        self._attrs = attrs
        self._sccs = sccs
        self._destiny = destiny

    def better_scc_names(self) :
        better={}
        attr2scc={}

        for scc_id in self._sccs[1].keys():
            is_attractor=False
            nodes_in_scc=self._sccs[1][scc_id]
            for node_in_scc in nodes_in_scc:
                for (attr_id,nodes_in_attr) in enumerate(self._attrs):
                    if node_in_scc in nodes_in_attr:
                        is_attractor=True
                        attr2scc[attr_id]=scc_id
                        break

            if is_attractor:
                if len(self._sccs[1][scc_id])==1:
                    better[scc_id]="F "+str(scc_id)
                else:
                    better[scc_id]="A "+str(scc_id)
            else:
                better[scc_id]=str(scc_id)

        return (better,attr2scc)

    def getDestinySTG(self) :
        destinySTG=self._stg.copy()
        node_attribute_destiny={}
        node_attribute_scc={}
        node_attribute_label={}

        (betterSCCNames,attr2scc)=self.better_scc_names()
        for node in destinySTG:
            string=""
            for dest_attr in self._destiny[node]:
                if string!="":
                    string+=", "
                string+=betterSCCNames[attr2scc[dest_attr]]
            node_attribute_destiny[node]=string

            if node in self._sccs[0]:
                node_attribute_scc[node]=betterSCCNames[self._sccs[0][node]]
            else:
                node_attribute_scc[node]="0"

            node_attribute_label[node]=str(node)

        nx.set_node_attributes(destinySTG,"destiny",node_attribute_destiny)
        nx.set_node_attributes(destinySTG,"SCCID",node_attribute_scc)
        nx.set_node_attributes(destinySTG,"label",node_attribute_label)
        return destinySTG
