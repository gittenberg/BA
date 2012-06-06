def generate_smv(container, parameterSet, formula=None):
    """Creates a Model written in NuSMV language from a set of parameters K"""
    priorityClasses = container._priorityClasses
    priorityTypes = container._priorityTypes
    dynamics = container._dynamics
    unitary = container._unitary
    
    if dynamics == "asynchronous":
        #priorityClasses = {1:reduce(lambda x,y: x+y,priorityClasses.values())}
        priorityClasses = {1:container.varnames()}
        priorityTypes = {1:"asynchronous"}
    elif dynamics == "synchronous":
        #priorityClasses = {1:reduce(lambda x,y: x+y,priorityClasses.values())}
        priorityClasses = {1:container.varnames()}
        priorityTypes = {1:"synchronous"}
    if unitary:
        step="sign"
    else:
        step="difference"
        
    def writesynblock(varnamelist,priority,tabs=1):
        #Writes the assignments for all varnames of a synchronous priorityClass
        result=""
        for varname in varnamelist:
            result+="\t"*tabs+"next("+varname+") := \n"
            result+="\t"*(tabs+1)+"case\n"
            result+="\t"*(tabs+1)+"class = "+str(priority)+ " : "+varname+" + "+varname+step+";\n"
            result+="\t"*(tabs+1)+"TRUE : "+varname+";\n"
            #in case this is the priorityClass, in which changes occur, each varname is changed by varnamedifference/varnamesign, otherwise it doesnt change.
            result+="\t"*(tabs+1)+"esac;\n"
        return result    

    def writeasynblock(varnamelist,priority,tabs=1):
        #Writes the assignments for all varnames of a asynchronous priorityClass
        result=""
        for i in range(len(varnamelist)):
            result+="\t"*tabs+"next("+varnamelist[i]+") := \n"
            result+="\t"*(tabs+1)+"case\n"
            if i==len(varnamelist)-1:
                result+="\t"*(tabs+1)+"class = "+str(priority)+(varnamelist[:i] and "&" or "")+"&".join([" next("+varname2+") = "+varname2 for varname2 in varnamelist[:i]])+" : "+varnamelist[i]+" + "+varnamelist[i]+step+";\n"
            else:
                result+="\t"*(tabs+1)+"class = "+str(priority)+(varnamelist[:i] and "&" or "")+"&".join([" next("+varname2+") = "+varname2 for varname2 in varnamelist[:i]])+" : {"+varnamelist[i]+", "+varnamelist[i]+" + "+varnamelist[i]+step+"};\n"
            result+="\t"*(tabs+1)+"TRUE : "+varnamelist[i]+";\n"
            #in case this is the priorityClass, in which changes occur, each varname can change by varnamedifference/sign, if no of the other varnames changed, otherwise it doesnt change.
            result+="\t"*(tabs+1)+"esac;\n"
        return result
        
    def getclass(priorityClasses): #Creates the string, that determines, in which priorityClass changes occur
        #A change occurs in priorityClass with priority n, iff there exists no priorityclass with priority m<n, in which changes can occur.
        return "&".join([varname2+step+"=0" for varname2 in priorityClasses[0][1]])+"?"+(len(priorityClasses)!=1 and getclass(priorityClasses[1:]) or "0")+":"+str(priorityClasses[0][0])
        

    output=""
    output+="MODULE main\n" #Writes MODULE

    output+="\nDEFINE\n" #Writes DEFINE section

    for varname in container.varnames(): #Set images, differences and signs as variables for each varname
        output += "\t"+varname+"image := \n\t\tcase\n" #Inserts a case selection for the assigning of values
        for context in sorted(container.contexts(varname),key=lambda x: len(x),reverse=True): #Distinguishes between different contexts,
            #sorted by their length, so that the more strong context is always chosen first
            if context:
                output += "\t\t\t" + "&".join([varname2+">="+str(container.threshold(varname2,varname)) for varname2 in context])
            else:
                output += "\t\t\tTRUE "
            #Writes the boolean condition that all varnames of the context are over their threshold
            output += ": " + str(parameterSet[varname][context]) + ";\n"
        output += "\t\tesac;\n"
        output += "\t" + varname + "difference := " + varname + "image" + " - " +  varname +";\n" #Sets the variable varnamedifference to the difference of image and current state for each varname
        output += "\t" + varname + "sign := " + varname + "difference" + " > 0 ? 1 : " + varname + "difference" + " < 0 ? -1 : 0;\n\n" #Sets the variable varnamesign to the algebraic sign of varnamedifference
    output += "\tclass := " + getclass(sorted(priorityClasses.items(),key=lambda x:x[0])) + ";\n"           

    output += "\nVAR\n"
    for varname in container.varnames(): #For each varname set its range
        output += "\t"+ varname + " : " + "0" + ".." + str(container.varMax([varname][0])) + ";\n"
        #Test without variableMax: output += "\t" + varname + " : " + str(0) + ".." + str(1) + ";\n"
    output += "\nASSIGN\n"
    for pC in sorted(priorityClasses.items(),key=lambda x: x[0]): #For each priorityClass write a new block, depending on whether the priorityClass is synchronous or asynchronous
        #print pC[0]
        if priorityTypes[pC[0]]=="synchronous":
            output+= writesynblock( pC[1], pC[0] )
        elif priorityTypes[pC[0]]=="asynchronous":
            output+=writeasynblock( pC[1], pC[0] )

    if formula: output += "CTLSPEC "+formula
    
