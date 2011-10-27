class LocalParameterSet(dict):
    '''
    LocalParameterSet is a dictionary with additional flags. It should be used 
    to store K-values of a local parameter Set in the follwing way:
    
        lps = LocalParameterSet()
        lps[context] = k
         
    where k is an integer and context a tuple of regulators as given by 
    ModelContainer.contextId()
    Flags can be set spearately for each regulator of the variable:
    
        _flags[reg1] = {"inc":True, "dec":True } 
        _flags[reg2] = {"inc":True } 
            
    LocalParameterSet behaves excactly like a dictionary with two distinctions:

      - There is a additional member variable self._flags, that is used in 
        backtracking algorithm to check validity
      - the copy() method has been expanded to correctly copy flags.
        
    By the way, a LocalParameterSet does not contain the varname it is related to.
    (this should be taken care of elsewhere)
    '''
    
    def __init__(self, *args):
        dict.__init__(self, *args)
        self._flags = {}
            
    def set_flag(self, regulator, flag):
        if regulator not in self._flags:
            self._flags[regulator] = {}
        self._flags[regulator][flag] = True

    def clear_flags(self):
        self._flags = {}
    
    def get_flag(self, regulator, flag):
        '''
        get_flag verifies whether a specific flag regarding a specific regulator
        has already been set.
        (Note: Although flags are saved as keys in a dictionary, their values don't 
        matter, only the existence of a key is crucial)
        '''
        if regulator not in self._flags:
            return False
        else:
            if flag in self._flags[regulator]:
                return True
            else:
                return False
        
    def copy(self):
        '''
        This copy method does work correctly, if LPS is used only in the way mentioned above.
        If you insert objects or "deeper" dictionarys, copy() cannot assure a correct behaviour!
        '''
        lps = LocalParameterSet()
        # copy flags
        flags = {}
        for reg in self._flags:
		    flags[reg] = {}
		    for flag in self._flags[reg]:
		        flags[reg][flag] = True
        lps._flags = flags
		# copy content
        for context in self:
            lps[context] = self[context]
        return lps

