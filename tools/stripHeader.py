__author__ = 'juliewe'
#stripHeader.py is intended to strip the copyright header from the training documents in the given directory and place the result in a clean directory

import ConfigParser,sys,os,glob

class Guillotine:

    ENDHEADER=list("*END*THE SMALL PRINT!")

    def __init__(self,config):
        self.config=config
        self.parameters=ConfigParser.RawConfigParser()
        self.parameters.read(config[1])
        if len(self.config)>1:
            self.option=self.config[2]
        else:
            self.option='default'
        self.indir=os.path.join(self.parameters.get(self.option,'parent'),self.parameters.get('default','input'))
        self.outdir=os.path.join(self.parameters.get(self.option,'parent'),self.parameters.get('default','output'))

    def checkfiles(self):

        print self.indir
        #files = [f for f in os.listdir(indir) if os.path.isfile(os.path.join(indir,f))]

        files=glob.glob(self.indir+"/*.TXT")
        print len(files),files

        print self.outdir
        files=glob.glob(self.outdir+"/*")
        print len(files),files

    def ensure_outpath(self):
        self.outpath=os.path.join(self.outdir,self.parameters.get('default','input'))
        if not os.path.exists(self.outpath):
            os.makedirs(self.outpath)


    def checkline(self,line):
        chars=list(line)
        if chars[:21]==Guillotine.ENDHEADER:
            self.PASTHEADER=True
    def cleanup(self,inpath):
        filename=os.path.basename(inpath)
        outpath=os.path.join(self.outpath,filename)
        with open(inpath) as instream:
            with open(outpath,'w') as outstream:

                self.PASTHEADER=False
                for line in instream:
                    if self.PASTHEADER:
                        outstream.write(line)
                    self.checkline(line.rstrip())




    def run(self):
        self.checkfiles()
        self.ensure_outpath()
        for f in glob.glob(self.indir+"/*.TXT"):
            self.cleanup(f)


        return

if __name__=='__main__':
    myGuillotine=Guillotine(sys.argv)
    myGuillotine.run()