#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 27 23:11:33 2018

@author: tom
@author: joe
"""
import pandas as pd
import matplotlib.pyplot as plt
import random
import numpy as np
from operator import itemgetter
from datetime import datetime,timedelta
import math
import csv
import os.path

#import numpy as np
#from sklearn.feature_selection import VarianceThreshold

#def getWeek(DataFrame):

#gets day and location-------------------------------------------------------------------------------#
def getLocation(DataFrame):
    #filters the Day and Place column only
    filtered = DataFrame[['Place','Time']].copy()
    
    #remove rows with Nan in any column
    df = filtered.dropna()
    return df

#gets time and activity------------------------------------------------------------------------------#
def getActivity(DataFrame):
    #filters the Day and Place column only
    filtered = DataFrame[['Day','Time', 'Activity']]
    
    #remove rows with Nam in any column
    df = filtered.dropna()
    
    final = df[(df.Activity != 'walk')]
    final = final[(final.Activity != 'lesson')]
    final = final[(final.Activity != 'home time')]
    final = final[(final.Activity != 'vehicle')]
    final = final[(final.Activity != 'groceries')]
    final = final[(final.Activity != 'sleep')]
    final = final[(final.Activity != 'drinks')]
    final = final[(final.Activity != 'religion')]
    final = final[(final.Activity != 'exhibition')]
    return df

#this returns a dataframe of location data for one day-------------------------------------------------#
#   grabs the last index in the file (indicating today's date)
#   use index to return all the locations from today as Dataframe
def getTodayLoc(DataFrame):
    
    day = int(datetime.strftime(datetime.now(), '%Y%m%d'))  #"""FIXME"""
    df = DataFrame[DataFrame.Day == day]
    df = getLocation(df)
    
    return df

#get all data from yesterday
#   uses datetime library to grab the all data from yesterday
#   returns all the location from yesterday as a dataframe  
def getYesterdayLoc(DataFrame):
    
    day = int(datetime.strftime(datetime.now(), '%Y%m%d'))# """FIXME"""
    #print(day)
    df = DataFrame[DataFrame.Day == day]
    df = getLocation(df)
    return df

# steps------------------------------------------------------------------------------------------------# 

# 1 creates a list of all the places visited in yesterday in placesVistedList
# 2 make an empty list that stores incorrect locations called inCorrect_loc
# iterate untill you have a list of 3
# 2 grab a random place from the data set, check it against the placesvisitedList
# if the random place does not exitst inside the place visted list 
#   append it to the inCorrect_loc list:
#else:
# continue 

def checkLocList(DataFrame):
    ''' We return geolocations that are not from today, these locations get cleaned and double cheked in the udivs question set '''
    
    df = getYesterdayLoc(DataFrame)
    df = df.drop_duplicates(subset = 'Place', keep = 'first')
    df = df['Place']
    return df


#this returns the time of place in the format HH:MM AM/PM----------------------------------------------#
def getHourTime(DataFrame):
    ''' This is a helper function that returns the time from a geolocation in Hours and Minutes and AM or PM'''
    date_time = DataFrame['Time'].iloc[0]
    time = datetime.strptime(date_time, '%a %b %d %H:%M:%S %Z %Y')
    hour_time = time.strftime('%I:%M %p')
    return hour_time

# This grabs location --------------------------------------------------------------------------------- #   
def getData(DataFrame, Amount):
    ''' This is a helper function to return a location for the udivs system'''
    lastday = DataFrame.iloc[:,1]
    lastindex = len(lastday.index)
    #count = o
    #lastIndex = Activities
    return lastday[lastindex]

# function returns an array of applications used in a day each with a total duration 
def getDuration(DataFrame):
    
    day = int(datetime.strftime(datetime.now(), '%Y%m%d')) #"""FIXME"""
    df = data[data.Day == day]
    df = df[['Time', 'Activity', 'Duration ms']].copy()
    df = df.dropna()
    df = df[df['Activity'].str.contains("phone:")]
    group = df.groupby('Activity').sum()
    
    return group

# function converts miliseconds to minutes
def convertms(ms):
    ''' This helper function converts the miliseconds into minutes for a qustion in the UDIVS system. It return the floor minute'''
    minutes = (ms/(1000*60))
    minutes = math.floor(minutes)

    return minutes

# -----------------------------------------------------------------------------------------------------#
def getRecentApp():
    ''' This helper function returns the most recent app used for the UDIVS system'''
    day = somDay_df['Activity'].dropna()
    for x in day[::-1]:
        #print(x)
        if "phone:" not in x:
            continue
        ans = x
        break
    return ans

#-------------------------------------------------------------------------------------------------------#
# get the first location that is not the current location, generate incorrect answeres 
def getRecentLocation():
    ''' Returns the most recent app used by the user for the UDIVS system'''
    x=1
    while(True):
       curLoc = somDay_df['Place'].iloc[-x]
       if curLoc == "nan":
           x = x+1
       else:
           break
    #print("curLock:",curLoc)
    
    locData = somDay_df['Place'].dropna()
    #print(locData)
    ans = ""
    for x in locData[::-1]:
        if x != curLoc:
            ans = x
            break
    return ans

#--------------------------------------------------------------------------------------------------------#
'''
This is the logic to produce the questions, the incorrect answers, and the actual answer for the 
UDIVS survey.
'''
#--------------------------------------------------------------------------------------------------------#
def getOptions(n):
    
    options = []
    
    #question options for "which app did you use most recently
    if n == 0:
        """'Which app did you use most recently?'"""
        ans = getRecentApp()
        options.append(ans)
        count = 1
        print('Which app did you use most recently?\n')
        #this loop gives an array of answers called options for the user to choose from
        day = somDay_df['Activity'].dropna()
        for x in day:
            flag = 0
            if "phone:" in x:
                for y in options:
                    if x == y:
                        flag = 1
                if flag == 0:
                    options.append(x)
                    count = count +1
                if count == 4:
                    break
        random.shuffle(options,random.random)
        return ans,options
    
    elif n == 1:

       """What place were you at most recently?"""
       ans = getRecentLocation()
       options.append(ans)
       count = 1

       locData = somDay_df['Place'].dropna()
       print('What place were you at most recently?\n')
       #this loop gives an array of answers called options for the user to choose from
       for x in locData:
           flag = 0
           for y in options:
               if x == y:
                   flag = 1
           if flag == 0:
               options.append(x)
               count = count +1
           if count == 4:
               break
       random.shuffle(options,random.random)
       return ans,options

    elif n == 2:
        """'which place were you at around:'"""
        
        time_loc = getTodayLoc(data)
        ans_data = time_loc.sample(n=1)
        ans = ans_data['Place'].iloc[0]
        options.append(ans)
        
        print('which place were you at around', getHourTime(ans_data), 'today\n')
        dummy_data = getLocation(data)
        count = 1
        
        while count < 4:
            random_day = dummy_data.sample(n=1)
            place = random_day['Place'].iloc[0]
            flag = 0
            for y in options:
                if y == place:
                    flag = 1
            if flag == 1:
                pass
            else:
                options.append(place)
                count = count + 1
        random.shuffle(options,random.random)
        return ans,options

    elif n == 3:
        """Which of these places did you go to yesterday?'"""
        time_loc = getYesterdayLoc(data)
        ans_data = time_loc.sample(n = 1)
        ans = ans_data['Place'].iloc[0]
        options.append(ans)
        placesVisited = checkLocList(data)
        
        print('Which of these places did you go to yesterday?\n')
        dummy_data = getLocation(data)
        count = 1
        while count < 4:
            random_day = dummy_data.sample(n=1)
            place = random_day['Place'].iloc[0]
            flag = 0
            for z in placesVisited:
                if z == place:
                    flag = 1
            for y in options:
                if y == place:
                    flag = 1
            if flag == 1:
                pass
            else:
                options.append(place)
                count = count + 1
        random.shuffle(options,random.random)
        return ans,options
    
    elif n == 4:
        """'About how long did you use __ for'"""
        options = ['0-10 minutes', '11-20 minutes', '21-30 minutes', '+30 minutes']
        
        groups = getDuration(data)
        activity = groups.sample(n=1)
        miliseconds = int(activity['Duration ms'])
        minutes = convertms(miliseconds)
        app = activity.index[0]
        
        print("About how long did you use", app.replace('phone: ', '', 1), "today?")
        
        if minutes <= 10:
            ans = options[0]
        elif minutes <= 20:
            ans = options[1]
        elif minutes <= 30:
            ans = options[2]
        else: 
            ans = options[3]
        
        return ans,options
    elif n ==5:
        '''which app did you use most frequently today'''
        
        print("Which app did you use most frequently today?")
        applicationList = []
        count = 1
        day = somDay_df['Activity'].dropna()
        for x in day:
            if "phone:" in x:
                applicationList.append(x)
        app_df = pd.DataFrame(data = applicationList)
        ans= app_df[0].value_counts().idxmax()
    
        options.append(ans)
        for x in day:
            flag = 0
            if "phone:" in x:
                for y in options:
                    if x == y:
                        flag = 1
                if flag == 0:
                    options.append(x)
                    count = count +1
                if count == 4:
                    break
        random.shuffle(options,random.random)
        return ans,options
        
                
        

