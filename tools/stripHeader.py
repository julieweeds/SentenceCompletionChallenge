__author__ = 'juliewe'
#stripHeader.py is intended to strip the copyright header from the training documents in the given directory and place the result in a clean directory

import ConfigParser,sys,os,glob

class Guillotine:


    def __init__(self,config):
        self.parameters=ConfigParser.RawConfigParser()
        self.parameters.read(config)

    def checkfiles(self):
        indir=os.path.join(self.parameters.get('default','parent'),self.parameters.get('default','input'))
        print indir
        #files = [f for f in os.listdir(indir) if os.path.isfile(os.path.join(indir,f))]

        files=glob.glob(indir+"/*.TXT")
        print len(files),files



    def run_tests(self):
        self.checkfiles()
    def run(self):
        return

if __name__=='__main__':
    myGuillotine=Guillotine(sys.argv[1])
    myGuillotine.run_tests()
    #myGuillotine.run()