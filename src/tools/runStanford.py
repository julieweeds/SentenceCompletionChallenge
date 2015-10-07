__author__ = 'juliewe'

import ConfigParser,sys,os,ast,subprocess,datetime
import xml.etree.cElementTree as ET


def current_time():
    return datetime.datetime.ctime(datetime.datetime.now())

class PythonParser:

    def __init__(self,configfile):
        self.config=ConfigParser.RawConfigParser()
        self.config.read(configfile)
        self.whereami=self.config.get('default','whereami')
        self.stanford_dir=self.config.get(self.whereami,'stanford_dir')
        self.data_dir=self.config.get(self.whereami,'data_dir')
        self.working_dir=self.config.get(self.whereami,'working_dir')

        self.java_threads=self.config.get('default','java_threads')
        self.options=ast.literal_eval(self.config.get('default','options'))

        self.outext=self.config.get('default','outextension')
        self.output_dir = self.data_dir+'-'+self.outext
        self.outputformat=self.config.get('default','outputformat')
        self.inputformat=self.config.get('default','inputformat')
        self.data_dir=self.data_dir+"-"+self.inputformat
        #self.conll_dir=self.output_dir+'-conll'
        self.testinglevel=float(self.config.get('default','testinglevel'))
        self.mode=self.config.get('default','mode')  #no_overwrite for not overwriting output files which are non-empty

    def _make_filelist_and_create_files(self, data_dir, filelistpath, output_dir):

    # 1. Create a list of files in a directory to be processed, which
    #    can be passed to stanford's "filelist" input argument.
    # 2. Pre-create each output file in an attempt to avoid cluster
    #    problems.

        with open(filelistpath, 'w') as filelist:
            for filename in os.listdir(data_dir):
                if not filename.startswith("."):
                    #need to check whether the associated file exists in the output directory and whether size is greater than 0 so can restart after memory crash
                    filepath = os.path.join(data_dir, filename)
                    outpath=os.path.join(output_dir,filename+'.'+self.outext)
                    if self.mode=='overwrite' or not os.path.exists(outpath) or os.path.getsize(outpath)==0:
                        filelist.write("%s\n" % filepath)
                        with open(os.path.join(outpath),
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
            if self.testinglevel>3:exit()

            #construct stanford java command
            optionstring=self.options[0]
            for option in self.options[1:]:
                optionstring+=','+option

            ext='.'+self.outext
            stanford_cmd = ['./corenlp.sh',
                            '-annotators',optionstring,
                            '-filelist',filelist,
                            '-outputDirectory',output_sub_dir,
                            '-threads', str(self.java_threads),
                            '-outputFormat','xml',
                            '-outputExtension',ext]

            print "Running: \n"+str(stanford_cmd)
            subprocess.call(stanford_cmd)
            print "<%s> Stanford complete for path: %s" %(current_time(),output_sub_dir)
        print "<%s> All stanford complete." % current_time()

##################
#
#  Formatting to CoNLL from XML format
#
##################
    def process_corpora_from_xml(self):
        """
        Given a directory of corpora, where each corpus is a
        directory of xml files produced by stanford_pipeline,
        convert text to CoNLL-style formatting:
        ID    FORM    LEMMA    POS
        Jobs are run in parallel.
        """
        print "<%s> Starting XML conversion..." % current_time()
        for data_sub_dir in os.listdir(self.output_dir):
            #if data_sub_dir =='saved':
            self._process_xml_to_conll(os.path.join(self.output_dir, data_sub_dir))


    def _process_xml_to_conll(self,data_sub_dir):
        """
        Given a directory of XML documents from stanford's output,
        convert them to CoNLL style sentences. Jobs are not run in parallel.
        """
        print "<%s> Beginning formatting to CoNLL: %s" % (
        current_time(), data_sub_dir)
        # jobs = {}
#        Parallel(n_jobs=processes)(delayed(_process_single_xml_to_conll)(
 ##           os.path.join(path_to_data, data_file))
   #                                for data_file in os.listdir(path_to_data)
    #                               if not (data_file.startswith(".") or
     #                                      data_file.endswith(".conll")))

        for data_file in [df for df in os.listdir(data_sub_dir) if not (df.startswith(".") or df.endswith(".conll"))]:
            if self.outext.endswith('parsed'):
                self._process_single_xml_with_deps_to_conll(os.path.join(data_sub_dir,data_file))
            else:
                self._process_single_xml__to_conll(os.path.join(data_sub_dir,data_file))
        print "<%s> All formatting complete." % current_time()



    def _process_single_xml_with_deps_to_conll(self,path_to_file):
        """
        Convert a single file from XML to CoNLL style.  With dependencies
        """
        with open(path_to_file + ".conll", 'w') as outfile:
            #Create iterator over XML elements, don't store whole tree
            try:
                xmltree = ET.iterparse(path_to_file, events=("end",))
                for _, element in xmltree:
                    if element.tag == "sentence": #If we've read an entire sentence
                        i = 1

                        tuples=[(word,lemma,pos,ner) for word, lemma, pos, ner in zip(element.findall(".//word"),
                                                         element.findall(".//lemma"),
                                                         element.findall(".//POS"),
                                                         element.findall(".//NER"))]

                        dependencies=[dep for dep in element.findall('.//dep')]
                        #print tuples
                        #print dependencies
                        giddict={}
                        reldict={}
                        for dep in dependencies:
                            rel=dep.attrib['type']
                            for child in dep:
                                if child.tag=='governor':
                                    gid=child.attrib['idx']
                                if child.tag=='dependent':
                                    did=child.attrib['idx']
                            #print did,gid,rel
                            giddict[did]=gid
                            reldict[did]=rel



                        for (word,lemma,pos,ner) in tuples:
                            outfile.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                                i, word.text.encode('utf8'), lemma.text.encode('utf8'),
                                pos.text, ner.text,giddict.get(str(i),''),reldict.get(str(i),'')))
                            i += 1
                        outfile.write("\n")
                        #Clear this section of the XML tree
                        element.clear()
            except Exception:
                pass #ignore this file




    def _process_single_xml__to_conll(self,path_to_file):
        """
        Convert a single file from XML to CoNLL style.  No dependencies
        """
        with open(path_to_file + ".conll", 'w') as outfile:
            #Create iterator over XML elements, don't store whole tree
            try:
                xmltree = ET.iterparse(path_to_file, events=("end",))
                for _, element in xmltree:
                    if element.tag == "sentence": #If we've read an entire sentence
                        i = 1
                        #Output CoNLL style
                        for word, lemma, pos, ner in zip(element.findall(".//word"),
                                                         element.findall(".//lemma"),
                                                         element.findall(".//POS"),
                                                         element.findall(".//NER")):
                            outfile.write("%s\t%s\t%s\t%s\t%s\n" % (
                                i, word.text.encode('utf8'), lemma.text.encode('utf8'),
                                pos.text, ner.text))
                            i += 1
                        outfile.write("\n")
                        #Clear this section of the XML tree
                        element.clear()
            except:
                pass #ignore this (probably empty) file

    def stripxml(self):
        os.chdir(self.working_dir)
        self.tags=ast.literal_eval(self.config.get('default','xmltags'))
        strip_command=["java","-mx4g","-jar",self.config.get('default','xmlstripper_jar'),self.data_dir]+self.tags
        print "<%s> Running xml stripper with command: %s" %(current_time(),str(strip_command))
        subprocess.call(strip_command)
        print "<%s> XML stripping complete for path: %s" %(current_time(),self.data_dir)
        self.data_dir=self.data_dir.replace("xml","raw")

    def run(self):

        if self.inputformat=='xml':
            self.stripxml()
        if len(self.options)>0:
            self.run_stanford_pipeline()
        if self.outputformat=='conll':
            self.process_corpora_from_xml()


if __name__=='__main__':

    myPythonParser=PythonParser(sys.argv[1])
    myPythonParser.run()