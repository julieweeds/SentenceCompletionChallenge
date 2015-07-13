__author__ = 'juliewe'
#contains a number of tools useful for working with APT vector files - started March 2015
#split : by POS
#maketotals : for PPMI calculation/Byblo
#filter : only words in lists (nouns and adjectives) and/or with particular frequency
#compose : words in lists using simple add composition
#reduceorder : only retain features with given orders
#revectorise : output PPMI vectors or PNPPMI vectors
#normalise: convert counts to probabilities

#vectors are displayed via their most salient features



import sys,math, json,gzip
from operator import itemgetter
import graphing

class Composition:

    #datapath="~/Documents/workspace/ThesEval/data/wikiPOS_t100f100_nouns_deps"
    datafile="wikipedia-lc2vectors.tsv"
    #datafile="wikiPOS.events"
    filterfreq=1000
    #nouns=["brush/n","shoot/n","rose/n","gift/n","conviction/n"]
    filterfile="senseneighbours2.json"
    #filterfile=""
    #adjectives=["military/J"]
    nouns=[]
    adjectives=[]

    def __init__(self,options):
        self.option=options[0]
        if len(options)>1:
            self.inpath=options[1]
        else:
            self.inpath=Composition.datafile
        self.nounfile=self.inpath+".nouns"
        self.verbfile=self.inpath+".verbs"
        self.adjfile=self.inpath+".adjs"
        self.advfile=self.inpath+".advs"
        self.otherfile=self.inpath+".others"

        if len(options)>2:
            self.pos=options[2]
        else:
            self.pos="N"

        if len(options)>3 and not options[3]=="X":

            self.minorder=int(options[3])
            self.maxorder=int(options[4])
            self.reducedstring=".reduce_"+str(self.minorder)+"_"+str(self.maxorder)
        else:
            self.minorder=0
            self.maxorder=2
            self.reducedstring=""

        self.pp_normal= "pp_normalise" in options or "pnppmi" in options #include one of these flags in order for PPMI values to be multiplied by path probability in final vectors
        self.gof_ppmi="gof_ppmi" in options

        self.normalised = "normalise" in options or "normalised" in options #this may be the main option (to carry out normalisation) or be included as one of the optional options so that normalised counts are used

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


        infile=self.inpath+".gz"


        with gzip.open(infile) as instream:
            lines=0
            for line in instream:

                line=line.rstrip()
                entry=line.split("\t")[0]

                try:
                    pos=entry.split("/")[-1].lower()
                except:
                    print "Cannot split "+entry+" on line "+str(lines)
                    pos=""

                #pos=entry.split("/")[-1].lower()
                if pos.startswith("n"):
                    nouns.write(line+"\n")
                elif pos.startswith("v"):
                    verbs.write(line+"\n")
                elif pos.startswith("j"):
                    adjs.write(line+"\n")
                elif pos.startswith("r"):
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



        infile = self.selectpos()+self.reducedstring
        outfile=infile+".filtered"

        coltotals= self.load_coltotals()
        self.reducedstring=".reduce_1_1" #always use same rowtotals for filtering whatever the reduction
        rowtotals = self.load_rowtotals()
        outstream=open(outfile,"w")
        print "Filtering for words ",self.words
        print "Filtering for frequency ",Composition.filterfreq
        todo=len(rowtotals)
        with open(infile) as instream:
            lines=0
            for line in instream:
                line = line.rstrip()
                if lines%1000==0:
                    percent=lines*100.0/todo
                    print "Processing line "+str(lines)+"("+str(percent)+"%)"
                lines+=1
                fields=line.split("\t")
                #entry=fields[0].lower()
                entry=fields[0]
                features=fields[1:]
                entrytot=rowtotals.get(entry,0)
                nofeats=0
                if entrytot>Composition.filterfreq and self.include(entry):
                    outline=entry
                    #print "Filtering entry for "+entry
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

    def normalise(self):
        rowtotals=self.load_rowtotals()
        infile= self.selectpos()+self.reducedstring+".filtered"
        outfile=infile+".norm"

        print "Normalising counts => sum to 1"
        outstream=open(outfile,"w")

        todo=len(rowtotals.keys())
        print "Estimated total vectors to do = "+str(todo)
        with open(infile) as instream:
            lines=0
            for line in instream:

                line = line.rstrip()
                fields=line.split("\t")
                entry=fields[0]
                features=fields[1:]
                entrytot=rowtotals[entry]
                outline=entry
                while len(features)>0:
                    weight=float(features.pop())
                    feat=features.pop()
                    weight = weight/entrytot
                    outline+="\t"+feat+"\t"+str(weight)
                outline+="\n"
                outstream.write(outline)
                lines+=1
                if lines%1000==0:
                    percent=lines*100.0/todo
                    print "Completed "+str(lines)+" vectors ("+str(percent)+"%)"
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

        if self.normalised:
            infile=self.selectpos()+self.reducedstring+".filtered"+".norm"
        else:
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
        infile= self.selectpos()+self.reducedstring
        if self.normalised and not self.option=="normalise":
            infile+=".filtered.norm"
        rowtotals=infile+".rtot"
        totals={}
        print "Loading entry totals from: "+rowtotals
        with open(rowtotals) as instream:
            for line in instream:
                line=line.rstrip()
                fields=line.split("\t")
                totals[fields[0]]=float(fields[1])

        return totals

    def load_coltotals(self):
        infile=self.selectpos()+self.reducedstring
        if self.normalised and not self.option=="normalise":
            infile+=".filtered.norm"
        coltotals=infile+".ctot"
        totals={}
        print "Loading feature totals from: "+coltotals
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
        if self.normalised and not self.option=="normalise":
            infile+=".norm"
        vecs={}
        print "Loading vectors from: "+infile
        with open(infile) as instream:
            lines=0
            for line in instream:
                lines+=1
                if lines%1000==0: print "Reading line "+str(lines)

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
        #write a set of vectors to file
        print "Writing vectors to output file: "+outfile
        with open(outfile,"w") as outstream:
            for entry in vectors.keys():
                vector=vectors[entry]

                if len(vector.keys())>0:
                    outstring=entry
                    for feat in vector.keys():
                        outstring+="\t"+feat+"\t"+str(vector[feat])
                    outstream.write(outstring+"\n")



    def compute_typetotals(self,feattots):
        #compute totals for different paths over all entries (using column totals given in feattots)
        print "Computing path totals C<*,t,*>"
        typetots={}
        for feature in feattots.keys():
            pathtype=self.getpathtype(feature)
            sofar=typetots.get(pathtype,0.0)
            typetots[pathtype]=sofar+float(feattots[feature])

        return typetots

    def compute_nounpathtotals(self,vectors):
        #compute totals for the different paths for each entry
        print "Computing path totals for each entry C<w1,t,*>"
        pathtotals={}
        for entry in vectors.keys():
            totalvector={}
            vector=vectors[entry]
            for feature in vector.keys():
                pathtype=self.getpathtype(feature)
                sofar=totalvector.get(pathtype,0.0)
                totalvector[pathtype]=sofar+float(vector[feature])

            pathtotals[entry]=totalvector
        return pathtotals

    def getpathtype(self,feature):
        #get the path of a given feature
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
            tots=self.nounpathtots
            feattots=self.nounfeattots
            typetots=self.nountypetots
            entrytots=self.nountots
        elif self.pos=="J":
            vecs=self.adjvecs
            tots=self.adjpathtots
            feattots=self.adjfeattots
            typetots=self.nountypetots
            entrytots=self.adjtots

        self.mostsalientvecs(vecs,tots,feattots,typetots,entrytots)

    def mostsalientvecs(self,vecs,pathtots,feattots,typetots,entrytots):

        ppmivecs=self.computeppmi(vecs,pathtots,feattots,typetots,entrytots)
        for entry in ppmivecs.keys():
            print "Most salient features for "+entry+" , width: "+str(len(vecs[entry].keys()))+", "+str(len(ppmivecs[entry].keys()))
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

    def computeppmi(self,vecs,pathtots,feattots,typetots,entrytots):

        ppmivecs={}
        grandtot=0.0
        if self.pp_normal:
            print "Computing pnppmi"
        elif self.gof_ppmi:
            print "Computing gof_ppmi"
            for type in typetots.keys():
                grandtot+=float(typetots[type])
                print type, grandtot
        else:
            print "Computing ppmi"
        done =0
        todo=len(vecs.keys())

        for entry in vecs.keys():

            ppmivector={}

            vector=vecs[entry]

            for feature in vector.keys():

                freq=float(vector[feature])  # C<w1,p,w2>
                total=float(pathtots[entry][self.getpathtype(feature)]) # S<w1,p,*>
                feattot=float(feattots[feature]) #S<*,p,w2>
                typetot=float(typetots[self.getpathtype(feature)]) #S<*,p,*>
                entrytotal=float(entrytots[entry]) # S<w1,*,*>

                if self.gof_ppmi:

                    pmi=math.log10((freq*grandtot)/(feattot*entrytotal))
                else:
                    pmi=math.log10((freq*typetot)/(feattot*total))

                if pmi>0:
                    if self.pp_normal:

                        pmi=pmi * total/entrytotal
                    ppmivector[feature]=pmi

            done+=1
            if done%1000==0:
                percent=done*100.0/todo
                print "Completed "+str(done)+" vectors ("+str(percent)+"%)"



            ppmivecs[entry]=ppmivector
            #print ppmivector
        return ppmivecs

    def revectorise(self):

        if self.normalised:
            suffix=".norm"
        else:
            suffix=""
        if self.pp_normal:
            suffix += ".pnppmi"
        elif self.gof_ppmi:
            suffix += ".gof_ppmi"
        else:
            suffix += ".ppmi"
        outfile=self.selectpos()+self.reducedstring+".filtered"+suffix
        self.nounvecs=self.load_vectors()
        self.nounfeattots=self.load_coltotals()
        self.nountots=self.load_rowtotals()
        self.nounpathtots=self.compute_nounpathtotals(self.nounvecs)
        self.nountypetots=self.compute_typetotals(self.nounfeattots)

        ppmivecs=self.computeppmi(self.nounvecs,self.nounpathtots,self.nounfeattots,self.nountypetots,self.nountots)
        self.output(ppmivecs,outfile)

    def compose(self):
        self.pos="N"
        self.set_words()
        self.nounfeattots=self.load_coltotals()
        self.nountots=self.load_rowtotals()
        self.nounvecs= self.load_vectors()
        self.nounpathtots=self.compute_nounpathtotals(self.nounvecs)
        self.nountypetots=self.compute_typetotals(self.nounfeattots)

        self.mostsalient()

        self.pos="J"
        self.set_words()
        self.adjfeattots=self.load_coltotals()
        self.adjtots=self.load_rowtotals()
        self.adjvecs= self.load_vectors()
        self.adjpathtots=self.compute_nounpathtotals(self.adjvecs)
        self.adjtypetots=self.compute_typetotals(self.adjfeattots)

        self.mostsalient()

        self.runANcomposition()

    def inspect(self):
        self.pos="N"
        self.set_words()
        self.nounfeattots=self.load_coltotals()
        self.nountots=self.load_rowtotals()
        self.nounvecs= self.load_vectors()
        self.nounpathtots=self.compute_nounpathtotals(self.nounvecs)
        self.nountypetots=self.compute_typetotals(self.nounfeattots)
        print self.nountypetots
        graphing.display_bargraph(self.nountypetots,title="Path Distribution over all Nouns")
        for entry in self.nounvecs.keys():
            title="Path Distribution for "+entry
            graphing.display_bargraph(self.nounpathtots[entry],title)

        self.mostsalient()

    def runANcomposition(self):

        ANfeattots=self.addAN(self.adjfeattots,self.nounfeattots)

        ANtypetots=self.addAN(self.adjtypetots,self.nountypetots)

        ANpathtots=self.addAN(self.adjpathtots,self.nounpathtots)
        #print ANtypetots

        ANvecs={}
        ANtots={}
        for adj in self.adjectives:
            for noun in self.nouns:
                (entry,ANvec,ANtot)=self.ANcompose(adj,noun)
                ANvecs[entry]=ANvec
                ANtots[entry]=ANtot
                #print ANvecs,ANtots

        #check this
        self.mostsalientvecs(ANvecs,ANpathtots,ANfeattots,ANtypetots,ANtots)

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
       # self.nounpathtots=self.compute_nounpathtotals(self.nounvecs)

        intersectedvecs=self.intersectall()
        self.nounpathtots=self.compute_nounpathtotals(intersectedvecs)
        self.mostsalientvecs(intersectedvecs,self.nounpathtots,self.nounfeattots,self.nountypetots,self.nountots)

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
        elif self.option=="reduceorder":
            self.reduceorder()
        elif self.option=="maketotals":
            self.maketotals()
        elif self.option =="filter":
            self.filter()
        elif self.option == "normalise":
            self.normalise()
        elif self.option=="compose":
            self.compose()
        elif self.option=="inspect":
            self.inspect()
        elif self.option=="revectorise":
            self.revectorise()
        elif self.option=="intersect":
            self.intersect()


        else:
            print "Unknown option: "+self.option

if __name__=="__main__":
    myComposer = Composition(sys.argv[1:])
    myComposer.run()