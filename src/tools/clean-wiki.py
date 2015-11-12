__author__ = 'juliewe'
#chunk and clean the wiki-20pageviews before parsing
import re

linePATT = re.compile('wikipedia-\d+,\"(.*)\"')
linePATT2 = re.compile('wikipedia-\d+,(.*)')

def chunkNclean(infile,outdir,chunksize=100):
    with open(infile) as instream:
        fileopen=False
        for index,line in enumerate(instream):
            if index%chunksize==0:
                if fileopen:
                    outstream.close()
                    print "Closing file "+outfile

                chunkno=(index/chunksize)+1
                outfile=outdir+"wiki-chunk"+str(chunkno)
                outstream=open(outfile,"w")
                fileopen=True
            line =line.rstrip()
            matchobj=linePATT.match(line)
            if matchobj:
                cleanline=matchobj.groups()[0]
                outstream.write(cleanline+"\n")
            else:
                matchobj=linePATT2.match(line)
                if matchobj:
                    cleanline=matchobj.groups()[0]
                    outstream.write(cleanline+"\n")
                else:
                    print "Error cleaning line "+str(index)
                    print line








if __name__=="__main__":
    filename="wikipedia_utf8_filtered_20pageviews.csv"
    outdir="wiki-raw/20pageviews/"
    chunkNclean(filename,outdir)
