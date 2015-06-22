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
    if len(arguments)>3:
        parameters["linelength"]=int(arguments[3])


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
        self.linelength=self.parameters.get('linelength',10)
        self.maxlength=self.parameters.get('maxlength',500)

    def processline(self,line,outstream,data):

        fields=line.split('\t')
        if len(fields)==self.linelength:
            index=fields[0]
            if(data['writetooutput']):
                word=fields[1]
                pos=fields[3]
                dep = fields[6]
                label = fields[7]
                newline=index+"\t"+word+"/"+pos+"\t"+dep+"\t"+label+"\n"
                data['buffer']+=newline
            data['currentlines']=data['currentlines']+1
            data['currentmaxindex']=int(index)
        else:
            data['buffer']+="\n"
            if data['writetooutput'] and int(data['currentmaxindex'])<self.maxlength:
                outstream.write(data['buffer'])
            data['buffer']=""
            data['sentences']=data['sentences']+1
            if int(data['currentlines'])>int(data['maxlines']):
                data['maxlines']=data['currentlines']
                data['maxlines_sentpos']=data['sentences']
                data['maxlines_linepos']=data['lines']

            if int(data['currentmaxindex'])>int(data['maxmaxindex']):
                data['maxmaxindex']=data['currentmaxindex']
                data['maxindex_sentpos']=data['sentences']
                data['maxindex_linepos']=data['lines']

            data['currentlines']=0
            data['currentindex']=0
        return data

    def init_data(self):
        data={}
        data['lines']=0
        data['writetooutput']=False
        data['maxlines']=0
        data['maxlines_sentpos']=-1
        data['maxlines_linepos']=-1
        data['maxmaxindex']=0
        data['maxindex_sentpos']=-1
        data['maxindex_linepos']=-1
        data['currentlines']=0
        data['currentindex']=0
        data['sentences']=0
        data['buffer']=""
        return data


    def convert(self):
        inname=self.parameters["filename"]
        outname=getOutputName(inname)
        print "Converting "+inname+" and writing to "+outname
        data=self.init_data()
        data['writetooutput']=True

        with gzip.open(inname,'rb') as instream:
            with gzip.open(outname,'wb') as outstream:

                for line in instream:
                    data['lines']+=1
                    self.processline(line.rstrip(),outstream,data)
                    if data['lines']%1000000==0:print "Processed "+str(data['lines'])+" lines with "+str(data['sentences'])+" sentences"

        print "Processed "+str(data['lines'])+" lines with "+str(data['sentences'])+" sentences"
        print "Longest sentence by index: "+str(data['maxmaxindex'])+" tokens at sentence "+str(data['maxindex_sentpos'])+", line "+str(data['maxindex_linepos'])
        print "Longest sentence by lines: "+str(data['maxmaxindex'])+" tokens at sentence "+str(data['maxlines_sentpos'])+", line "+str(data['maxlines_linepos'])


    def analyse(self):
        inname=self.parameters["filename"]

        print "Analysing "+inname+" with linelength "+str(self.linelength)
        with gzip.open(inname,'rb') as instream:

            data = self.init_data()
            for line in instream:
                data['lines']+=1
                if data['lines']%1000000==0:print "Processed "+str(data['lines'])+" lines with "+str(data['sentences'])+" sentences"
                data=self.processline(line,'',data)

        print "Processed "+str(data['lines'])+" lines with "+str(data['sentences'])+" sentences"
        print "Longest sentence by index: "+str(data['maxmaxindex'])+" tokens at sentence "+str(data['maxindex_sentpos'])+", line "+str(data['maxindex_linepos'])
        print "Longest sentence by lines: "+str(data['maxmaxindex'])+" tokens at sentence "+str(data['maxlines_sentpos'])+", line "+str(data['maxlines_linepos'])



    def run(self):
        if self.parameters["option"]=="convert":
            self.convert()
        if self.parameters["option"]=="analyse":
            self.analyse()
        else:
            print "Unknown option: "+self.parameters["option"]
            exit()

if __name__=="__main__":

    myConverter=Converter(configure(sys.argv))
    myConverter.run()