##                                                                                                    
##    output += "\nTRANS\n"
##    output += "\t" + " + ".join(["(next("+varname+")-"+varname+")*(next("+varname+")-"+varname+")" for varname in container.varnames()])
##    output += " = 1;\n"
##    
    return output

def generate_pm(container, parameterSet):
    """
    Creates a Model written in Prism language from a set of parameters K

    parameters:
    --container: choose container (see python module parameterSetContainer for details) to be converted
    --parameterSet: choose a set of parameters to be used for conversion
    --filename: specify the name of the output file
    --priorityClasses: a dictionary including all priority classes as keys, each with varnames included in that class as value
    --priorityTypes: a dictionary including all priority classes as keys, each with its destined dynamics mode as value (possibilities: "synchronous","asynchronous")
    --dynamics: sets the preferred dynamics mode, options are "syn" for synchronous and "asyn" for asynchronous behavior and "priorityClasses" for the use of priority classes
    --unitary: unitary behavior will be used if unitary is set to "True", else the behavior will be non-unitary
    """

    dynamics = container._dynamics
    priorityClasses = container._priorityClasses
    priorityTypes = container._priorityTypes
    dynamics = container._dynamics
    unitary = container._unitary
    
    if dynamics == "asynchronous":
        #use one single priority class which includes all varnames
        priorityClasses = {1:container.varnames()}
        priorityTypes = {1:"asynchronous"}
    elif dynamics == "synchronous":
        priorityClasses = {1:container.varnames()}
        priorityTypes = {1:"synchronous"}
    if unitary:
        step="sign"
    else:
        step="difference"

    def writesynblock(varnamelist,priority,tabs=1):
        #Writes the assignments for all varnames of a synchronous priorityClass
        result="\t"*tabs+"[] class="+str(priority)+" -> "+"&".join(["("+varname2+"'="+varname2+"+"+varname2+step+")" for varname2 in varnamelist])+";\n"
        return result    

    def writeasynblock(varnamelist,priority,tabs=1):
        #Writes the assignments for all varnames of a asynchronous priorityClass
        result=""
        for i in range(len(varnamelist)):
            result+="\t"*tabs+"[] "+varnamelist[i]+step+"!=0&class="+str(priority)+" -> ("+varnamelist[i]+"'="+varnamelist[i]+"+"+varnamelist[i]+step+");\n"
        return result
        
    def getclass(priorityClasses): #Creates the string, that determines, in which priorityClass changes occur
        #A change occurs in priorityClass with priority n, if there exists no priorityclass with priority m<n, in which changes can occur.
        try:
            return "&".join([varname2+step+"=0" for varname2 in priorityClasses[0][1]])+"?"+(len(priorityClasses)!=1 and getclass(priorityClasses[1:]) or "0")+":"+str(priorityClasses[0][0])
        except:
            print("error on",priorityClasses)
            
    output=""
    #print("parameterset="+str(parameterSet)+"\npriorityClasses="+str(priorityClasses)+"\npriorityTypes="+str(priorityTypes)+"\ndynamics="+str(dynamics)+"\nunitary="+str(unitary)+"\n"+"IG="+str(container.get_IG())+"\n\n")
    #print("Parameterset:",parameterSet)
    #print("PriorityClasses:",priorityClasses)
    #print("PriorityTypes:",priorityTypes)
    #print("Dynamics:",dynamics)
    #print("Unitary:",unitary)
    #print("IG:",container.get_IG())
    
    output+="dtmc\n" #Writes dtmc

    for varname in container.varnames(): #Set images, differences and signs as variables for each varname
        output += "formula "+varname+"image = " 
        for context in sorted(container.contexts(varname),key=lambda x: len(x),reverse=True): #Distinguishes between different contexts,
            #sorted by their length, so that the stronger context is always chosen first
            if context:
                output += "&".join([varname2+">="+str(container.threshold([varname2,varname])) for varname2 in context])+"?"+str(parameterSet[varname][context])+":"
            #Writes the boolean condition that all varnames of the context are over their threshold
        output += str(parameterSet[varname][tuple()])+";\n"
        output += "formula " + varname + "difference = " + varname + "image" + " - " +  varname +";\n" #Sets the variable varnamedifference to the difference of image and current state for each varname
        output += "formula " + varname + "sign = " + varname + "difference" + ">0?1:" + varname + "difference" + "<0?-1:0;\n\n" #Sets the variable varnamesign to the algebraic sign of varnamedifference
    output += "formula class = " + getclass(sorted(priorityClasses.items(),key=lambda x:x[0])) + ";\n"           

    output += "\nmodule Main\n"
    for varname in container.varnames(): #For each varname set its range
        output+="\t"+varname+": [0.."+str(container.varMax([varname][0]))+"];\n"

    output+="\n"
    for pC in sorted(priorityClasses.items(),key=lambda x: x[0]): #For each priorityClass write a new block, depending on whether the priorityClass is synchronous or asynchronous
        if priorityTypes[pC[0]]=="synchronous":
            output+= writesynblock( pC[1], pC[0] )
        else:
            output+=writeasynblock( pC[1], pC[0] )                                                                        
    output+="endmodule"
    return output

