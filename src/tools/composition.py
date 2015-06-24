__author__ = 'juliewe'
#contains a number of tools useful for working with APT vector files - started March 2015
#split : by POS
#maketotals : for PPMI calculation/Byblo
#filter : only words in lists (nouns and adjectives) and/or with particular frequency
#compose : words in lists using simple add composition
#reduceorder : only retain features with given orders
#revectorise : output PPMI vectors

#vectors are displayed via their most salient features



import sys,math, json,codecs
from operator import itemgetter

class Composition:

    #datapath="~/Documents/workspace/ThesEval/data/wikiPOS_t100f100_nouns_deps"
    datafile="nyt.tsv"
    #datafile="wikiPOS.events"
    filterfreq=1000
    #nouns=["brush/n","shoot/n","rose/n","gift/n","conviction/n"]
    #filterfile="senseneighbours.json"
    filterfile=""
    #adjectives=["military/J"]
    nouns=[]
    adjectives=[]

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

        if len(options)>2:
            self.minorder=int(options[2])
            self.maxorder=int(options[3])
            self.reducedstring=".reduce_"+str(self.minorder)+"_"+str(self.maxorder)
        else:
            self.minorder=0
            self.maxorder=2
            self.reducedstring=""

        self.nounvecs={}
        self.adjvecs={}
        self.nountots={}
        self.nounfeattots={}
        self.adjtots={}
        self.adjfeattots={}

        self.set_words()

    def set_words(self):

        if Composition.filterfile=="":
            if self.pos=="N":
                self.words=Composition.nouns
            elif self.pos=="J":
                self.words=Composition.adjectives
        else:
            with open(Composition.filterfile) as fp:
                self.wordlistlist=json.load(fp)
            self.words=[]
            for wordlist in self.wordlistlist:
                self.words+=wordlist

    def splitpos(self):

        nouns=open(self.nounfile,"w")
        verbs=open(self.verbfile,"w")
        adjs=open(self.adjfile,"w")
        advs=open(self.advfile,"w")
        others=open(self.otherfile,"w")

        with open(self.inpath) as instream:
            lines=0
            for line in instream:

                line=line.rstrip()
                entry=line.split("\t")[0]

                try:
                    pos=entry.split("/")[1]
                except:
                    print "Cannot split "+entry+" on line "+str(lines)
                    pos=""

                pos=entry.split("/")[1].lower()
                if pos=="n":
                    nouns.write(line+"\n")
                elif pos=="v":
                    verbs.write(line+"\n")
                elif pos=="j":
                    adjs.write(line+"\n")
                elif pos=="r":
                    advs.write(line+"\n")
                else:
                    others.write(line+"\n")
                if lines % 1000==0:print "Processed "+str(lines)+" lines"
                lines+=1

        nouns.close()
        verbs.close()
        adjs.close()
        advs.close()
        others.close()

        return

    def reduceorder(self):

        infile=self.selectpos()
        outfile=infile+self.reducedstring
        with open(outfile,"w") as outstream:
            with open(infile) as instream:
                lines=0
                for line in instream:
                    line=line.rstrip()
                    print "Processing line "+str(lines)
                    lines+=1
                    fields=line.split("\t")
                    entry=fields[0]
                    features=fields[1:]
                    outline=entry
                    nofeats=0
                    while len(features)>0:
                        freq=features.pop()
                        feat=features.pop()
                        forder=self.getorder(feat)

                        if forder>=self.minorder and forder<=self.maxorder:
                            outline+="\t"+feat+"\t"+freq
                            nofeats+=1
                    print entry, nofeats
                    if nofeats>0:
                        outstream.write(outline+"\n")
                        #print "written out"


    def include(self,word):
        if len(self.words)==0:
            return True
        elif word in self.words:
            return True
        else:
            return False

    def filter(self):


        rowtotals = self.load_rowtotals()
        coltotals= self.load_coltotals()
        infile = self.selectpos()+self.reducedstring
        outfile=infile+".filtered"

        outstream=open(outfile,"w")
        print "Filtering for words ",self.words
        print "Filtering for frequency ",Composition.filterfreq
        with open(infile) as instream:
            lines=0
            for line in instream:
                line = line.rstrip()
                if lines%1000==0:print "Processing line "+str(lines)
                lines+=1
                fields=line.split("\t")
                #entry=fields[0].lower()
                entry=fields[0]
                features=fields[1:]
                entrytot=rowtotals.get(entry,0)
                nofeats=0
                if entrytot>Composition.filterfreq and self.include(entry):
                    outline=entry
                    print entry
                    while len(features)>0:
                        freq=features.pop()
                        #feat=features.pop().lower()
                        feat=features.pop()
                        feattot=float(coltotals.get(feat,0))
                        #print feat+"\t"+str(feattot-Composition.filterfreq)

                        if feattot>Composition.filterfreq:
                            outline+="\t"+feat+"\t"+freq
                            nofeats+=1

                    if nofeats>0:
                        outstream.write(outline+"\n")
                else:
                    print "Ignoring "+entry+" with frequency "+str(entrytot)

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

        infile= self.selectpos()+self.reducedstring
        rowtotals=infile+".rtot"
        coltotals=infile+".ctot"

        rows=open(rowtotals,"w")
        cols=open(coltotals,"w")

        featuretotals={}
        with open(infile) as instream:
            lines=0
            for line in instream:

                print "Processing line "+str(lines)
                lines+=1
                rowtotal=0.0
                line=line.rstrip()
                fields=line.split("\t")
                entry=fields[0].lower()
                features=fields[1:]

                index=0
                while len(features)>0:
                    index+=1

                    freq=features.pop()
                    feat=features.pop().lower()

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
        rowtotals=infile+self.reducedstring+".rtot"
        totals={}
        with open(rowtotals) as instream:
            for line in instream:
                line=line.rstrip()
                fields=line.split("\t")
                totals[fields[0]]=float(fields[1])

        return totals

    def load_coltotals(self):
        infile=self.selectpos()
        coltotals=infile+self.reducedstring+".ctot"
        totals={}

        with open(coltotals) as instream:
            for line in instream:
                line=line.rstrip()
                fields=line.split("\t")
                totals[fields[0]]=float(fields[1])
        return totals

    def add(self,avector,bvector):
        rvector=dict(avector)
        for feat in bvector.keys():
            rvector[feat]=rvector.get(feat,0)+bvector[feat]
        return rvector

    def load_vectors(self):
        infile=self.selectpos()+self.reducedstring+".filtered"
        vecs={}
        with open(infile) as instream:
            lines=0
            for line in instream:
                lines+=1
                print "Reading line "+str(lines)

                line=line.rstrip()
                fields=line.split("\t")
                entry=fields[0]
                #print entry, self.words
                if self.include(entry):
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
                    if entry in vecs.keys():
                        vecs[entry]=self.add(vecs[entry],vector)
                    else:
                        vecs[entry]=vector

        print "Loaded "+str(len(vecs.keys()))+" vectors"
        return vecs

    def output(self,vectors,outfile):
        with open(outfile,"w") as outstream:
            for entry in vectors.keys():
                vector=vectors[entry]

                if len(vector.keys())>0:
                    outstring=entry
                    for feat in vector.keys():
                        outstring+="\t"+feat+"\t"+str(vector[feat])
                    outstream.write(outstring+"\n")



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

    def getpathvalue(self,feature):
        fields=feature.split(":")
        if len(fields)>1:
            return fields[1]
        else:
            #print "No feature value for "+feature
            return ""

    def mostsalient(self):
        if self.pos=="N":
            vecs=self.nounvecs
            tots=self.nountots
            feattots=self.nounfeattots
            typetots=self.nountypetots
        elif self.pos=="J":
            vecs=self.adjvecs
            tots=self.adjtots
            feattots=self.adjfeattots
            typetots=self.nountypetots

        self.mostsalientvecs(vecs,tots,feattots,typetots)

    def mostsalientvecs(self,vecs,tots,feattots,typetots):

        ppmivecs=self.computeppmi(vecs,tots,feattots,typetots)
        for entry in ppmivecs.keys():
            print "Most salient features for "+entry+" , total feature count: "+str(tots[entry])+", width: "+str(len(vecs[entry].keys()))+", "+str(len(ppmivecs[entry].keys()))
            vector=ppmivecs[entry]
            #print vector
            feats=sorted(vector.items(),key=itemgetter(1),reverse=True)

            donetypes={}

            for tuple in feats:
                feature=tuple[0]
                pathtype=self.getpathtype(feature)
                done=donetypes.get(pathtype,0)
                if done<3:
                    print feature+" : "+str(tuple[1])+" ("+str(vecs[entry][feature])+")"
                donetypes[pathtype]=done+1

            print donetypes
            print "-----"

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

    def revectorise(self):

        outfile=self.selectpos()+self.reducedstring+".filtered.ppmi"
        self.nounvecs=self.load_vectors()
        self.nounfeattots=self.load_coltotals()
        self.nountots=self.load_rowtotals()
        self.nountypetots=self.compute_typetotals(self.nounfeattots)

        ppmivecs=self.computeppmi(self.nounvecs,self.nountots,self.nounfeattots,self.nountypetots)
        self.output(ppmivecs,outfile)

    def compose(self):
        self.pos="N"
        self.set_words()
        self.nounfeattots=self.load_coltotals()
        self.nountots=self.load_rowtotals()
        self.nounvecs= self.load_vectors()
        self.nountypetots=self.compute_typetotals(self.nounfeattots)

        self.mostsalient()

        self.pos="J"
        self.set_words()
        self.adjfeattots=self.load_coltotals()
        self.adjtots=self.load_rowtotals()
        self.adjvecs= self.load_vectors()
        self.adjtypetots=self.compute_typetotals(self.adjfeattots)

        self.mostsalient()

        self.runANcomposition()

    def inspect(self):
        self.pos="N"
        self.set_words()
        self.nounfeattots=self.load_coltotals()
        self.nountots=self.load_rowtotals()
        self.nounvecs= self.load_vectors()
        self.nountypetots=self.compute_typetotals(self.nounfeattots)

        self.mostsalient()

    def runANcomposition(self):

        ANfeattots=self.addAN(self.adjfeattots,self.nounfeattots)

        ANtypetots=self.addAN(self.adjtypetots,self.nountypetots)
        #print ANtypetots

        ANvecs={}
        ANtots={}
        for adj in self.adjectives:
            for noun in self.nouns:
                (entry,ANvec,ANtot)=self.ANcompose(adj,noun)
                ANvecs[entry]=ANvec
                ANtots[entry]=ANtot
                #print ANvecs,ANtots
        self.mostsalientvecs(ANvecs,ANtots,ANfeattots,ANtypetots)

    def getorder(self,feature):
        path=self.getpathtype(feature)

        if path=="":
            order=0
        else:
            fields=path.split("\xc2\xbb")
            order=len(fields)

        return order

    def splitfeature(self,feature):
        path=self.getpathtype(feature)

        if path=="":
            return "",""
        else:
            fields=path.split("\xc2\xbb")


            if len(fields)>1:
                text=fields[1]
                if len(fields)>2:
                    for field in fields[2:]:
                        text+="\xc2\xbb"+field
                return fields[0],text
            else:
                return fields[0],""


    def offsetAN(self,adjvector):
        adjPREFIX="_mod"
        nounPREFIX="mod"

        offsetvector={}
        incomp=0
        for feature in adjvector.keys():
            (prefix,suffix)= self.splitfeature(feature)
            if prefix==adjPREFIX:
                newfeature=suffix+":"+self.getpathvalue(feature)
            elif prefix.startswith("_"):
                #incompatible feature for composition
                #print "Incompatible feature for composition: "+feature
                incomp+=1
                newfeature=""
            elif feature.startswith(":"):
                newfeature=nounPREFIX+feature
            else:
                newfeature=nounPREFIX+"\xc2\xbb"+feature
            if not newfeature == "":
                offsetvector[newfeature]=adjvector[feature]
        #print "Incompatible features in adjective vector: "+str(incomp)
        return offsetvector


    def addAN(self,adjvector,nounvector):

        offsetvector = self.offsetAN(adjvector)

        ANvector={}
        #print "Processing noun features "+str(len(nounvector.keys()))
        count=0
        intersect=[]
        for feature in nounvector.keys():
            count+=1
            if feature in offsetvector:
                ANvector[feature]=float(nounvector[feature])+float(offsetvector[feature])
                intersect.append(feature)
                offsetvector.__delitem__(feature)
            else:
                ANvector[feature]=nounvector[feature]
            #if count%10000==0:print"Processed "+str(count)
        print "Intersecting features: "+str(len(intersect))
        #print "Processing remaining adj features "+str(len(adjvector.keys()))+" : reduced to : "+str(len(offsetvector.keys()))
        count=0
        ANvector.update(offsetvector)
        #print "Complete"

        return ANvector

    def ANcompose(self,adj,noun):
        nounvector=self.nounvecs[noun]
        adjvector=self.adjvecs[adj]
        ANvector=self.addAN(adjvector,nounvector)
        ANtot=float(self.nountots[noun])+float(self.adjtots[adj])
        entry=adj+" "+noun

        return(entry,ANvector,ANtot)

    def intersect(self):

        self.nounfeattots=self.load_coltotals()
        self.nountots=self.load_rowtotals()
        self.nountypetots=self.compute_typetotals(self.nounfeattots)
        self.nounvecs= self.load_vectors()

        intersectedvecs=self.intersectall()

        self.mostsalientvecs(intersectedvecs,self.nountots,self.nounfeattots,self.nountypetots)

    def intersectall(self):

        intersected={}
        for wordlist in self.wordlistlist:
            name=self.join(wordlist,'_')
            vector=self.nounvecs[wordlist[0]]
            for aword in wordlist[1:]:
                vector = self.intersecteach(vector,self.nounvecs[aword])
            intersected[name]=vector
            total=0
            for value in vector.values():
                total+=value
            self.nountots[name]=total
        return intersected

    def intersecteach(self,avector,bvector):
        newvector={}
        for feat in avector.keys():
            value=min(avector[feat],bvector.get(feat,0))
            if value>0:
                newvector[feat]=value
        return newvector


    def join (self,alist,achar):
        if len(alist)>1:
            astring=alist[0]
            for element in alist[1:]:
                astring+=achar+element
            return astring

        elif len(alist)==1:
            return alist[0]
        else:
            return ""

    def run(self):

        if self.option=="split":
            self.splitpos()
        elif self.option =="filter":
            self.filter()
        elif self.option=="maketotals":
            self.maketotals()
        elif self.option=="compose":
            self.compose()
        elif self.option=="inspect":
            self.inspect()
        elif self.option=="reduceorder":
            self.reduceorder()
        elif self.option=="revectorise":
            self.revectorise()
        elif self.option=="intersect":
            self.intersect()

        else:
            print "Unknown option: "+self.option

if __name__=="__main__":
    myComposer = Composition(sys.argv[1:])
    myComposer.run()