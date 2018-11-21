# Milestone 1
## Project description
A recent direction of research has been to infer properties of source codes by learning statistical models on repositories of such codes. Examples of successful application include predicting variable names and locations in which an incorrect variable was used. We are interested in inferring types, a property of wide interest to the programming languages community.

## Problem statement
We want to evaluate whether it is possible to infer the types of various variables in a program using machine learning. In order to answer this question, we want to use programs in a language which supports type inference, and use the inferred types as our gold standard to train a predictor. Important properties from programs like the inter-dependence of variables and the control-structures they are governed should inform such a type-prediction task.

Specifically, we want to understand the difference between programs modeled using graph-neural networks, as against those modeled using more traditional machine learning models on source code, such as recurrent neural networks.

## Dataset
Hellendoorn, Vincent J., et al. "Deep Learning Type Inference." (FSE 2018) is recent work by a group at Microsoft Research who inferred types using traditional neural-network based models. They have a publicly released dataset. This will help serve as our baseline to compare how graph-based neural networks perform on this task.

The dataset is available at: https://github.com/DeepTyper/DeepTyper

## Research questions
- RQ1; Predictive ability of graph-based models. Do graph-based neural networks help capture program properties in order to predict variable types.
- RQ2; Value-addition of graph-based models. What do graph-based models capture which traditional machine learning models fail to when modeling source codes.
- RQ3; Interpretability. Do graph-based networks allow for any rich interpretation on what features contributed to a prediction task.
- RQ4; Improvements. How can graph-based networks be modified and enhanced to improve their predictive power, make them easier to train, easier to use, or more clearly correct?

# Milestone 2
## Machine learning approach

We will model programs to predict type information in scripts written in TypeScript, a language similar to Javascript.

This is a supervised learning setup, where the ground truth types (labels) are obtained by running TypeScript’s internal type inference algorithm. The machine learning task is then to model each token/variable’s type information and evaluate it against what the compiler infers.

In addition to compiler-inferred types, these scripts also have human-annotated type information. This will serve as an additional gold standard for our prediction task.

Since the goal of our work is to experiment and Implement a graph-based neural network, as described in Allamanis, Miltiadis, Marc Brockschmidt, and Mahmoud Khademi. "Learning to represent programs with graphs." arXiv preprint arXiv:1711.00740 (2017), we will implement a gated graph neural network using TensorFlow

## Evaluation
- We will evaluate our approach against the baseline in Hellendoorn et al., which uses cross entropy loss between the predicted type vector and the ground truth type vector.
- We will also look at the type vectors with the lowest accuracy, analyzing both false positives and false negatives.
- During evaluation, we’ll test on both unseen inter- and intra- repository code.

# Milestone 3
## Implementation: Libraries vs. Code from scratch
### Libraries
Typescript related. Our dataset is a large collection of TypeScript code, and its corresponding type annotations. We plan on using the programmatic access TypeScript has to its compiler and typechecker API to parse and preprocess the input data and targets.

Graph-based NN related. We plan on using either the recently released DeepMind graph neural network library (https://github.com/deepmind/graph_nets), or the Google Brain version (https://github.com/tensorflow/tensor2tensor/blob/master/tensor2tensor/layers/common_message_passing_attention.py#L786). Both of these are implemented in Tensorflow.

### Code from scratch
- Pipeline: We will write out the entire pipeline which comprise the following steps
    - processes Typescript codes to produce its ASTs,
    - process these ASTs to produce edge information for the graph-based NN, push this edge info through the graph-based NN to learn/train a model.
    - predict types on unseen programs validate results, checking train/test error in a way that matches the setup of our baseline (i.e. only on variable declarations)


## Open Problems
- What edges will we include in the graph we construct? Just AST edges, or will we add in control flow edges, use/def edges, or more?
- What initial values will various nodes in the graph take on? For leaf nodes (i.e. AST tokens) this may just be a learnable embedding, but for nonterminals this is more of an open question.
- How can we avoid choosing a hardcoded threshold for the number of iterations to train the graph-based NN on. Prior literature suffers from this problem, where a pre-decided number is not justified.
- What improvements can we make to graph NNs? E.g. can we somehow restrict to functions that guarantee a fixpoint in the limit of infinite iterations? (is this property already satisfied? Who knows!)

## Initial division of work
- Katie: Initial architecture design+implementation on TensorFlow; graph-based NN experiments
- Shashank: AST-processing to produce edge-information; graph-based NN experiments
- Alex: frontend pipeline, including parsing TypeScript and outputting usable ASTs that conform to the data available in the baselines; graph-based NN experiments

# Milestone 4
We discuss our idea and demonstrate code-setup to the TA.

# Milestone 5
## Progress
We’re able to train a graph neural net on type data derived from the ASTs of programs!

## Our results so far
- On a relatively large example (`facebook.ts`, which connects to Facebook’s authentication API), we’re able to get a **training accuracy of 89%**.
- On two simple sample files (that we manually containing a relatively diverse distribution of rich types), we’re able to get up to about **76% training accuracy, and 43% test accuracy**, which seems to be an encouraging result.

## Baseline
The hand crafted benchmarks from our reference paper report an **accuracy of 37.5%,  while their best result is 57% accuracy**. We believe there are tweaks we can make to significantly improve our performance.

## Shortcoming
We are still having some issues with generalization, primarily due to the dataset distribution: the majority of types in a given file are either unique to that particular file (e.g. specialized Javascript objects are a common pattern), or are inferred as Any, the bottom type in Typescript.

## Next steps
- Debug why our implementation is slow, so we can scale our experiments up to larger datasets
- Continue to refine our neural network architecture, to hopefully get even better results
- Try out some data augmentation approaches (or just take out the most common types), so that our neural network predictions are less degenerate with regard to the most frequent types.
