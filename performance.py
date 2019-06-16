#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 20 02:24:23 2018

@author: tom
@author: joe
"""
    
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math    

def dprime(mean_gen, mean_imp, std_gen, std_imp,**kwargs):
    
    x = math.sqrt(2) * abs(mean_gen - mean_imp)
    y = math.sqrt((std_gen**2) + (std_imp**2))
    return (x / y)

def plot_questions(Q_scores, title):
    
    plt.figure()
    zeros = []
    ones = []
    for x in Q_scores:
        if x == 0:
            zeros.append(0)
        else:
            ones.append(1)
    plt.hist(zeros, color='red', lw=2, histtype='step', hatch='//', label='Negatives', range = (0,1), bins = 2)
    plt.hist(ones, color='green', lw=2, histtype='step', hatch='\\', label='Positives', range = (0,1), bins = 2)
    plt.legend(loc='best')
    #dp = dprime(gen_scores, imp_scores)
    plt.title(title)
    plt.show()
    return
 

def plot_scoreDist(gen_scores, imp_scores, dp):
    
    plt.figure()
    plt.hist(gen_scores, color='green', lw=2, histtype='step', hatch='//', label='Genuine Scores', range = (0,5), bins = 4)
    plt.hist(imp_scores, color='red', lw=2, histtype='step', hatch='\\', label='Impostor Scores', range = (0,5), bins = 4)
    plt.legend(loc='best')
    #dp = dprime(gen_scores, imp_scores)
    plt.title('Score Distribution d-prime=' +  str(round(dp, 2)))
    plt.show()
    return

def Calculate_Efficency(Q_gen,Q_imp):
    gen_num_correct = 0
    gen_num_incorrect = 0
    imp_num_correct = 0
    imp_num_incorrect = 0
    total = 0
    for g in Q_gen:
        if g ==1:
            gen_num_correct = gen_num_correct + 1
        else:
            gen_num_incorrect = gen_num_incorrect + 1
        total = total + 1
    for i in Q_imp:
        if i == 1:
            imp_num_correct = imp_num_correct + 1
        else:
            imp_num_incorrect = imp_num_incorrect + 1
        total = total + 1
    return ((gen_num_correct+imp_num_incorrect)-(gen_num_incorrect+ imp_num_correct)/total)

genuine = pd.read_csv('../raw_scores/survey_score_genuine.csv')
imposter = pd.read_csv('../raw_scores/survey_score_imposter.csv')

Q1_gen = pd.read_csv('../raw_scores/question1_genuine.csv')
Q1_imp = pd.read_csv('../raw_scores/question1_imposter.csv')

Q2_gen = pd.read_csv('../raw_scores/question2_genuine.csv')
Q2_imp = pd.read_csv('../raw_scores/question2_imposter.csv')

Q3_gen = pd.read_csv('../raw_scores/question3_genuine.csv')
Q3_imp = pd.read_csv('../raw_scores/question3_imposter.csv')

Q4_gen = pd.read_csv('../raw_scores/question4_genuine.csv')
Q4_imp = pd.read_csv('../raw_scores/question4_imposter.csv')

Q5_gen = pd.read_csv('../raw_scores/question5_genuine.csv')
Q5_imp = pd.read_csv('../raw_scores/question5_imposter.csv')

Q6_gen = pd.read_csv('../raw_scores/question6_genuine.csv')
Q6_imp = pd.read_csv('../raw_scores/question6_imposter.csv')

e =[]
# Question 1 Graphs and Eff----------------------------------------------------#
q_g = Q1_gen.values
plot_questions(q_g[:,0], "Question 1 Genuine Scores")
q_i = Q1_imp.values
plot_questions(q_i[:,0], "Question 1 Imposter Scores")
e.append(Calculate_Efficency(q_g,q_i))

# Question 2 Graphs and Eff----------------------------------------------------#
q_g = Q2_gen.values
plot_questions(q_g[:,0], "Question 2 Genuine Scores")
q_i = Q2_imp.values
plot_questions(q_i[:,0], "Question 2 Imposter Scores")
e.append(Calculate_Efficency(q_g,q_i))

# Question 3 Graphs and Eff----------------------------------------------------#
q_g = Q3_gen.values
plot_questions(q_g[:,0], "Question 3 Genuine Scores")
q_i = Q3_imp.values
plot_questions(q_i[:,0], "Question 3 Imposter Scores")
e.append(Calculate_Efficency(q_g,q_i))

# Question 4 Graphs and Eff----------------------------------------------------#
q_g = Q4_gen.values
plot_questions(q_g[:,0], "Question 4 Genuine Scores")
q_i = Q4_imp.values
plot_questions(q_i[:,0], "Question 4 Imposter Scores")
e.append(Calculate_Efficency(q_g,q_i))

# Question 5 Graphs and Eff----------------------------------------------------#
q_g = Q5_gen.values
plot_questions(q_g[:,0], "Question 5 Genuine Scores")
q_i = Q5_imp.values
plot_questions(q_i[:,0], "Question 5 Imposter Scores")
e.append(Calculate_Efficency(q_g,q_i))

# Question 6 Graphs and Eff----------------------------------------------------#
q_g = Q6_gen.values
plot_questions(q_g[:,0], "Question 6 Genuine Scores")
q_i = Q6_imp.values
plot_questions(q_i[:,0], "Question 6 Imposter Scores")
e.append(Calculate_Efficency(q_g,q_i))

# polt all the effiecy rates
objects = ('Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6')
y_pos = np.arange(len(objects))
performance = e
 
plt.bar(y_pos, performance, align='center', alpha=0.5)
plt.xticks(y_pos, objects)
plt.xlabel('Question Number')
plt.ylabel('Accuracy Percent')
plt.title('Question Accuracy')
plt.show()



#scores = genuine[0]
genuine_scores = genuine.values
imposter_scores = imposter.values
genuine_scores = genuine_scores[:,0]
imposter_scores = imposter_scores[:,0]
print(genuine_scores)
print('NEXT IS IMPOSTER')
print(imposter_scores)

mu_g = genuine_scores.mean()
mu_i = imposter_scores.mean()

sigma_g = np.std(genuine_scores)
sigma_i = np.std(imposter_scores)

dp = dprime(mean_gen = mu_g,mean_imp=mu_i,std_gen=sigma_g,std_imp=sigma_i)

plot_scoreDist(genuine_scores, imposter_scores, dp)

# This is for the DET curve
far = []
tpr = []
frr = []
fpr = []
err = []
tp = 0
tn = 0
fp = 0
fn = 0
thresholds = np.linspace(0.0, 4.0, 100,dtype = 'int')
for t in thresholds:
    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for g_s in genuine_scores:
        if g_s >= t:
            tp += 1
        else: 
            fn += 1
    
    for i_s in imposter_scores:
        if i_s >= t:
            fp += 1
        else:
            tn += 1
            
    far.append(fp / (fp + tn))
    tpr.append(tp / (tp + fn))
    frr.append(fn / (fn + tp))

min_distance = abs(frr[1] - far[1])       

for (i,j) in zip(frr, far):
    distance = abs(i - j)
    
    if distance < min_distance:
        min_distance = distance
        x = i
        y = j

EER = (x + y)/2
        
plt.figure()
plt.plot(far,frr,lw = 3,color = 'blue')
plt.plot([0,1], [0,1], lw = 1, color = 'black', linestyle = '--')
plt.xlabel('False Accept Rate')
plt.ylabel('False Reject Rate')
plt.title('Detection Error Tradeoff with EER = ' + str(round(EER, 3)))
plt.show()


plt.figure()
plt.plot(far, tpr, color='darkorange', lw=1)
plt.plot([0, 1], [0, 1], color='navy', lw=1, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")
plt.show()
