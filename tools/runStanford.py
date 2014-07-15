__author__ = 'juliewe'

import ConfigParser,sys,os,ast,subprocess,datetime
import xml.etree.cElementTree as ET


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
        #self.conll_dir=self.output_dir+'-conll'
        self.testinglevel=float(self.config.get('default','testinglevel'))

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
            self._process_single_xml_with_deps_to_conll(os.path.join(data_sub_dir,data_file))

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



    def run(self):
        self.run_stanford_pipeline()
        if self.config.get('default','outputformat')=='conll':
            self.process_corpora_from_xml()


if __name__=='__main__':

    myPythonParser=PythonParser(sys.argv[1])
    myPythonParser.run()