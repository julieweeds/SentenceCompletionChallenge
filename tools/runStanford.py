__author__ = 'juliewe'

import ConfigParser,sys,os,ast,subprocess,datetime

def current_time():
    return datetime.datetime.ctime(datetime.datetime.now())

class PythonParser:

    def __init__(self,configfile):
        self.config=ConfigParser.RawConfigParser()
        self.config.read(configfile)
        self.stanford_dir=self.config.get('default','stanford_dir')
        self.data_dir=self.config.get('default','data_dir')
        self.java_threads=self.config.get('default','java_threads')
        self.options=ast.literal_eval(self.config.get('default','options'))
        self.outext=self.config.get('default','outextension')
        self.output_dir = self.data_dir+'-'+self.outext
        self.testinglevel=self.config.get('default','testinglevel')

    def _make_filelist_and_create_files(self, data_dir, filelistpath, output_dir):

    # 1. Create a list of files in a directory to be processed, which
    #    can be passed to stanford's "filelist" input argument.
    # 2. Pre-create each output file in an attempt to avoid cluster
    #    problems.

        with open(filelistpath, 'w') as filelist:
            for filename in os.listdir(data_dir):
                if not filename.startswith("."):
                    filepath = os.path.join(data_dir, filename)
                    filelist.write("%s\n" % filepath)
                    with open(os.path.join(output_dir, filename + '.'+self.outext),
                          'w'):
                        pass
                if self.testinglevel>4:#only process one file
                    break




    def run_stanford_pipeline(self):
    #Process directory of text with Stanford pipeline
    #options to perform:- tokenize,ssplit,pos,lemma,ner,parse
    #initialised via config file passed in via command line
        print "<%s> Starting Stanford pipeline. " % current_time()
        try:
            os.mkdir(self.output_dir)
        except OSError:
            pass

        #change working directory to stanford
        os.chdir(self.stanford_dir)

        for data_sub_dir in [name for name in os.listdir(self.data_dir) if not name.startswith(".")]:

            #setup output subdirectory
            output_sub_dir=os.path.join(self.output_dir,data_sub_dir)
            input_sub_dir=os.path.join(self.data_dir,data_sub_dir)
            try:
                os.mkdir(output_sub_dir)
            except OSError:
                pass #output directory already exists
            #create list of files to be processed
            filelist=os.path.join(self.stanford_dir,"%s-filelist.txt" %data_sub_dir)
            self._make_filelist_and_create_files(input_sub_dir,filelist,output_sub_dir)

            #construct stanford java command
            optionstring=self.options[0]
            for option in self.options[1:]:
                optionstring+=','+option

            ext='.'+self.outext
            stanford_cmd = ['./corenlp.sh',
                            '-annotators',optionstring,
                            '-filelist',filelist,
                            'outputDirectory',output_sub_dir,
                            '-threads', str(self.java_threads),
                            '-outputFormat','xml',
                            '-outputExtension',ext]

            print "Running: \n"+str(stanford_cmd)
            subprocess.call(stanford_cmd)
            print "<%s> Stanford complete for path: %s" %(current_time(),output_sub_dir)
        print "<%s> All stanford complete." % current_time()



if __name__=='__main__':

    myPythonParser=PythonParser(sys.argv[1])
    myPythonParser.run_stanford_pipeline()