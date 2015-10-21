__author__ = 'juliewe'
#support composition of compounds and comparison with observed vectors

from composition import Composition
import ConfigParser,sys
from compositionality.compounds import Compounder

class DepCompounder(Compounder):

    def __init__(self,configfile):
        return
    

class NounCompounder(Composition):
    def __init__(self,configfile):
        config = ConfigParser.RawConfigParser()
        config.read(configfile)
        myCompounder=DepCompounder(configfile)

    def run(self):
        return

if __name__=="__main__":
    myCompounder=NounCompounder(sys.argv[1])
    myCompounder.run()