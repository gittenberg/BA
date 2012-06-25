
networks = dict()
for letter in 'A': # in C, unfortunately green is the input gene
    networks[letter] = dict()
    
networks['A']['name'] = '(A) Incoherent type 1 feed-forward'
networks['A']['interactions'] = {("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
networks['A']['thresholds'] = {("rr","gg"):1, ("rr","bb"):2, ("bb","gg"):1, ("gg","gg"):1}
