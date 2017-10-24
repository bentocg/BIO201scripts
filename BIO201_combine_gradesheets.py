# -*- coding: utf-8 -*-
"""
Created on Sun Oct 15 20:24:12 2017

@author: bento
"""
# read midterm data
# import packages
import os
import numpy as np
import pandas as pd
from difflib import SequenceMatcher
from functools import reduce

# change working directory
os.chdir("C:/Users/bento/OneDrive/Documents/BIO201 scripts/format_midterm/FALL 17/midterm 1 section 2/")

def readTest(filename):
    """
    Helper function to read BIO201 exams .txt into python lists with questions
    Input: BIO201 exam converted from word to .txt
    Output: list with questions in exam
    """
    f = open(filename, 'r')

    def isDigit(string):
        """
        Helper function to check if element is an integer
        Input: A string
        Output: A boolean indicating whether that string can be converted to a integer
        """
        assert type(string) == str, "Input is not a string"
        try:
            int(string)
            return True
        except:
            return False

    # read lines
    lines = [line for line in f.readlines() if '.' in line]
    # get rid of lines before first question
    while not isDigit(lines[0][0]):
        lines.pop(0)
    # extract questions
    questions = []
    started = False
    for line in lines:
        if isDigit(line[0]):
            if started:
                questions.append(curr_quest)
            started = True
            curr_quest = line.strip()
        else:
            curr_quest += " " + line.strip()
    questions.append(curr_quest)
    return questions


def findEquiv(ref_keys, comp_keys):
    """
    Helper function to find equivalent questions from another exam
    Input: Two sets of similar keys scrambled in different orders (ref_keys and comp_keys)
    Output: A dictionary that maps questions from comp_dict to their equivalent in the ref_dict
    """
    assert (len(ref_keys) == len(comp_keys)), "Input lists have different sizes."
    def similarity(str1, str2):
        """
        Helper function to get similarity between two strings
        Input: Two strings
        Output: similarity score
        """
        return SequenceMatcher(None, str1, str2).ratio()

    def findFirstLetter(string):
        for i in range(len(string)):
            if ord(string[i]) >= 65 and ord(string[i]) < 123:
                return i
    # may alternate between one and the other in case it fails
    ref = [reduce(lambda x1, x2: x1 + " " + x2, sorted(ele[findFirstLetter(ele):].split(), key=lambda x: len(x))[-15:-1])
           for ele in ref_keys.copy()]
    comp = [reduce(lambda x1, x2: x1 + " " + x2, sorted(ele[findFirstLetter(ele):].split(), key=lambda x: len(x))[-15:-1])
            for ele in comp_keys.copy()]
    #ref = ref_keys.copy()
    #comp = comp_keys.copy()
    mapping = {}
    for idx1 in range(len(comp)):
        if comp[idx1] in ref:
            mapping[idx1] = ref.index(comp[idx1])

        else:
            max_val = 0
            idx_max = 0
            for idx2 in range(len(comp)):
                sim_score = similarity(comp[idx1], ref[idx2])
                if sim_score > max_val:
                    max_val = sim_score
                    idx_max = idx2
            mapping[idx1] = idx_max
    assert (len(pd.unique(mapping.values())) == len(ref_keys)), print(len(pd.unique(mapping.values())), "Failed to find a match!")
    return mapping


def createMasterSheet(raw_exam_file, test_files, answer_key, save_csv=True):
    """
    Create a master grading sheet 
    Input:  raw_exam_file - BIO 201 raw exam file containing answers from all exam versions
            test_files - list with paths to .txt test files of all versions
            answer_key - path to answer key
    Output: a .csv file where all questions are mapped to unique rows
    """
    # read all .txt test files and save questions
    tests = [readTest(filename) for filename in test_files]
    # find equivalence between questions
    conversion = [findEquiv(tests[0], tests[i]) for i in range(1, len(tests))]
    # read raw test data for all versions
    raw_data = pd.read_csv(raw_exam_file, header=None)
    # separate tests by version
    version_data = [raw_data.loc[raw_data[1] == version] for version in sorted(pd.unique(raw_data[1]))]
    # remove useless columns and rename columns to match questions
    for i in range(len(version_data)):
        version_data[i].drop([ele for ele in range(3)] +
                             [ele for ele in range(raw_data.shape[1] - 5, raw_data.shape[1])],
                             axis=1, inplace=True)
        version_data[i].columns = [ele for ele in range(version_data[i].shape[1])]
    # create a master sheet and combine data frames
    frames = [version_data[0]]
    for i in range(1, len(version_data)):
        curr_version = version_data[i].copy()
        curr_version.rename(columns=conversion[i - 1], inplace=True)
        curr_version.sort_index(axis=1, inplace=True)
        frames.append(curr_version)
    master_sheet = pd.concat(frames)
    master_sheet.sort_index()
    # add percent correct
    ans_key = pd.read_csv(answer_key, header=None)
    # allows for multiple correct answers
    correct_answers = [ele.split() for ele in ans_key[1]]
    percent_correct = []
    percent_a = []
    percent_b = []
    percent_c = []
    percent_d = []
    percent_e = []
    for i in range(master_sheet.shape[1]):
        percent_correct.append(np.sum([ele in correct_answers[i] for ele in master_sheet[i]]) / master_sheet.shape[0])
        percent_a.append(np.sum(master_sheet[i] == "A") / master_sheet.shape[0])
        percent_b.append(np.sum(master_sheet[i] == "B") / master_sheet.shape[0])
        percent_c.append(np.sum(master_sheet[i] == "C") / master_sheet.shape[0])
        percent_d.append(np.sum(master_sheet[i] == "D") / master_sheet.shape[0])
        percent_e.append(np.sum(master_sheet[i] == "E") /master_sheet.shape[0])
    master_sheet = master_sheet.append(pd.Series(percent_correct, [ele for ele in range(len(percent_correct))],
                                                 name="% correct"))
    master_sheet = master_sheet.append(pd.Series(percent_a, [ele for ele in range(len(percent_a))], name="% a"))
    master_sheet = master_sheet.append(pd.Series(percent_b, [ele for ele in range(len(percent_a))], name="% b"))
    master_sheet = master_sheet.append(pd.Series(percent_c, [ele for ele in range(len(percent_a))], name="% c"))
    master_sheet = master_sheet.append(pd.Series(percent_d, [ele for ele in range(len(percent_a))], name="% d"))
    master_sheet = master_sheet.append(pd.Series(percent_e, [ele for ele in range(len(percent_a))], name="% e"))

    master_sheet.columns = tests[0]
    master_sheet["Student_ID"] = raw_data[0]

    if save_csv:
        master_sheet.to_csv(raw_exam_file[:-7] + "MASTER_SHEET.csv")
    return master_sheet


all_exams = createMasterSheet(raw_exam_file="raw_answers.csv", test_files=["version 1.txt", "version 2.txt",
                                                                           "version 3.txt"],
                              answer_key="answer_key.csv")


