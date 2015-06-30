__author__ = 'juliewe'
#17/6/15

def configure(arguments):
    parameters={}
    parameters["thesfile"]="wiki-lc.sims.neighbours.strings"
    parameters["thesdir"]="/home/j/ju/juliewe/Documents/workspace/SentenceCompletionChallenge/data/apt/"
    #parameters["thesdir"]="/home/j/ju/juliewe/Documents/workspace/ThesEval/data/wikiPOS_t100f100_nouns_deps/"
    #parameters["thesfile"]="neighbours.strings"


    parameters["wn_sim"]="path"
    return parameters