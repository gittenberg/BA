# -*- coding: cp1252 -*-
def evaluate(expression,TS,subsets="all",operator_ordering="standard",heuristic=True,preprocessing = False):
    """
    Parses a string expression and returns whether it is True or False for a given SCC
    Pseudocode:
    if the expression is surrounded by simple brackets, evaluate the expression without them. ev("(a)")=ev("a")
    if the expression is surrounded by a quantor, evaluate it for given subsets of attractors, until it is True or return False.
        Using EXISTD(x1,x2,...,xn):a) means, that for pairwise xi,xj xi!=xj
        ev("EXISTD(x1,x2,...,xn):a)",(y1:a1,y2:a2,...ym:am))=ev(a,(x1€{y1,...ym},x2€{y1,...ym}\{x1},...xn€{y1,...,ym}\{x1,x2,...xn-1})) joining the possibilities with or
        Using EXISTI allows the case, that parts of the xi,xj are identical.
        ev("EXISTI(x1,x2,...,xn):a)",(y1:a1,y2:a2,...ym:am))=ev(a,(x1€values({y1,...ym}),x2€values){y1,...ym}),...xn€values({y1,...,ym}))) joining the possibilities with or
        If there is used an EXIST-statement 1 within another EXIST-statement 2, the subset of attractors of statement 1 is chosen only out of attractors from statement 2.
        ev("FORALL(x1:a)",(y1:a1,y2:a2,...ym:am) = ev("a",x1€{y1,...ym}) joining the possibilities with and.
    for all operators (and, or etc...) in sorted by increasing bindung power:
        split the expression at the given operator symbols, ignoring those, that are in between brackets.
        if the list is longer than 1:
            reduce the list splitted and recursively evaluated objects using the given operator and return the boolean value.
        else:
            continue
    evaluate the remaining simple expression and return it
    """
    if preprocessing:
        expression = expression.replace(" ","")
    if operator_ordering == "standard":
        #Define infix-operator symbols and functions:
        equivalence_operator = ("<=>", lambda x,y: (x and next(y)) or not(x or next(y)))
        implication_operator = ("->", lambda x,y: not x or next(y))
        or_operator = ("|", lambda x,y: x or next(y))
        and_operator = ("&", lambda x,y: x and next(y))
        #Define ordering with increasing binding power:
        operator_ordering = [equivalence_operator, implication_operator, or_operator, and_operator]
        
    #Split at given infix-operators with increasing binding power:
    for operator in operator_ordering:
        splitted_list = split_no_brackets(expression,operator[0])
        if len(splitted_list)>1:

            #Help-function evaluated_reduce
            def evaluated_reduce(initial,elementlist,operator):
                """Lazily evaluates the initial value and uses this and, if necessary, the remaining evaluated_reduced list, as arguments for the operator"""
                if elementlist == []:
                    yield evaluate(initial,TS,subsets,operator_ordering)
                if len(elementlist)==1:
                    result = operator(evaluate(initial,TS,subsets,operator_ordering),evaluated_reduce(elementlist[0],[],operator))
                    yield result
                else:
                    result = operator(evaluate(initial,TS,subsets,operator_ordering),evaluated_reduce(elementlist[0],elementlist[1:],operator))
                    yield result
            #End of help-function

            if heuristic and (operator[0] == "&" or operator[0] == "|"):
                splitted_list.sort(key=lambda x:len(x)+10*x.count("?"))
                
            return next(evaluated_reduce(splitted_list[0],splitted_list[1:],operator[1]))

    #Check for unneccessary brackets
    if expression[0] == "(" and expression[-1] == ")":
        #ModelContainer.message("Reading brackets...")
        return evaluate(expression[1:-1],TS,subsets,operator_ordering)

    #Check for quantors with mutually exclusive constructors
    if expression[0:2] == "?(" and expression[-1] == ")":
        colonpos = expression.find(":")
        attractornames = expression[2:colonpos].split(",")
        subset_found=False
        import itertools as IT
        if subsets=="all":
            old_values=range(len(TS.getAttrInfos()))
        else:
            old_values=subsets.values()
        if len(old_values)<len(attractornames):
            #print "Warning: Expression was rejected, because at \n\
            #?("+",".join(attractornames)+":...)\n\
            #the number of given attractors was greater than the total number of considered attractors."
            return False
        for choice in IT.permutations(old_values,len(attractornames)):
            newsubsets = dict(zip(attractornames,choice))
            #print newsubsets
            subset_found= evaluate(expression[colonpos+1:-1],TS,newsubsets,operator_ordering,heuristic)
            if subset_found:
                break
        return subset_found
    #Check for quantors with potentially equal constructors
    if expression[0:2] == "$(" and expression[-1] == ")":
        colonpos = expression.find(":")
        attractornames = expression[2:colonpos].split(",")
        subset_found=False
        import itertools as IT
        if subsets=="all":
            old_values=range(len(TS.getAttrInfos()))
        else:
            old_values=subsets.values()
        if len(old_values)<len(attractornames):
            #print "Warning: Expression was rejected, because at \n\
            #?("+",".join(attractornames)+":...)\n\
            #the number of given attractors was greater than the total number of considered attractors."
            return False
        for choice in IT.combinations_with_replacement(old_values,len(attractornames)):
            newsubsets = dict(zip(attractornames,choice))
            #print newsubsets
            subset_found= evaluate(expression[colonpos+1:-1],TS,newsubsets,operator_ordering,heuristic)
            if subset_found:
                break
        return subset_found

    
    #Check for negations
    if expression[0] == "!":
        return not evaluate(expression[1:],TS,subsets,operator_ordering)

    #Evaluating simple expressions about TS-properties
    import re

    expression = re.sub("\(","(\"",expression)
    expression = re.sub("\)","\")",expression)
    expression = re.sub("size","size()",expression)
    expression = re.sub("#A","TS.attrs()",expression)
    expression = re.sub("#F","TS.fixpoints()",expression)
    expression = re.sub("#C","TS.cAttrs()",expression)
    expression = re.sub("([^=<>!])=([^=])",lambda x:x.group(1)+"=="+x.group(2),expression)
    expression = re.sub("frozen","isFrozen",expression)
    expression = re.sub("min","minValue",expression)
    expression = re.sub("max","maxValue",expression)
    if type(subsets)==dict:
        for (attractorname,index) in subsets.items():
            expression = expression.replace(attractorname,"TS.getAttrInfos()["+str(index)+"]")
    
    return eval(expression)