data = pd.read_csv('../../userdevice_data/Joe_Data/Smarter_time/timeslots.csv')

#new version of filter to one day without hardcoding
last_index = len(data) - 1
day = data.loc[last_index, 'Day']
somDay_df = data[data.Day == day]
#-------------------------------------------------------------------------------------------------------------------------#
'''
This is where the actual survey begins, we ask the user three questions form or question set
This is a score fusion with a random question form features chosen from the data set

'''
#-------------------------------------------------------------------------------------------------------------------------#

print("Welcome to Joe's Device ! See if you can enter!")
questions=['Which app did you use most recently?','What place were you at most recently?','which place were you at around ','Which of these places did you go to yesterday?', 
           'How long were you on this app?','Which app did you use most frequently today?']
randomNums=random.sample(range(0,6),3)
print(randomNums)
# Ask the user if they are genuine or an imposter to collect the data properly
user = 2
genuine = True
while(user !=1 and user !=0):
    print("Are you a genuine(1)user or an imposter(0)?")
    user =int(input("0: imposter\n1: genuine\n"))
    print(user)
    if (user == 0):
        genuine = False
    else:
        genuine =True
        
score = 0
count = 1
for n in randomNums:
    ans,options = getOptions(n)
    #print(ans)                        # This is where we normaly print the answer for debugging
    for o in options:
        print(count,". ",o)
        count = count+1
    userAns=int(input("input answer here: ")) # Utilize Switch CasegetOptions(n)
    if genuine:
        user = 'genuine'
    else:
        user = 'imposter'
    Q_Num = n + 1
    file = open('../raw_scores/question' + str(Q_Num) + '_' + user + '.csv','a')
    writer = csv.writer(file)
    if ans == options[userAns-1]:
        score = score + 1
        Qdata = [1] 
        writer.writerow(Qdata)
    else:
        Qdata = [0]
        writer.writerow(Qdata)
    file.close()    
    count = 1

if genuine:
    user = 'genuine'
else:
    user = 'imposter'

# This will write the score to the appropriate file
scores = [score]
file = open('../raw_scores/survey_score_'+user+'.csv','a')
writer = csv.writer(file)
writer.writerow(scores)
file.close()

#------------------------------------------------------------------------------ This is where the data analysis goes-------------------------------------------#
''' This section of code is to to produce the False Reject Rate, The False Acceptance Rate, 
and True Reject Rate, True Accept Rate for the total system as well as analysis on each question'''

# Generate genuine and imposter scores with the seed at 1
genuine_scores = pd.read_csv('../raw_scores/survey_score_genuine.csv')
imposter_scores = pd.read_csv('../raw_scores/survey_score_imposter.csv')

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