def test_NuSMVpath(NuSMVpath):
    """
    Tests, whether the NuSMV located in NuSMVpath is working.
    Returns a dictionary with the following items:

    working_version: Boolean Value, whether NuSMV evaluates a model as is true, that has been validated
    as true by the version of NuSMV we used during the development of this software.

    version: String of the version of NuSMV installed in NuSMVpath
    output: The output of the cmd, when trieing to use NuSMV on the given model.
    """
    import imp
    import os
    import sys
    import subprocess as SP
    smv_string = \
    """MODULE main

DEFINE
	VAimage := 
		case
			VB>=1: 1;
			TRUE : 1;
		esac;
	VAdifference := VAimage - VA;
	VAsign := VAdifference > 0 ? 1 : VAdifference < 0 ? -1 : 0;

	VBimage := 
		case
			VA>=1: 1;
			TRUE : 1;
		esac;
	VBdifference := VBimage - VB;
	VBsign := VBdifference > 0 ? 1 : VBdifference < 0 ? -1 : 0;

	class := VAsign=0&VBsign=0?0:1;

VAR
	VA : 0..1;
	VB : 0..1;

ASSIGN
	next(VA) := 
		case
		class = 1 : {VA, VA + VAsign};
		TRUE : VA;
		esac;
	next(VB) := 
		case
		class = 1& next(VA) = VA : VB + VBsign;
		TRUE : VB;
		esac;
CTLSPEC !(VA=0&VB=0&EF(VA=1&VB=1&EF(VA=0&VB=0)))"""                          
    SMVpath = os.path.join(sys.path[0],"temp.smv")
    f=open(SMVpath,'w')
    f.write(smv_string)
    f.close()
    cmd = NuSMVpath+" "+SMVpath
    output = SP.Popen(cmd, shell=True, stdin=SP.PIPE, stdout=SP.PIPE, stderr=SP.STDOUT)
    message = output.stdout.read()
    working_version = False
    if "is true" in message:
        working_version = True
    version = None
    if message:
        first_line = message.splitlines()[0]
    
        import re
        version_search = re.search("This is NuSMV\ (\S*)",first_line)
        if version_search:
            version = version_search.group(1)
    return {"working_version":working_version,"version":version,"output":message}


def test_PRISMpath(PRISMpath):

    import imp
    import os
    import sys
    import subprocess as SP
    prism_string = \
    """dtmc
formula VAimage = VB>=1?1:1;
formula VAdifference = VAimage - VA;
formula VAsign = VAdifference>0?1:VAdifference<0?-1:0;

formula VBimage = VA>=1?1:1;
formula VBdifference = VBimage - VB;
formula VBsign = VBdifference>0?1:VBdifference<0?-1:0;

formula class = VAsign=0&VBsign=0?0:1;

module Main
    VA: [0..1];
    VB: [0..1];

    [] VAsign!=0&class=1 -> (VA'=VA+VAsign);
    [] VBsign!=0&class=1 -> (VB'=VB+VBsign);
endmodule"""
                        
    PMpath = os.path.join(sys.path[0],"temp.pm")
    f=open(PMpath,'w')
    f.write(prism_string)
    f.close()
    PCTLspec = '"!(VA=0&VB=1& P>0[F VA=1&VB=1& P>0[F VA=1&VB=0]])"'
    cmd = PRISMpath+" "+PMpath+" -pctl "+PCTLspec+" -fixdl"
    output = SP.Popen(cmd, shell=True, stdin=SP.PIPE, stdout=SP.PIPE, stderr=SP.STDOUT, close_fds=True)
    message = output.stdout.read()
    #print message

    working_version = False
    if "Result: true" in message:
        working_version = True
    version = None
    
    if working_version:
        version_line = message.splitlines()[3]
    
        import re
        version_search = re.search("([0-9]|\.)+",version_line)
        if version_search:
            version = version_search.group(0)
        else:
            version = None
    return {"working_version":working_version,"version":version,"output":message}


