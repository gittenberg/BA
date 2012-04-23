import os
import sqlite3


if __name__=='__main__':
    #os and path diagnostics:
    if os.name != 'nt':
        print "running on linux."
        path="/home/bude/mjseeger/git/BA/code"
        nusmvpath = r"~/NuSMV-2.5.4-i386-redhat-linux-gnu/bin/NuSMV"    # Linux computer
    elif os.name == 'nt':
        print "running on windows."
        path="C:\Users\MJS\git\BA\code"
        nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                     # Samsung laptop
        #nusmvpath = "C:\Progra~2\NuSMV\2.5.4\bin\NuSMV.exe"            # Acer laptop

    dbname = 'filter_results.without_morphogene.db'
    
    # connect to database
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    c.execute('SELECT * FROM globalparametersets')
    for i in range(10):
        print c.fetchone()

    print "Done."
