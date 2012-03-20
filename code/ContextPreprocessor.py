# -*- coding: utf-8 -*-

def list_condition(name, inclusion=True):
    if inclusion:
        return lambda context: name in context
    return lambda context: name not in context

def ineq_condition(barrier, increasing = True):
    if increasing:
        return lambda x: x >= barrier
    return lambda x: x <= barrier

class Preprocessor():
    '''
    (1) Computes for each component the subset of contexts, it may be in while on
        the monotone path from s1 to s2. If no variable is specified to be monotone this
        will be the whole set.
    (2) Checks for each component, if it can reach its target in s2, i.e. if there
        is a context among the subset of contexts, so that the parameter value is
        on the right side of the target.

    return:
        If not the variable is returned and whether it is too low or to high.
        Otherwise False is returned.
    
    :param mc: ModelContainer. Requires: predecessors, contexts, threshold
    :param s1,s2: States.
    :param mon: Monotonicity specifications.
    :type mc: ModelContainer.
    :type s1,s2: dict(string:value)
    :type mon: dict(string:bool)
    '''

    def __init__(self, mc, s1, s2, mon):
        self.varnames = mc.varnames()
        self.contexts = mc.contexts
        
        direction = {}
        constraints = dict([(n,[]) for n in self.varnames])
        #1. Richtungs- und Kontextbedingungen aufbauen
        for name in s1:
            # 1.1 Richtungsbedingung: Entweder die Messungen stimmen überein (es können keine Bedingungen an die Parameterwerte gestellt werden)..
            if s1[name]==s2[name]:
                pass
            else:
                # festhalten, in welche Richtung 'name' seine Aktivität ändern muss
                direction[name] = ineq_condition(barrier=s2[name], increasing= s2[name]>s1[name])

            if mon[name]:
                # 1.2 Kontextbedingungen für die Nachfolger von 'name'
                for suc in mc.successors(name):
                    Min = min(s1[name],s2[name])
                    Max = max(s1[name],s2[name])
                    T = mc.threshold(name,suc)
                    if T > Min:
                        if T > Max:
                            # ..'name' muss im Kontext dieser Nachfolger fehlen, da T>MAX
                            constraints[suc].append(list_condition(name, False))
                    else:
                        # ..'name' muss im Kontext dieser Nachfolger enthalten sein, da T<MIN
                        constraints[suc].append(list_condition(name))

        #2. Kontext-Teilmenge berechnen
        contexts = {}
        for name in self.varnames:
            contexts[name] = []
            for context in mc.contexts(name):
                if all([constraint(context) for constraint in constraints[name]]):
                    contexts[name].append(context)

        self.direction = direction
        self.contexts = contexts
        self.constraints = constraints

    def find_problem_names(self, pset):
        #3. Prüfen oder es einem Parameterwert gibt, der auf der richtigen Seite des Messwerts s2 liegt.
        problem_names = []
        for name in self.varnames:
            if self.direction.has_key(name):
                problem = True
                for context in self.contexts[name]:
                    if self.direction[name](pset[name][context]):
                        problem = False
                        break
                if problem:
                    problem_names.append(name)
        return problem_names
                        
                    
    

if __name__=='__main__':
    print 'Nichts zu tun..'
    











            
