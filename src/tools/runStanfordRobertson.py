import ConfigParser,os,sys,subprocess
from runStanford import PythonParser, current_time

__author__ = 'juliewe'
#run the Stanford pipeline upto tagging and NER, convert to CONLL and then use ADR's dependency parser

class ParsingPipeline(PythonParser):

    def __init__(self,configfile):
        self.config=ConfigParser.RawConfigParser()
        self.config.read(configfile)
        self.whereami=self.config.get('default','whereami')
        self.stanford_dir=self.config.get(self.whereami,'stanford_dir')
        self.data_dir=self.config.get(self.whereami,'data_dir')
        self.working_dir=self.config.get(self.whereami,'working_dir')
        self.robertson_jar=self.config.get('default','robertson_jar')
        self.java_threads=self.config.get('default','java_threads')
        self.options=['tokenize','ssplit','pos','lemma','ner']
        self.outext="tagged"
        self.outputformat="conll"
        self.inputformat=self.config.get('default','inputformat')

        self.output_dir = self.data_dir+'-'+self.outext
        self.data_dir=self.data_dir+"-"+self.inputformat
        self.testinglevel=float(self.config.get('default','testinglevel'))
        self.mode=self.config.get('default','mode')  #no_overwrite for not overwriting output files which are non-empty

    def run_robertson_parser(self):

        os.chdir(self.working_dir)

        robertson_command=["java","-mx16g","-jar",self.robertson_jar,self.output_dir]
        print("<%s> Running Robertson parser with command: %s" %(current_time(),str(robertson_command)))
        subprocess.call(robertson_command)
        print("<%s> Robertson parser complete for path: %s" %(current_time(),self.output_dir))

    def run(self):
        if self.inputformat!="sfd_parsed" and self.inputformat!="tagged":
            self.runPipeline()
        else:
            self.output_dir=self.data_dir
        self.run_robertson_parser()



if __name__=='__main__':

    myPythonParser=ParsingPipeline(sys.argv[1])
    myPythonParser.run()