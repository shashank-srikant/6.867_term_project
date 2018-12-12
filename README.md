# 6.867 term project - Fall 2018

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

