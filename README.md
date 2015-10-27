# SentenceCompletionChallenge

Tools for working with the MSR SCC data

# About

A number of tools useful for working with APT vector files - including splitting, filtering, composing, reducing order, PPMI calculation, normalisation and composition.


# Usage

## Vector pre-processing

To preprocess the vectors output by the Java tool run:

```
python src/tools/composition.py config data/apt/piped.cfg
```

This does things like filter normalise counts, filter by frequency, etc. The conf file needs to look like this:

```
[default]
options=["split","reduceorder","maketotals","filter","normalise","maketotals","revectorise"]
filename=sample_data/test_lexicon_3/test_vectors_3.tsv
pos=J
weighting=smooth_ppmi
minorder=0 
maxorder=2
wthreshold=0.0
fthreshold=1000
saliency=0
saliencyperpath=False
normalised=False
filterfile=
comppairfile=
```

Notes:
 
 - `filterfile` and `comppairfile` are not used, but need to be included anyway (for now).
 - `filename` should be a vectors file (ask Thomas). This should be a `tsv` file like those used by Byblo.
 - need to run separately for each part of speech. Currently only `J` and `N` are supported consistently.
 - For every part of speech, you must run this script with `minorder = maxoder = 1` first. Then you can do normal order reduction, e.g. `minorder=0, maxorder=2` 
 - output file is called something like `test_vectors_3.tsv.adjs.reduce_0_2.filtered.norm.smooth_ppmi` in the same directory as the input file

 

## Composition

To compose, run the following:

```
python src/tools/nouncompounds.py data/apt/composition.cfg
```

The config file needs to look like this:

```
[default]
options=["compose"]
filename=sample_data/test_lexicon_3/test_vectors_3.tsv
pos=N
weighting=smooth_ppmi
minorder=0
maxorder=2
wthreshold=0.0
fthreshold=1000
saliency=0
saliencyperpath=False
normalised=True
filterfile=""
comppairfile=""

[compounder]
compound_file=testcompounds.txt
```

The `compound_file` options needs to point to a list of phrases to compose. Currently only noun phrases (`nn` and `amod` dependency relations) are supported. The format needs to be like this:

```
gold|nn|mine/N
gold|amod|mine/N

```

The output file is called something like `test_vectors_3.tsv.nouns.reduce_0_2.composed.norm.smooth_ppmi` in the same directory as the input file. This is again a `tsv` file.

# License

Copyright 2015 Julie Weeds

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