def check(expression,operator_ordering="standard",heuristic=True,preprocessing = False):
    """Returns True, if the syntax of expression is correct, not considering whether the statement semantically makes sense or not.
    Returns a string with the exception, if the syntax is incorrect."""
    try:
        TS = dummyTS()
        result = evaltest(expression,TS,subsets="all",operator_ordering=operator_ordering,heuristic=heuristic, preprocessing=preprocessing)
        if type(result)==bool:
            return True
        else:
            return "Exception: The expression does not result in a boolean value."
    except Exception,e:
        return e

def evaltest(expression,TS,subsets="all",operator_ordering="standard",heuristic=True,preprocessing = False):
    """
    In principle does the same like evaluate, but does not need valid attractors in the Transitionsystem.
    Used for testing, whether the syntax, not considering an actual model, is correct.
    For pseudocode compare with evaluate.
    """
    if preprocessing:
        expression = expression.replace(" ","")
    if operator_ordering == "standard":
        #Define infix-operator symbols and functions:
        equivalence_operator = ("<=>", lambda x,y: (x and next(y)) or not(x or next(y)))
        implication_operator = ("->", lambda x,y: not x or next(y))
        or_operator = ("|", lambda x,y: x or next(y))
        and_operator = ("&", lambda x,y: x and next(y))
        #Define ordering with increasing binding power:
        operator_ordering = [equivalence_operator, implication_operator, or_operator, and_operator]
        
    #Split at given infix-operators with increasing binding power:
    for operator in operator_ordering:
        splitted_list = split_no_brackets(expression,operator[0])
        if len(splitted_list)>1:

            #Help-function evaluated_reduce
            def evaluated_reduce(initial,elementlist,operator):
                """Lazily evaluates the initial value and uses this and, if necessary, the remaining evaluated_reduced list, as arguments for the operator"""
                if elementlist == []:
                    yield evaltest(initial,TS,subsets,operator_ordering)
                if len(elementlist)==1:
                    result = operator(evaltest(initial,TS,subsets,operator_ordering),evaluated_reduce(elementlist[0],[],operator))
                    yield result
                else:
                    result = operator(evaltest(initial,TS,subsets,operator_ordering),evaluated_reduce(elementlist[0],elementlist[1:],operator))
                    yield result
            #End of help-function

            if heuristic and (operator[0] == "&" or operator[0] == "|"):
                splitted_list.sort(key=lambda x:len(x)+10*x.count("?"))
                
            return next(evaluated_reduce(splitted_list[0],splitted_list[1:],operator[1]))

    #Check for unneccessary brackets
    if expression[0] == "(" and expression[-1] == ")":
        #ModelContainer.message("Reading brackets...")
        return evaltest(expression[1:-1],TS,subsets,operator_ordering)

    #Check for quantors
    if (expression[0:2] == "?(" or expression[0:2] == "$(" ) and expression[-1] == ")":
        colonpos = expression.find(":")
        attractornames = expression[2:colonpos].split(",")
        subset_found=False
        import itertools as IT
        
        if not subsets=="all" and len(subsets)<len(attractornames):
            print "Warning: AL expression will reject all models, because at \n\
            ?("+",".join(attractornames)+":...)\n\
            the number of given attractors was greater than the total number of considered attractors."
        
        newsubsets = dict(zip(attractornames,[0]*len(attractornames)))
        #print newsubsets
        return evaltest(expression[colonpos+1:-1],TS,newsubsets,operator_ordering,heuristic)


    #Check for negations
    if expression[0] == "!":
        return not evaltest(expression[1:],TS,subsets,operator_ordering)

    #Evaluating simple expressions about TS-properties
    import re
    unmodified_expression = expression
    expression = re.sub("\(","(\"",expression)
    expression = re.sub("\)","\")",expression)
    expression = re.sub("size","size()",expression)
    expression = re.sub("#A","TS.attrs()",expression)
    expression = re.sub("#F","TS.fixpoints()",expression)
    expression = re.sub("#C","TS.cAttrs()",expression)
    expression = re.sub("([^=<>!])=([^=])",lambda x:x.group(1)+"=="+x.group(2),expression)
    expression = re.sub("frozen","isFrozen",expression)
    expression = re.sub("min","minValue",expression)
    expression = re.sub("max","maxValue",expression)
    if type(subsets)==dict:
        for (attractorname,index) in subsets.items():
            expression = expression.replace(attractorname,"TS.getAttrInfos()["+str(index)+"]")
    if type(eval(expression))==bool:
        return True
    else:
        raise Exception("Exception: "+unmodified_expression + " is not a boolean expression.")

def split_no_brackets(expression,splitter):
    """Splits expression at the symbols splitter, if they are not within brackets, and returns a list of the splitted elements"""
    open_brackets=[]
    for i in range(len(expression)):
        if expression[i] == "(":
            open_brackets.append("(")
        if expression[i] == ")":
            if open_brackets.pop()!="(":
                raise Exception("Parse Error of AL-expression: unexpected \')', unbalanced bracketing.")
        if open_brackets== [] and expression[i:i+len(splitter)] == splitter:
            return [expression[:i]]+split_no_brackets(expression[i+len(splitter):],splitter)
    if open_brackets != []:
        raise Exception("Parse Error of AL-expression: unbalanced bracketing")
    else:
        return [expression]

class dummyAttrInfo() :
    def _init():
        pass
    def isFrozen(self, var) :
        return True
    def maxValue(self, var) :
        return 0
    def minValue(self, var) :
        return 0
    def size(self) :
        return 0

class dummyTS() :
    def _init():
        pass
    def attrs(self):
        return 0
    def fixpoints(self):
        return 0
    def cAttrs(self):
        return 0
    def getAttrInfos(self):
        return [dummyAttrInfo()]

