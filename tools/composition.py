__author__ = 'juliewe'
import sys

class Composition:

    #datapath="~/Documents/workspace/SentenceCompletionChallenge/data/apt/"
    datafile="nyt_sample100.tsv"
    filterfreq=100

    def __init__(self,options):
        self.option=options[0]
        self.inpath=Composition.datafile;
        self.nounfile=self.inpath+".nouns"
        self.verbfile=self.inpath+".verbs"
        self.adjfile=self.inpath+".adjs"
        self.advfile=self.inpath+".advs"
        self.otherfile=self.inpath+".others"
        if len(options)>1:
            self.pos=options[1]
        else:
            self.pos="N"

    def splitpos(self):

        nouns=open(self.nounfile,"w")
        verbs=open(self.verbfile,"w")
        adjs=open(self.adjfile,"w")
        advs=open(self.advfile,"w")
        others=open(self.otherfile,"w")

        with open(self.inpath) as instream:
            for line in instream:
                line=line.rstrip()
                entry=line.split("\t")[0]
                pos=entry.split("/")[1]
                if pos=="N":
                    nouns.write(line+"\n")
                elif pos=="V":
                    verbs.write(line+"\n")
                elif pos=="J":
                    adjs.write(line+"\n")
                elif pos=="R":
                    advs.write(line+"\n")
                else:
                    others.write(line+"\n")


        nouns.close()
        verbs.close()
        adjs.close()
        advs.close()
        others.close()

        return

    def filter(self):
        rowtotals = self.load_rowtotals()
        coltotals= self.load_coltotals()
        infile = self.selectpos()
        outfile=infile+".filtered"

        outstream=open(outfile,"w")
        with open(infile) as instream:
            lines=0
            for line in instream:
                line = line.rstrip()
                lines+=1
                print "Processing line "+str(lines)
                fields=line.split("\t")
                entry=fields[0]
                features=fields[1:]
                entrytot=rowtotals.get(entry,0)
                nofeats=0
                if entrytot>Composition.filterfreq:
                    outline=entry
                    print entry
                    while len(features)>0:
                        freq=features.pop()
                        feat=features.pop()

                        feattot=float(coltotals.get(feat,0))
                        #print feat+"\t"+str(feattot-Composition.filterfreq)

                        if feattot>Composition.filterfreq:
                            outline+="\t"+feat+"\t"+freq
                            nofeats+=1

                if nofeats>0:
                    outstream.write(outline+"\n")


        outstream.close()

    def selectpos(self):
        if self.pos=="N":
            infile=self.nounfile
        elif self.pos=="V":
            infile=self.verbfile
        elif self.pos=="J":
            infile=self.adjfile
        elif self.pos=="R":
            infile=self.advfile

        return infile

    def maketotals(self):

        infile= self.selectpos()
        rowtotals=infile+".rtot"
        coltotals=infile+".ctot"

        rows=open(rowtotals,"w")
        cols=open(coltotals,"w")

        featuretotals={}
        with open(infile) as instream:
            lines=0
            for line in instream:
                lines+=1
                print "Processing line "+str(lines)
                rowtotal=0.0
                line=line.rstrip()
                fields=line.split("\t")
                entry=fields[0]
                features=fields[1:]

                index=0
                while len(features)>0:
                    index+=1

                    freq=features.pop()
                    feat=features.pop()

                    #print str(index)+"\t"+feat+"\t"+str(freq)
                    try:
                        freq=float(freq)
                        rowtotal+=freq
                        current=featuretotals.get(feat,0.0)
                        featuretotals[feat]=current+freq
                    except ValueError:
                        print "Error: "+str(index)+"\t"+feat+"\t"+str(freq)+"\n"
                        features=features+list(feat)



                rows.write(entry+"\t"+str(rowtotal)+"\n")

        for feat in featuretotals.keys():
            cols.write(feat+"\t"+str(featuretotals[feat])+"\n")


        rows.close()
        cols.close()

    def load_rowtotals(self):
        infile= self.selectpos()
        rowtotals=infile+".rtot"
        totals={}
        with open(rowtotals) as instream:
            for line in instream:
                line=line.rstrip()
                fields=line.split("\t")
                totals[fields[0]]=fields[1]

        return totals

    def load_coltotals(self):
        infile=self.selectpos()
        coltotals=infile+".ctot"
        totals={}

        with open(coltotals) as instream:
            for line in instream:
                line=line.rstrip()
                fields=line.split("\t")
                totals[fields[0]]=fields[1]
        return totals


    def run(self):

        if self.option=="split":
            self.splitpos()
        elif self.option =="filter":
            self.filter()
        elif self.option=="maketotals":
            self.maketotals()
        else:
            print "Unknown option: "+self.option

if __name__=="__main__":
    myComposer = Composition(sys.argv[1:])
    myComposer.run()