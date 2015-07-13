__author__ = 'juliewe'
#useful graphing functions for display
#mainly for import
#7/7/15

import numpy as np
import matplotlib.pyplot as plt


def display_bargraph(adict,title="",max=10):
    #labels are keys
    #values are frequencies
    print adict
    adict = filter(adict, max)
    print adict
    labels=charcheck(adict.keys())
    freqs=adict.values()
    fig=plt.figure()
    width=0.75
    ind = np.arange(len(freqs))
    plt.bar(ind,freqs)
    plt.xticks(ind+width/2,labels)
    plt.title(title)
    plt.show()

def charcheck(alist):
    blist=[]
    for entry in alist:
        if "\xc2\xbb" in entry:
            fields=entry.split("\xc2\xbb")
            newentry=fields[0]
            for field in fields[1:]:
                newentry+="::"+field
            blist.append(newentry)
        else:
            blist.append(entry)

    return blist

def filter(adict,max):


    myvalues=adict.values()
    if max<len(myvalues):
        bdict={}
        myvalues.sort(reverse=True)
        cutoff=myvalues[max]
        for key in adict.keys():
            if adict[key]>cutoff:
                bdict[key]=adict[key]

        return bdict
    else:
        return adict
if __name__=="__main__":
    testdict={"dep\xc2\xbbparataxis":10,"dep":1413,"mod":307}
    display_bargraph(testdict,"A bar chart",max=2)