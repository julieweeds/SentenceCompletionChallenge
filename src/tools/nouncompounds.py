from src.tools.composition import Composition

__author__ = 'juliewe'
# support composition of compounds and comparison with observed vectors

import sys


def union(list1, list2):
    for value in list2:
        if value not in list1:
            list1.append(value)

    return list1


class Compound:
    leftRels = {"J": ["amod", "mod"], "N": ["nn"]}
    rightRels = {"N": ["amod", "nn", "mod"], "J": []}

    def __init__(self, text):
        self.text = text
        if not self.verify():
            print("Error: incorrect format for compound " + self.text)
            exit(-1)

    def verify(self):
        if len(self.text.split('|')) == 3:
            if len(self.text.split('|')[2].split('/')) == 2:
                return True
        return False

    def getLeftLex(self):
        return self.text.split('|')[0]

    def getRel(self):
        return self.text.split('|')[1]

    def getRightLex(self):
        return self.text.split('|')[2].split('/')[0]

    def getPos(self):
        return self.text.split('|')[2].split('/')[1]

    def getWordsByPos(self, pos):
        # check not lower case for pos
        words = []
        if self.getRel() in Compound.leftRels.get(pos, []):
            words.append(self.getLeftLex() + "/" + pos)
        if self.getRel() in Compound.rightRels.get(pos, []):
            words.append(self.getRightLex() + "/" + pos)
        return words

    def toString(self):
        return self.getRel() + ":" + self.getLeftLex() + "\t" + self.getRightLex() + "\t" + self.getPos()


class DepCompounder:
    def __init__(self, config):

        try:
            self.datadir = config.get('compounder', 'datadir')
        except:
            self.datadir = ""

        self.compoundfile = self.datadir + config.get('compounder', 'compound_file')
        self.leftindex = {}
        self.relindex = {}
        self.rightindex = {}
        self.wordsByPos = {"J": [], "N": []}

    def readcompounds(self):
        print("Reading " + self.compoundfile)
        with open(self.compoundfile) as fp:
            for line in fp:
                line = line.rstrip()
                acompound = Compound(line)

                self.leftindex = self.addtoindex(acompound.getLeftLex(), self.leftindex, acompound)
                self.rightindex = self.addtoindex(acompound.getRightLex(), self.rightindex, acompound)
                self.relindex = self.addtoindex(acompound.getRel(), self.relindex, acompound)

                for pos in list(self.wordsByPos.keys()):
                    self.wordsByPos[pos] = union(self.wordsByPos[pos], acompound.getWordsByPos(pos))

    def addtoindex(self, key, index, acompound):
        """

        :type index: dict
        """
        sofar = index.get(key, [])
        sofar.append(acompound)
        index[key] = sofar
        return index

    def run(self):
        self.readcompounds()
        print("Compounder stats... ")
        print("Left index: " + str(len(list(self.leftindex.keys()))))
        print("Right index: " + str(len(list(self.rightindex.keys()))))
        print("Rel index: " + str(len(list(self.relindex.keys()))))


class NounCompounder(Composition):
    left = Composition.depPoS
    right = Composition.headPoS

    def set_words(self):
        self.words = self.myCompounder.wordsByPos[self.pos]
        if not self.words:
            self.words = ['-']

    def runANcomposition(self):
        myvectors = {}
        for rel in list(self.myCompounder.relindex.keys()):
            print("Adding feature totals")
            self.ANfeattots = self.addCompound(self.feattotsbypos[NounCompounder.left[rel]],
                                               self.feattotsbypos[NounCompounder.right[rel]], rel)  # C<*,t,f>
            print("Adding type totals")
            self.ANtypetots = self.addCompound(self.typetotsbypos[NounCompounder.left[rel]],
                                               self.typetotsbypos[NounCompounder.right[rel]], rel)  # C<*,t,*>

            self.ANvecs = {}
            self.ANtots = {}
            self.ANpathtots = {}

            for compound in self.myCompounder.relindex[rel]:
                # should check not lower case for pos
                try:
                    self.CompoundCompose(compound.getLeftLex() + "/" + NounCompounder.left[rel],
                                         compound.getRightLex() + "/" + NounCompounder.right[rel], rel)
                except KeyError:
                    print("Error: 1 or more vectors not present for " + compound.text)

            myvectors.update(
                self.mostsalientvecs(self.ANvecs, self.ANpathtots, self.ANfeattots, self.ANtypetots, self.ANtots))
        return myvectors

    def run(self):
        self.option = self.options[0]
        self.myCompounder = DepCompounder(self.config)
        self.myCompounder.run()
        self.compose()


if __name__ == "__main__":
    myCompounder = NounCompounder(["config", sys.argv[1]])
    myCompounder.run()
