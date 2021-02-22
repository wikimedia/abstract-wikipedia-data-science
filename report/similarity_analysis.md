# Introduction

In the world of various wikimedia projects, Lua modules are used extensively to perform basic (calculate age, location) to more complex functions (rendering templates). With Abstract Wikipedia the aim is to consolidate knowledge in a language-independent way. The knowledge is rendered in any languages as required using the 'knowledge of language' stored in wikidata. To this end, the reservoir of Lua modules that we have scattered among wikis need to be gathered as well. In this project our aim was to find out which modules are more important to be merged first (priority detection [T272003](https://phabricator.wikimedia.org/T272003)) and what are the various modules similar to them (similarity detection), so that they can be merged.

# What is code similarity?

In our case we want to provide users with a list of modules that possibly perform the same functions across wikis and so can be merged into one for Abstract Wikipedia. Figuring out code functionality is hardly possible though computation, so we opt to search for code that 'look' similar and let users decide if they really do the same thing (they should do something similar atleast). We've experiemented with multiple ways to group modules together which I describe below. But first let's look at the types of modules available.

# Types of modules

Modules are not only functions but also places to store a bit of data, like list pronounciation, longitude-latitude of places etc. Looking at the distribution of the length of modules, we see lots of modules with very large character count. On analysis we find that most of these are infact data modules and not some very large convoluted lua function. To find similar modules, we therefore separate data modules and include the option for users to view either all modules, or modules that are only functions.

Data modules were isolated in this task [T273767](https://phabricator.wikimedia.org/T273767).

# Clustering modules

To group modules we start with distance based analysis of modules and use those distances as features to perform clustering using various algorithms. Later distance based methods were found to be slow and requiring excessive memory (pair-wise distances require n^2 memory where n=300k modules). Considering code contains much overlap with regular text, we can find code pieces that look similar. So we train models to project modules in high-dimentional vectors and use these as features instead of the actual code to perform clustering. So there are mainly 2 things to choose: Features and Clustering algorithm. Brief description of the features and how they were used in various algorithms is given below.

## Features

1. **Levenshtein distance:** Levenshtein distance between two sequence is the minimum number of single-character edits (insertions, deletions or substitutions) required to change one word into the other ([Wkipedia](https://en.wikipedia.org/wiki/Levenshtein_distance)). Basically this distance can tell us how similar two modules are, and to normalize caracter counts we divide the count by the sum of lengths of the two modules.

   `Lev(A,B) = Levenshtein_distance(A,B)/( Length(A) + Length(B) )`

   One idea was to use diffing (like in git). Analysing some plagarism detection algorithms I found that Levenshtein distance covers it already in a better way and the memory footprint for diffing is not any lower. This distance matrix was then used as input to various clustering algorithms.

   Note: I also looked into using plagarism detector as a way to find similar codes but unfortunately none was found comptible for Lua codes.

2. **Levenshtein distance (dimentionality reduced with MDS):** Not all algorithms can take in raw distance matrixes. The traditional KMeans cannot, and so it is necessary to reduce the dimentionality of this matrix using MDS ([Multidimensional scaling](https://en.wikipedia.org/wiki/Multidimensional_scaling)). PCA is not suitable for distance matrices. Then the new matrix is used for clustering.

3. **Tf-idf:** [Td-idf](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) is the most common method to represent any text in numeric form. For each token it calculates a value representing importance of the token in the corpus. tf-idf of tokens along with n-grams of tokens give better representation of the document to be used as feature.

4. **Word Embedding:** Word embeddings are high-dimentional vectors that represent each token and have values such that similar tokens are nearer in the vector space than un-related tokens. A word-embedding model (fasttext in our case) has to be trained only once and then vector representation of any word ca be generated from the trained model. A representation of word embeddings in 2d plane is shown below, some simialar words are seen nearby.

![](img/WE_map.png)

Since it gives us an embedding for each token, the way to get embedding for the whole module can be one of two ways:

- Averaged Embeddings: Average all word-embeddings, so it gives us a small vector for each module. Altough it sounds hacky, this method actually works for numerous text processing systems like document classification, sentiment analysis etc.
- Concatenated Embeddings: Instead of averaging, all embeddings are concatenated together. This requires fixing a length for wach module. Longer code is trucated, shorter ones are post-padded.

5. **Document Embedding:** Doc2Vec can be used to get a embedding for the whole document in one shot. This also is trained once and embedding for any document is generated on the go. A sample of doc2vec embedings reduced to 2 dimentions is plotted below with the module titles.

![](img/docEmb_map.png)

6. **Code Embedding:** So far text-analysis based methods have been used to numericalize Lua modules. Some models are available to project specifically 'codes' into a vector space (e.g [Code2Vec](https://code2vec.org/)). Unfortunately most available models are trained in populalar languages like Python, C++, Java etc. To train Lua codes in these models some time must be spent understanding and creating a `Lua extractor` which takes in raw Lua codes and uses ASTs of codes to produce input that the model can then take in. We have not ventured into these territories yet but a trained Lua Code2Vec can be beneficial for lots of other tasks as well. Something we can look into later.

## Clustering Algorithms

1. Naive method
2. KMeans
3. Affinity Propagation
4. Heirarchical Clustering
5. DBSCAN
6. OPTICS

## Summary of pros and cons

(with 500 random modules)

| Feature                      | Clustering Algo      | Time                                                       | Memory                                                                                                         | clusters                                                                                                                                           |
| ---------------------------- | -------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Levenshtein                  | dbscan               | instant                                                    | memory runs out with all modules (as Levenshtein creates nxn matrix )                                          | Lots of small clusters and too many noise detected                                                                                                 |
| Levenshtein                  | affinity propagation | instant                                                    | -                                                                                                              | Most in 2-3 clusters, rest are individual clusters (size=1)                                                                                        |
| Levenshtein                  | heirarchical         | instant                                                    | -                                                                                                              | Similar to affinity propagation                                                                                                                    |
| Levenshtein                  | KMeans (after MDS)   | bit slow                                                   | memory runs out with large number of clusters                                                                  | Elbow method to find `number of cluster` parameter. Evenly sized clusters but modules within clusters are not highly realted                       |
| Tf-idf                       | KMeans               | tfidf is really slow                                       | runs out of memory on tf-idf step for all data (estimated amount of memory required is too high >1000s of GBs) | Detects reLevenshteinant clusters and cluster sizes are medium with only a few noise clusters (cluster of all modules that dont fit anything else) |
| Tf-idf                       | DBSCAN               | tfidf is really slow                                       | runs out of memory on all data due to Tf-idf                                                                   | Better than Levenshtein DBSCAN but still a lot of noise                                                                                            |
| Word Embedding (FastText)    | KMeans               | Embedding all data takes 12 hours, but is a one time thing | -                                                                                                              | Clusters have long tail and arent as related either                                                                                                |
| Word Embedding (FastText)    | DBSCAN               | As above                                                   | Out of memory for all data                                                                                     | Lots of noise, clusters are highly related                                                                                                         |
| Word Embedding (FastText)    | OPTICS               | As above plus takes long time for clustering               | Fits. Tradeoff with time.                                                                                      | Lots of noise, clusters sizes are moderate (on tuning). Noise can be reduced by tuning as well.                                                    |
| Docement Embedding (Doc2Vec) | OPTICS               | As above                                                   | Fits. Tradeoff with time.                                                                                      | More noise than fasttext version. Clusters are smaller in size and less in number. Tuning possible.                                                |
