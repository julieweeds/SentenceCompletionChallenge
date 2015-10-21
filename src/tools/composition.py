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



import sys,math,gzip,ast
import ConfigParser
#import json

from operator import itemgetter

try:
    import graphing
except ImportError:
    print "Warning: Unable to import graphing module"

try:
    import yaml
except ImportError:
    print "Warning: Unable to import yaml for reading composition pair file"


class Composition:


    nouns=[]
    adjectives=[]
    verbs=[]
    adverbs=[]
    others=[]

    includedtypes=[]  #all types of relation will be considered if this is empty
    featmax=3  #how many features of each path type to display when showing most salient features

    ppmithreshold=0
    filterfreq=1000
    saliency=0
    saliencyperpath=False

    headPoS={"nn":"N","amod":"N"}
    depPoS={"nn":"N","amod":"J"}

    def __init__(self,options):

        if options[0] == "config":
            self.configure(options[1]) # configure via configuration file
        else:
            #configure via command line options
            # parameter0 = function
            self.options=[options[0]]

            # parameter1 or default = original input file name (in current working directory)
            if len(options)>1:
                self.inpath=options[1]
            else:
                print "Requires the base filename as second input"

            #parameter2 = pos to be considered (necessary for all functions other than split).  If not given = N
            if len(options)>2:
                self.pos=options[2]
            else:
                self.pos="N"

            #parameter3 = minimum order of dependency relation to include
            #parameter4 = maximum order of dependency relation to include
            #parameter3 can = X if you want to set further options without setting this (i.e., work with all orders given)

            if len(options)>3 and not options[3]=="X":

                self.minorder=int(options[3])
                self.maxorder=int(options[4])
                self.reducedstring=".reduce_"+str(self.minorder)+"_"+str(self.maxorder)
            else:
                self.minorder=0
                self.maxorder=2
                self.reducedstring=""

            #optional parameters.  Can be anywhere from parameter4 onwards
            #type of ppmi calculation: default = ppmi, alternatives are gof_ppmi (where probabilities are calculated over all types rather than on a path type basis)
            #   and pnppmi (where standard ppmi calculation is multiplied by path probability)
            #normalised: this is required so that the result of the normalisation function can be used as input to a future function e.g. revectorisation or composition

            self.pp_normal= "pp_normalise" in options or "pnppmi" in options #include one of these flags in order for PPMI values to be multiplied by path probability in final vectors
            self.gof_ppmi="gof_ppmi" in options
            self.normalised = "normalise" in options or "normalised" in options #this may be the main option (to carry out normalisation) or be included as one of the optional options so that normalised counts are used

            self.ppmithreshold=Composition.ppmithreshold
            self.filterfreq=Composition.filterfreq
            self.saliency=Composition.saliency
            self.saliencyperpath=Composition.saliencyperpath

          #suffixes for pos
        self.nounfile=self.inpath+".nouns"
        self.verbfile=self.inpath+".verbs"
        self.adjfile=self.inpath+".adjs"
        self.advfile=self.inpath+".advs"
        self.otherfile=self.inpath+".others"
        #these are dictionaries which will hold vectors and totals
        self.nounvecs={}
        self.adjvecs={}
        self.nountots={}
        self.nounfeattots={}
        self.adjtots={}
        self.adjfeattots={}

        #if present load phrases for composition
        # and set words/paths of interest

        if self.comppairfile!="":
            with open(self.comppairfile) as fp:
                self.comppairlist = yaml.safe_load(fp)
        else:
            self.comppairlist=[]
        self.set_words()
        self.includedtypes=Composition.includedtypes


    def configure(self,filename):
        #load and configure
        print "Reading configuration from "+filename
        #with open(filename) as fp:
            #config=json.load(fp,encoding="ascii")
        #    config=yaml.safe_load(fp)
        config=ConfigParser.RawConfigParser()
        config.read(filename)

        self.options=ast.literal_eval(config.get('default','options'))

        self.inpath=config.get('default','filename')
        self.pos=config.get('default','pos')
        mini = config.get('default','minorder')
        maxi = config.get('default','maxorder')
        if mini == "X":
            self.minorder=0
            self.maxorder=2
            self.reducedstring=""
        else:
            self.minorder=int(mini)
            self.maxorder=int(maxi)
            self.reducedstring=".reduce_"+str(mini)+"_"+str(maxi)

        self.weighting=config.get('default','weighting')
        self.pp_normal=(self.weighting=="pnppmi" or self.weighting=="pp_normalise")
        self.gof_ppmi=(self.weighting=="gof_ppmi")
        self.smooth_ppmi=(self.weighting=="smooth_ppmi" or self.weighting=="smoothed_ppmi")
        self.normalised=(config.get('default','normalised')=="True") or self.options[0]=="normalise"
        self.ppmithreshold=float(config.get('default','wthreshold'))
        self.saliency=int(config.get('default','saliency'))
        self.saliencyperpath=config.get('default','saliencyperpath')
        self.filterfreq=int(config.get('default','fthreshold'))
        self.comppairfile=config.get('default','comppairfile')
        self.filterfile=config.get('default','filterfile')

        return
    #----HELPER FUNCTIONS

    #-----
    # set the words of interest
    #1) if self.comppairfile set, add the appropriate member of pair form self.comppairlist to self.words
    #2) elseif filterfile not present, add any nouns/adjectives in defaults
    # 3) elseif filterfile is present, add these words to self.words
    #-----
    def set_words(self):

        if self.comppairfile!="":
            if self.pos=="J":
                index=2
            else:
                index=0
            self.words=[]
            for pair in self.comppairlist:
                if not pair[index] in self.words:
                    self.words.append(pair[index])


        elif self.filterfile=="":
            if self.pos=="N":
                self.words=Composition.nouns
            elif self.pos=="J":
                self.words=Composition.adjectives
            elif self.pos=="V":
                self.words=Composition.verbs
            elif self.pos=="R":
                self.words=Composition.adverbs
            else:
                self.words=Composition.others
        else:
            with open(self.filterfile) as fp:
                self.wordlistlist=yaml.safe_load(fp)
            self.words=[]
            for wordlist in self.wordlistlist:
                self.words+=wordlist
        print "Setting words of interest: ",self.words


    #----
    #boolean function as to whether a word is in self.words or self.words=[]
    #-----
    def include(self,word):
        if len(self.words)==0:
            return True
        elif word in self.words:
            return True
        else:
            return False

    #---
    #boolean function as to whether a pathtype is in self.includedtypes or self.includedtypes=[]
    #----
    def typeinclude(self,pathtype):
        if self.includedtypes==[]:
            return True
        else:
            return pathtype in self.includedtypes

    #---
    #generate the input file string according to POS
    #---
    def selectpos(self):
        if self.pos=="N":
            infile=self.nounfile
        elif self.pos=="V":
            infile=self.verbfile
        elif self.pos=="J":
            infile=self.adjfile
        elif self.pos=="R":
            infile=self.advfile
        elif self.pos=="AN":
            infile=self.inpath+".ans"
        else:
            infile=self.nounfile

        return infile

    #----
    #get the path prefix / dependency path of a given feature
    #self.getpathtype("amod:red") = amod
    #self.getpathtype("_dobj>>amod:red") = _dobj>>amod
    #----
    def getpathtype(self,feature):
        #get the path of a given feature
        fields=feature.split(":")
        return fields[0]

    #----
    #get the path value of a given feature
    #self.getpathvalue("amod:red")=red
    #self.getpathvalue("_dobj>>amod:red") = red
    #----
    def getpathvalue(self,feature):
        fields=feature.split(":")
        if len(fields)>1:
            return ":"+fields[1]
        else:
            #print "No feature value for "+feature
            return ""

    #----
    #get the order of a given feature
    #----
    def getorder(self,feature):
        path=self.getpathtype(feature)

        if path=="":
            order=0
        else:
            fields=path.split("\xc2\xbb")
            order=len(fields)

        return order

    #---
    #split a higher order feature / find path prefix
    #0th order e.g., :red => return ("","")
    #1st order e.g., amod:red =>  return ("amod:red","")
    #2nd order e.g., _dobj>>amod:red => return ("_dobj","amod:red:)
    #3rd order e.g., nsubj>>_dobj>>amod:red => return ("nsubj","dobj>>amod:red")
    #----
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

    #---
    #turn alist into a string concatenated using the achar
    #---
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

    #----MAIN FUNCTIONS

    #----
    #SPLIT
    #take the original gzipped file and split it by POS
    #----
    def splitpos(self):

        nouns=open(self.nounfile,"w")
        verbs=open(self.verbfile,"w")
        adjs=open(self.adjfile,"w")
        advs=open(self.advfile,"w")
        others=open(self.otherfile,"w")


        infile=self.inpath+".gz"

        try:
            instream=gzip.open(infile)
        except:
            instream=open(self.inpath)


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
        instream.close()
        return

    #----
    #REDUCEORDER
    #generally used after SPLIT
    #remove dependencies which do not have an order within the thresholds set by minorder and maxorder
    #note that
    # :gunman/N etc is considered to be a 0th order dependency
    #_dobj:shoot/V is a 1st order dependency
    # _dobj:nsubj:man/N is a 2nd order dependency
    #-------
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


    #----
    #MAKETOTALS
    #calculate row and column totals
    #this is usually done before filtering and also after filtering and normalisation
    #------

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

                if lines%1000==0:print "Processing line "+str(lines)
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

    #---
    #subsequenct functions in pipeline can load pre-calcualated row totals using this function
    #---
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
                if self.normalised or float(fields[1])>self.filterfreq:
                    totals[fields[0]]=float(fields[1])
        print "Loaded "+str(len(totals.keys()))

        return totals

    #---
    #subsequent functions in pipeline can load pre-calculated column totals using this function
    #----
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
                if self.normalised or float(fields[1])>self.filterfreq:
                    totals[fields[0]]=float(fields[1])
        print "Loaded "+str(len(totals.keys()))
        return totals


    #---
    #FILTER
    #filter by frequency and by words of interest
    #make sure filterfile and comppairfile etc are undefined if you want vectors for all words above threshold frequency
    #no threshold on individual event frequencies, only on entry/row and feature/column totals.
    #----
    def filter(self):

        infile = self.selectpos()+self.reducedstring
        outfile=infile+".filtered"

        coltotals= self.load_coltotals()
        savereducedstring=self.reducedstring
        self.reducedstring=".reduce_1_1" #always use same rowtotals for filtering whatever the reduction
        rowtotals = self.load_rowtotals()
        self.reducedstring=savereducedstring
        outstream=open(outfile,"w")
        print "Filtering for words ",self.words
        print "Filtering for frequency ",self.filterfreq
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
                if entrytot>self.filterfreq and self.include(entry):
                    outline=entry
                    #print "Filtering entry for "+entry
                    while len(features)>0:
                        freq=features.pop()
                        #feat=features.pop().lower()
                        feat=features.pop()
                        feattot=float(coltotals.get(feat,0))
                        #print feat+"\t"+str(feattot-self.filterfreq)

                        if feattot>self.filterfreq:
                            outline+="\t"+feat+"\t"+freq
                            nofeats+=1

                    if nofeats>0:
                        outstream.write(outline+"\n")
                else:
                    print "Ignoring "+entry+" with frequency "+str(entrytot)

        outstream.close()

    #----
    #NORMALISE
    #this option normalises vectors so that they "sum to 1"
    #however they won't actually sum to 1 as row totals are computed before filtering
    #so necessary to call maketotals again after normalise
    #-----
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
        self.normalised=True

    #---
    #load in pre-filtered and (optionally) normalised vectors
    #----
    def load_vectors(self,infile=""):
        if infile=="":
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

    #----
    #write a set of vectors to file
    #these could be raw or PPMI vectors
    #----
    def output(self,vectors,outfile):
        #write a set of vectors to file
        print "Writing vectors to output file: "+outfile
        with open(outfile,"w") as outstream:
            for entry in vectors.keys():
                vector=vectors[entry]
                print entry
                #print vector
                if len(vector.keys())>0:
                    outstring=entry
                    ignored=0
                    nofeats=0
                    for feat in vector.keys():
                        forder=self.getorder(feat)

                        if forder>=self.minorder and forder<=self.maxorder:

                            try:
                                outstring+="\t"+feat+"\t"+str(vector[feat])
                                nofeats+=1
                            except:
                                ignored+=1
                    print "Ignored "+str(ignored)+" features"
                    if nofeats>0:
                        outstream.write(outstring+"\n")




    #----SALIENCY FUNCTIONS

    #---
    #use the totals for each feature to compute grand totals for each feature type (e.g., "amod")
    #this is C<*,t,*> and is computed by S_f C<*,t,f>
    #----
    def compute_typetotals(self,feattots):
        #compute totals for different paths over all entries (using column totals given in feattots)
        print "Computing path totals C<*,t,*>"
        typetots={}
        for feature in feattots.keys():
            pathtype=self.getpathtype(feature)
            sofar=typetots.get(pathtype,0.0)
            typetots[pathtype]=sofar+float(feattots[feature])

        return typetots

    #--
    #compute path totals for each noun
    #i.e., C<w1,t,*>
    #this is needed in the standard PPMI calculation we use
    #----
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

    #----
    #compute ppmi (or similar) for a set of vectors and return new set of vectors
    #@vecs: dict of dicts representing a set of vectors for which PPMI calculations to be carried out on i.e., vectors[w1][p:w2]=f  => C<w1,p,w2>=f
    #@pathtotals: dict of dicts representing a set of totals indexed by entry and path i.e., pathtots[w1][p] = f => C<w1,p,*> = f
    #@feattots: dict where feattots[p:w2]=f => C<*,p,w2>=f
    #@typetots: dict where typetots[p]=f => C<*,p,*>=f
    #@entrytots: dict where entrytots[w1]=f => C<w1,*,*>=f
    #
    #TODO: play with PPMI threshold and/or number of features
    #-----

    def computeppmi(self,vecs,pathtots,feattots,typetots,entrytots):

        ppmivecs={}
        grandtot=0.0
        if self.pp_normal:
            print "Computing pnppmi"
        elif self.gof_ppmi:
            print "Computing gof_ppmi"
            for type in typetots.keys():
                grandtot+=float(typetots[type])
            if self.smooth_ppmi:
                grandtot=math.pow(grandtot,0.75)

                #print type, grandtot
        else:
            print "Computing ppmi"
        done =0
        todo=len(vecs.keys())

        for entry in vecs.keys():

            ppmivector={}

            vector=vecs[entry]
            for feature in vector.keys():
                freq=float(vector[feature])  # C<w1,p,w2>
                total=float(pathtots[entry][self.getpathtype(feature)]) # C<w1,p,*>
                feattot=float(feattots[feature]) #C<*,p,w2>
                typetot=float(typetots[self.getpathtype(feature)]) #C<*,p,*>
                entrytotal=float(entrytots[entry]) # C<w1,*,*>

                if self.smooth_ppmi:
                    feattot=math.pow(feattot,0.75)
                    typetot=math.pow(typetot,0.75)

                if self.gof_ppmi:

                    pmi=math.log10((freq*grandtot)/(feattot*entrytotal))
                else:
                    pmi=math.log10((freq*typetot)/(feattot*total))

                if pmi>self.ppmithreshold:
                    if self.pp_normal:

                        pmi=pmi * total/entrytotal
                    ppmivector[feature]=pmi

            done+=1
            if done%1000==0:
                percent=done*100.0/todo
                print "Completed "+str(done)+" vectors ("+str(percent)+"%)"



            ppmivecs[entry]=self.mostsalient_vector(ppmivector)
            #print ppmivector
        return ppmivecs

    #-----
    #REVECTORISE
    #load the appropriate vectors and totals files, compute more totals, compute PPMI and output the returned vectors
    #------
    def revectorise(self):

        if self.normalised:
            suffix=".norm"
        else:
            suffix=""
        if self.pp_normal:
            suffix += ".pnppmi"
        elif self.gof_ppmi:
            suffix += ".gof_ppmi"
        elif self.smooth_ppmi:
            suffix += ".smooth_ppmi"
        else:
            suffix += ".ppmi"
        if self.ppmithreshold>0:
            suffix+="_"+str(self.ppmithreshold)
        if self.saliency>0:
            if self.saliencyperpath:
                suffix+=".spp_"+str(self.saliency)
            else:
                suffix+=".sal_"+str(self.saliency)
        outfile=self.selectpos()+self.reducedstring+".filtered"+suffix
        self.nounvecs=self.load_vectors()
        self.nounfeattots=self.load_coltotals()
        self.nountots=self.load_rowtotals()
        self.nounpathtots=self.compute_nounpathtotals(self.nounvecs)
        self.nountypetots=self.compute_typetotals(self.nounfeattots)

        ppmivecs=self.computeppmi(self.nounvecs,self.nounpathtots,self.nounfeattots,self.nountypetots,self.nountots)
        self.output(ppmivecs,outfile)


    #---
    #use POS to determine which vectors/totals to supply to self.mostsalientvecs
    #----
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

        return self.mostsalientvecs(vecs,tots,feattots,typetots,entrytots)

    #---
    #compute PPMI and then only retain the most salient features (up to featmax for each includedtype)
    #does not modify ppmivectors
    #primary purpose has been to compute complete vectors to output to file but display the most salient ones for inspection
    #-----
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
                if done<Composition.featmax and self.typeinclude(pathtype):
                    print feature+" : "+str(tuple[1])+" ("+str(vecs[entry][feature])+")"
                donetypes[pathtype]=done+1

            print donetypes
            print "-----"
        return ppmivecs

    #-----
    #take a vector and retain only the most highly weighted features
    #-----
    def mostsalient_vector(self,ppmivector):

        if self.saliency>0:
            newvector={}
            feats=sorted(ppmivector.items(),key=itemgetter(1),reverse=True)
            donetypes={}
            all=0
            for tuple in feats:
                feature=tuple[0]
                pathtype=self.getpathtype(feature)
                done=donetypes.get(pathtype,0)
                if self.typeinclude(pathtype) and ((self.saliencyperpath and done<Composition.saliency)or(not self.saliencyperpath and all<Composition.saliency)):
                    newvector[feature]=tuple[1]
                    donetypes[pathtype]+=1
                    all+=1
            return newvector
        else:
            return ppmivector
    #----
    #INSPECT
    #display the path distribution graph for a set of noun vectors and the most salient feature for those vectors
    #-----
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

    #----COMPOSITION FUNCTIONS

    #----
    #COMPOSE
    #load appropriate vectors, display most salient features for each vector, then runANcomposition and output to file
    #----
    def compose(self):

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
        if self.ppmithreshold>0:
            suffix+="_"+str(self.ppmithreshold)
        if self.saliency>0:
            if self.saliencyperpath:
                suffix+=".spp_"+str(self.saliency)
            else:
                suffix+=".sal_"+str(self.saliency)
        outfile=self.selectpos()+self.reducedstring+".composed"+suffix
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

        self.output(self.runANcomposition(),outfile)



    #----
    #run ANcompose for each adjective, noun pair of interest
    #then run mostsalientvecs on ANvecs which cause PPMI to be computed, most salient features displayed and PPMI vectors returned for output
    #----
    def runANcomposition(self):

        self.ANfeattots=self.addAN(self.adjfeattots,self.nounfeattots)  #C<*,t,f>
        self.ANtypetots=self.addAN(self.adjtypetots,self.nountypetots)  #C<*,t,*>
       #print ANtypetots

        self.ANvecs={}
        self.ANtots={}
        self.ANpathtots={}

        if self.comppairfile:
            for comppair in self.comppairlist:
                 self.ANcompose(comppair[2],comppair[0])



        else:

            for adj in self.adjectives:
                for noun in self.nouns:
                    self.ANcompose(adj,noun)  #C<an,t,f>

                    #print ANvecs,ANtots


        return self.mostsalientvecs(self.ANvecs,self.ANpathtots,self.ANfeattots,self.ANtypetots,self.ANtots)

    #----
    #for a given adjective and noun, compute the compsed vector using addAN and the appropriate composed totals
    #add these to the dicts for ANs
    #----
    def ANcompose(self,adj,noun):
        self.CompoundCompose(adj,noun,"mod")

    def CompoundCompose(self,dep,head,rel):
        hdpos=Composition.headPoS.get(rel,"N")
        dppos=Composition.depPoS.get(rel,"J")

        if hdpos=="N":
            headvector=self.nounvecs[head]
            headpathtots=self.nounpathtots[head]
            headtot=self.nountots[head]
        else:
            headvector=self.adjvecs[head]
            headpathtots=self.adjpathtots[head]
            headtot=self.adjtots[head]

        if dppos=="N":
            depvector=self.nounvecs[dep]
            deppathtots=self.nounpathtots[dep]
            deptot=self.nountots[dep]
        else:
            depvector=self.adjvecs[dep]
            deppathtots=self.adjpathtots[dep]
            deptot=self.adjtots[dep]

        entry=dep+"|"+rel+"|"+head
        self.ANvecs[entry]=self.addCompound(depvector,headvector,rel)
        self.ANpathtots[entry]=self.addCompound(deppathtots,headpathtots,rel)
        self.ANtots[entry]=float(deptot)+float(headtot)


    #----
    #add an adjective vector to a noun vector (may be feature vectors or path vectors)
    #do this by offsetting the adjective vector so that it is aligned with the noun vector
    #then add noun vector to adjective vector
    #----
    def addCompound(self,depvector,headvector,rel):

        offsetvector = self.offsetVector(depvector,rel)

        COMPOUNDvector={}
        #print "Processing noun features "+str(len(nounvector.keys()))
        count=0
        intersect=[]
        #print nounvector
        #print adjvector
        for feature in headvector.keys():
            count+=1
            if feature in offsetvector:
                COMPOUNDvector[feature]=float(headvector[feature])+float(offsetvector[feature])
                intersect.append(feature)
                offsetvector.__delitem__(feature)
            else:
                COMPOUNDvector[feature]=headvector[feature]
            if count%10000==0:print"Processed "+str(count)

        print "Intersecting features: "+str(len(intersect))
        #print "Processing remaining adj features "+str(len(adjvector.keys()))+" : reduced to : "+str(len(offsetvector.keys()))
        COMPOUNDvector.update(offsetvector)
        #print "Complete"
        return COMPOUNDvector

    def addAN(self,adjvector,nounvector):
        return self.addCompound(adjvector,nounvector,"mod")

    #----
    #offset an adjective vector so that it aligns with the noun vector it is modifying
    #----
    def offsetAN(self,adjvector):
        return self.offsetVector(adjvector,"mod")

    def offsetVector(self,depvector,rel):
        depPREFIX="_"+rel
        headPREFIX=rel

        offsetvector={}
        incomp=0
        for feature in depvector.keys():
            (prefix,suffix)= self.splitfeature(feature)
            if prefix==depPREFIX:
                newfeature=suffix+self.getpathvalue(feature)
            elif prefix.startswith("_"):
                #incompatible feature for composition
                #print "Incompatible feature for composition: "+feature
                incomp+=1
                newfeature=""
            elif feature.startswith(":"):
                newfeature=headPREFIX+feature
            else:
                newfeature=headPREFIX+"\xc2\xbb"+feature
            if not newfeature == "":
                offsetvector[newfeature]=depvector[feature]
        #print "Features in original adj vector: "+str(len(adjvector.keys()))
        #print "Incompatible features in adjective vector: "+str(incomp)
        #print "Features in offset adj vector: "+str(len(offsetvector.keys()))
        return offsetvector

    #---
    #add two vectors
    #not used I think
    #---
    def add(self,avector,bvector):
        rvector=dict(avector)
        for feat in bvector.keys():
            rvector[feat]=rvector.get(feat,0)+bvector[feat]
        return rvector


    #----OTHER FUNCTIONS

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




    def rewrite(self):
        self.output(self.load_vectors(self.inpath),self.inpath+".new")

    #----main run function
    def run(self):

        while len(self.options)>0:
            self.option=self.options[0]
            self.options=self.options[1:]

            print "Stage: "+self.option
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
            elif self.option=="rewrite":
                self.rewrite()


            else:
                print "Unknown option: "+self.option



if __name__=="__main__":

    #----
    #example runs:
    #python composition.py split filename
    #python composition.py reduceorder filename N 1 2
    #python composition.py maketotals filename N 1 2
    #python composition.py filter filename N 1 2
    #python composition.py normalise filename N 1 2
    #python composition.py revectorise filename N 1 2 ppmi
    #python composition.py compose filename AN 0 2 normalised pnppmi
    #-----

    myComposer = Composition(sys.argv[1:])
    myComposer.run()