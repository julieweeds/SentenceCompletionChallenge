__author__ = 'juliewe'
#17/6/2015
import sys
from .conf import configure
from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic as wn_ic


class Analyser:
    k=10
    posdict={'N':wn.NOUN,'J':wn.ADJ}
    max=0
    synsetthresh=3
    totalthresh=0.3
    propthresh=0.4
    simthresh=0.1
    simmetric="path"


    def __init__(self,parameters):

        self.parameters=parameters
        self.wn_sim=self.parameters.get("wn_sim",Analyser.simmetric)
        self.ic=wn_ic.ic('ic-semcor.dat')
        self.candidates={}
        self.synsetthresh=self.parameters.get("synset_thresh",Analyser.synsetthresh)
        self.totalthresh=self.parameters.get("total_thresh",Analyser.totalthresh)
        self.propthresh=self.parameters.get("prop_thresh",Analyser.propthresh)
        self.simthresh=self.parameters.get("sim_thresh",Analyser.simthresh)

    def strippos(self,word):
        fields=word.split("/")
        if len(fields)>1:
            return fields[0]
        else:
            return word

    def getPOS(self,word):
        fields=word.split('/')
        if len(fields)>1:
            return fields[1][0]
        else:
            return 'X'

    def findsim(self,s1,s2):
        if self.wn_sim=="path":
            return s1.path_similarity(s2)
        elif self.wn_sim=="lch":
            return s1.lch_similarity(s2)
        elif self.wn_sim=="wup":
            return s1.wup_similarity(s2)
        elif self.wn_sim=="res":
            return s1.res_similarity(s2,self.ic)
        elif self.wn_sim=="jcn":
            return s1.jcn_similarity(s2,self.ic)
        elif self.wn_sim=="lin":
            return s1.lin_similarity(s2,self.ic)


    def updatedist(self,dist,synsets,neigh,sim,apos):


        sofar=-1
        max=0
        try:
            nsynsets=wn.synsets(neigh.lower(),pos=apos)
        except:
            #print "Cannot get synsets for neighbour "+neigh
            nsynsets=[]

        for e in synsets:
            for n in nsynsets:
                wnsim=self.findsim(e,n)
                if wnsim>max:
                    max=wnsim
                    sofar=e

        if max>0:
            dist[sofar]=dist.get(sofar,0)+max*sim
        return dist


    def processline(self,line):
        fields=line.split("\t")
        entry=fields[0]
        word=self.strippos(entry).lower()
        apos=self.posdict.get(self.getPOS(entry),'X')
        if apos==self.posdict.get('N','X'):
            try:
                synsets=wn.synsets(word,pos=apos)
                if len(synsets)>1:
                    print(word,apos,len(synsets))
                    neighs=fields[1:(Analyser.k*2+1)]
                    neighs.reverse()
                    sensedist={}
                    while len(neighs)>0:
                        neigh=neighs.pop()
                        sim=neighs.pop()
                        sensedist=self.updatedist(sensedist,synsets,self.strippos(neigh),float(sim),apos)

                    #print entry, sensedist

                    return self.selectcandidate(entry,sensedist)
                else:
                    return False

            except:
                #print "Cannot get synsets for entry "+word
                return False


    def selectcandidate(self,entry,dist):

        if len(list(dist.keys()))>1 and len(list(dist.keys()))<self.synsetthresh:

            total=0
            for value in list(dist.values()):
                total+=value

            if total>self.totalthresh:
                minprop=1
                for value in list(dist.values()):
                    prop=value/total
                    if prop<minprop:
                        minprop=prop

                if minprop>self.propthresh:

                    totalsim=0
                    count=0
                    for value1 in list(dist.keys()):
                        for value2 in list(dist.keys()):
                            if value1 != value2:
                                totalsim+=self.findsim(value1,value2)
                                count+=1
                    avsim=totalsim/count
                    if avsim<self.simthresh:
                        # hyps=0
                        # for value1 in dist.keys():
                        #     if len(value1.hyponyms())>0:
                        #         hyps+=1
                        # if hyps>1:
                        #     self.candidates[entry]=dist
                        self.candidates[entry]=dist
                        return True
        return False


    def processfile(self):
        infile=self.parameters["thesdir"]+self.parameters["thesfile"]
        outfile=infile+".filtered"
        lines=0
        with open(outfile,'w') as outstream:
            with open(infile) as instream:
                for line in instream:
                    lines+=1
                    line=line.rstrip()
                    if self.processline(line):
                        outstream.write(line+"\n")
                    if Analyser.max>0 and lines>Analyser.max:
                        break

    def displaycandidates(self):

        print("----Starting display of candidates----")
        for cand in list(self.candidates.keys()):
            dist = self.candidates[cand]
            print(cand)
            for synset in list(dist.keys()):
                print(synset.name(),synset.definition(),dist[synset])
                hypstring=""
                for hyp in synset.hyponyms():
                    hypstring+=hyp.name()+"\t"
                print(hypstring)
            print("----")

    def run(self):
        self.processfile()
        self.displaycandidates()

if __name__=="__main__":
    myAnalyser=Analyser(configure(sys.argv))
    myAnalyser.run()

