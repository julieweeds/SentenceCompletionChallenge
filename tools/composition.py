__author__ = 'juliewe'
import sys,math
from operator import itemgetter

class Composition:

    #datapath="~/Documents/workspace/SentenceCompletionChallenge/data/apt/"
    datafile="nyt_sample100.tsv"
    filterfreq=100
    nouns=["order/N"]
    adjectives=["financial/J"]

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
        self.nounvecs={}
        self.adjvecs={}
        self.nountots={}
        self.nounfeattots={}
        self.adjtots={}
        self.adjfeattots={}

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

    def load_vectors(self,words):
        infile=self.selectpos()+".filtered"
        vecs={}
        with open(infile) as instream:
            lines=0
            for line in instream:
                lines+=1
                print "Processing line "+str(lines)

                line=line.rstrip()
                fields=line.split("\t")
                entry=fields[0]
                if entry in words:
                    vector={}
                    features=fields[1:]

                    index=0
                    while len(features)>0:
                        index+=1

                        freq=features.pop()
                        feat=features.pop()

                        #print str(index)+"\t"+feat+"\t"+str(freq)
                        try:
                            freq=float(freq)
                            vector[feat]=freq
                        except ValueError:
                            print "Error: "+str(index)+"\t"+feat+"\t"+str(freq)+"\n"
                            features=features+list(feat)
                    vecs[entry]=vector

        return vecs

    def compute_typetotals(self,feattots):
        typetots={}
        for feature in feattots.keys():
            pathtype=self.getpathtype(feature)
            sofar=typetots.get(pathtype,0.0)
            typetots[pathtype]=sofar+float(feattots[feature])

        return typetots

    def getpathtype(self,feature):
        fields=feature.split(":")
        return fields[0]

    def mostsalient(self):
        if self.pos=="N":
            vecs=self.nounvecs
            tots=self.nountots
            feattots=self.nounfeattots
            typetots=self.nountypetots

        ppmivecs=self.computeppmi(vecs,tots,feattots,typetots)
        for vector in ppmivecs.values():
            #print vector
            feats=sorted(vector.items(),key=itemgetter(1),reverse=True)

        for tuple in feats[:10]:
            print tuple[0],tuple[1]


    def computeppmi(self,vecs,tots,feattots,typetots):

        ppmivecs={}
        for entry in vecs.keys():
            ppmivector={}
            total=float(tots[entry])
            vector=vecs[entry]
            for feature in vector.keys():
                #try:
                freq=float(vector[feature])
                feattot=float(feattots[feature])
                typetot=float(typetots[self.getpathtype(feature)])

                pmi=math.log10((freq*typetot)/(feattot*total))

                if pmi>0:
                    ppmivector[feature]=pmi



                #except:
                 #   print "Error on feature: "+feature+" on word: "+entry


            ppmivecs[entry]=ppmivector
            #print ppmivector
        return ppmivecs

    def compose(self):
        self.pos="N"
        self.nounfeattots=self.load_coltotals()
        self.nountots=self.load_rowtotals()
        self.nounvecs= self.load_vectors(self.nouns)
        self.nountypetots=self.compute_typetotals(self.nounfeattots)

        self.mostsalient()

    def run(self):

        if self.option=="split":
            self.splitpos()
        elif self.option =="filter":
            self.filter()
        elif self.option=="maketotals":
            self.maketotals()
        elif self.option=="compose":
            self.compose()
        else:
            print "Unknown option: "+self.option

if __name__=="__main__":
    myComposer = Composition(sys.argv[1:])
    myComposer.run()