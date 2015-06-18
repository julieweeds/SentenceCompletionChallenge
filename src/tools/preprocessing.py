__author__ = 'juliewe'
#18/6/15
#includes tools for preprocessing
#-> convertCONLL
#: takes general CONLL format and converts it into APT input format

import sys,gzip


def configure(arguments):

    parameters={}
    if len(arguments)<3:
        print "Requires two arguments: option and filename"
        exit()
    else:
        parameters["option"]=arguments[1]
        parameters["filename"]=arguments[2]
    return parameters

def getOutputName(filepath):
    parts=filepath.split('/')
    parts[-1]="output."+parts[-1]
    outname=parts[0]
    if len(parts)>1:
        for part in parts[1:]:
            outname+='/'+part
    return outname

class Converter:

    def __init__(self,parameters):
        self.parameters=parameters

    def processline(self,line,outstream):

        fields=line.split('\t')
        if len(fields)==10:
            index=fields[0]
            word=fields[1]
            pos=fields[3]
            dep = fields[6]
            label = fields[7]
            newline=index+"\t"+word+"/"+pos+"\t"+dep+"\t"+label+"\n"
            outstream.write(newline)
        else:
            print "Incorrect file format "+line


    def convert(self):
        inname=self.parameters["filename"]
        outname=getOutputName(inname)
        print "Converting "+inname+" and writing to "+outname

        with gzip.open(inname,'rb') as instream:
            with gzip.open(outname,'wb') as outstream:
                lines=0
                for line in instream:
                    self.processline(line.rstrip(),outstream)
                    lines+=1
                    if lines%1000==0:print "Processed "+str(lines)+" lines"
    def run(self):
        if self.parameters["option"]=="convert":
            self.convert()
        else:
            print "Unknown option: "+self.parameters["option"]
            exit()

if __name__=="__main__":

    myConverter=Converter(configure(sys.argv))
    myConverter.run()