import networkx as nx
import requests
import matplotlib.pyplot as plt
import collections
import copy
import statistics
import numpy as np
import operator
import collections
from itertools import islice
#from statsmodels.distributions.empirical_distribution import ECDF
from bs4 import BeautifulSoup

from atla_alias import alias_dict  # contains all characters of the show and their known alias
from atla_color import color_dict  # contains all characters of the show and theis respective colors
import atla_functions as atla_func # contains text reading functions

# CONTROL VARIABLES
skip_analysis = True        # whether to skip the transcript analysis based on the reader
skip_classic_analysis = True # whether to skip the transcript analysis based on the classical model
skip_metrics = False         # whether to skip the network's properties analysis



# modifies a list of metrics and plots an ECDF of the given values
def get_metric_dic(mlist, mdict, name, name2, xlabel, ylabel, number_label):
    key_min = min(mdict.keys(), key=(lambda k: mdict[k]))
    mlist.append(key_min)
    key_max = max(mdict.keys(), key=(lambda k: mdict[k]))
    mlist.append(key_max)
    values = [mdict[key] for key in mdict]
    mlist.append(statistics.mean(values))
    mlist.append(statistics.median(values))
    if(len(values) >= 2):
        mlist.append(statistics.stdev(values))
        #custom_ecdf(values)
        """ cdf = ECDF(values)
        plt.plot(cdf.x, cdf.y, label=name+" ECDF", marker=".", linestyle='none', markerfacecolor='none')
        plt.xlabel(xlabel, fontsize=18)
        plt.ylabel(ylabel, fontsize=16)
        plt.legend()
        plt.show() """
    else:
        print("WARNING: No ECDF for " + name)
        mlist.append(0)
    
    # sort the 20 highest values
    top_20 = collections.Counter(mdict).most_common(20)
    top_20_labeled = []
    for i in range(len(top_20)):
        for j in range(len(number_label)):
            if top_20[i][0] == j:
                top_20_labeled.append([number_label[j], top_20[i][1]])
    print("Category:", name)
    # print top 20 highest values with their respective characters
    print("Top 20:", top_20_labeled)
    # get the bottom value character
    bottom_tier = []
    for i in range(len(number_label)):
        if min(mdict, key=mdict.get) == i:
            bottom_tier.append([number_label[i], mdict[min(mdict, key=mdict.get)]])
    print("Bottom Tier:", bottom_tier)





page_link = 'http://atla.avatarspirit.net/transcripts.php?num='

season1_episode_numbers = [
    '101', '102', '103', '104', '105', '106', '107', '108', '109', '110',
    '111', '112', '113', '114', '115', '116', '117', '118', '119', '120'
]

# episode 215 DOES NOT contain the Act I, Act II, Act III division
season2_episode_numbers = [
    '201', '202', '203', '204', '205', '206', '207', '208', '209', '210',
    '211', '212', '213', '214', '216', '217', '218', '219', '220'
]

season3_episode_numbers = [
    '301', '302', '303', '304', '305', '306', '307', '308', '309', '310',
    '311', '312', '313', '314', '315', '316', '317', '318', '319', '320', '321'
]

seasons = season1_episode_numbers + season2_episode_numbers + season3_episode_numbers

current_characters_list = [] #initialize as empty. contains all characters that have ever appeared, and their aliases
current_scene = ""           #list of strings of characters to be analyzed
#raw_episode                  #webpage in html to be converted to a string list
current_episode = []         #list of scenes of an episode
current_interactions = []    #list of current interactions in a scene, a list of pairs. WARNING: [A,B] == [B,A]





# must contain size-3 lists of format [v1, v2, weight]
edges_list = [["Sokka", "Katara", 0]]

# # # # # # # # #
# Simple Reader #
# # # # # # # # #
if skip_analysis == False:
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # Make a request to a webpage, read its episode transcript and modify the list        #
    # of edges accordingly. This section will add new edges when necessary, in the format #
    # described above in edges_list, and modify current edges weights by 1 at a time if   #
    # those have been detected again.                                                     #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    for num in seasons:
        soup_string = ""
        try:
            page = requests.get(page_link+num)
            if page.status_code != 200:
                print("RequestError:", num, "status_code:", page.status_code)
                continue
            soup = BeautifulSoup(page.text, 'html.parser')
            soup_string = str(soup)
        except requests.exceptions.RequestException as e:
            print('RequestException:', e)

        scenes = atla_func.sceneSeparator(soup_string)
        #print(scenes)

        # start empty because it's the beginning of the episode
        previous_speaker = ""

        # get the first speaker
        next_speaker = ""
        first_scene_sentences = atla_func.sceneSentenceSeparator(scenes[0])
        if len(first_scene_sentences) > 0:
            # find speaker
            beginning_speaker = first_scene_sentences[0].find("<b>") + len("<b>")
            end_speaker = first_scene_sentences[0].find("</b>", beginning_speaker)
            speaker = first_scene_sentences[0][beginning_speaker:end_speaker]
            # find speaker's character
            speaker_character = atla_func.aliasOrName(speaker)
            if len(speaker_character) > 0:
                next_speaker = speaker_character[0]

        # # # # # # # # # # # #
        # M A I N    L O O P  #
        # # # # # # # # # # # #
        for scene in scenes:
            #print(scene)
            sentences = atla_func.sceneSentenceSeparator(scene)
            current_interactions = []
            #print("*********************************************************")
            #print("ALL SENTENCES:",sentences)
            for s in sentences:

                interaction = atla_func.detectSpeakerInteraction(s, previous_speaker, next_speaker)
                #print("Interaction: ",interaction)
                if len(interaction) > 0:
                    previous_speaker = interaction[0]
                next_speaker = ""
                # check if new interaction has already occurred in this scene; add if not
                if len(interaction) > 0:
                    if interaction not in current_interactions and interaction[::-1] not in current_interactions:
                        current_interactions.append(interaction)

            #print("current_interactions:",current_interactions)
            # check if edge already exists and increase its weight; insert edge if not
            for ci in current_interactions:
                #print("ci:",ci)
                for character in ci[1]:
                    candidate_edge = [ci[0], character]
                    r_candidate_edge = candidate_edge[::-1]
                    # check if interaction is in edges_list
                    new_edge = True
                    for i in range(len(edges_list)):
                        if edges_list[i][0:2] == candidate_edge:
                            edges_list[i][2] += 1
                            new_edge = False
                            break
                        elif edges_list[i][0:2] == r_candidate_edge:
                            edges_list[i][2] += 1
                            new_edge = False
                            break

                    if new_edge == True:
                        edges_list.append([ci[0], character, 1])


    print("###########################################################################")
    print("###########################################################################")

    # clean up self-edges 
    edges_list = [e for e in edges_list if e[0] != e[1]]

    print(edges_list)
    print(len(edges_list))

    print("###########################################################################")
    print("###########################################################################")

# # # # # # # # # #
# Classic Method  #
# # # # # # # # # #
if skip_classic_analysis == False:
    for num in seasons:
        soup_string = ""
        try:
            page = requests.get(page_link+num)
            if page.status_code != 200:
                print("RequestError:", num, "status_code:", page.status_code)
                continue
            soup = BeautifulSoup(page.text, 'html.parser')
            soup_string = str(soup)
        except requests.exceptions.RequestException as e:
            print('RequestException:', e)

        
        soup_string = soup_string.replace("<b>"," ")
        soup_string = soup_string.replace("</b>"," ")
        soup_string = soup_string.replace("<br/>"," ")
        soup_string = soup_string.replace("<br>"," ")
        soup_string = soup_string.replace("<u>"," ")
        soup_string = soup_string.replace("</u>"," ")
        soup_string = soup_string.replace("<i>"," ")
        soup_string = soup_string.replace("</i>"," ")
        
        # # # # # # # # # # # #
        # M A I N    L O O P  #
        # # # # # # # # # # # #
        characters = []

        # get all possible proper nouns
        proper_nouns = atla_func.detectProperNouns(soup_string)

        # add to characters list accordingly
        for p in range(len(proper_nouns)):
            # check if there are alias or names
            if len(atla_func.aliasOrName(proper_nouns[p])) > 0:
                c_name = atla_func.aliasOrName(proper_nouns[p])[0]
                # add if new character
                if c_name not in characters:
                    characters.append(c_name)

        # all unique pairs of characters
        pairs = []
        for p1 in range(len(characters)):
                for p2 in range(p1+1,len(characters)):
                        pairs.append([characters[p1], characters[p2]])

        #print(pairs)

        # for every possible pair of character, check if already exists in edges_list; modify accordingly
        for c in range(len(pairs)):
            candidate_edge = [pairs[c][0], pairs[c][1]]
            r_candidate_edge = candidate_edge[::-1]
            # check if already in edges_list
            new_edge = True
            for j in range(len(edges_list)):
                if edges_list[j][0:2] == candidate_edge:
                    edges_list[j][2] += 1
                    new_edge = False
                    break
                elif edges_list[j][0:2] == r_candidate_edge:
                    edges_list[j][2] += 1
                    new_edge = False
                    break

            if new_edge == True:
                edges_list.append([pairs[c][0], pairs[c][1], 1])


    print("###########################################################################")
    print("###########################################################################")

    # clean up self-edges 
    edges_list = [e for e in edges_list if e[0] != e[1]]

    print(edges_list)
    print(len(edges_list))

    print("###########################################################################")
    print("###########################################################################")
 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# PRE-CALCULATED edges_lists OF EACH SEASON SEPARATELY BELOW  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # ,

edges_list_1 = [['Sokka', 'Katara', 50], ['Zuko', 'Iroh', 51], ['Zuko', 'Aang', 14], ['Aang', 'Appa', 20], ['Katara', 'Aang', 116], ['Kanna', 'Katara', 7], ['Aang', 'Sokka', 40], ['Sokka', 'Kanna', 1], ['Kanna', 'Aang', 1], ['Katara', 'Appa', 7], ['Iroh', 'Ozai', 1], ['Gyatso', 'Aang', 7], ['Aang', 'Bumi', 7], ['Aang', 'Momo', 4], ['Bumi', 'Flopsy', 2], ['Aang', 'Flopsy', 5], ['Katara', 'Bumi', 1], ['Bumi', 'Ozai', 3], ['Katara', 'Haru', 8], ['Sokka', 'Haru', 2], ['Sokka', 'Momo', 3], ['Haru', 'Tyro', 1], ['Tyro', 'Katara', 2], ['Haru', 'Aang', 2], ['Aang', 'Hei-Bai', 2], ['Sokka', 'Hei-Bai', 1], ['Aang', 'Roku', 17], ['Iroh', 'Aang', 4], ['Shyu', 'Aang', 5], ['Shyu', 'Roku', 6], ['Aang', 'How', 2], ['Shyu', 'Ozai', 1], ['Zhao', 'Zuko', 9], ['Zhao', 'Aang', 13], ['Zhao', 'Ozai', 4], ['Katara', 'Momo', 9], ['Aang', 'The Duke', 1], ['Zhang Leader', 'Jin', 3], ['Gan Jin Leader', 'Katara', 1], ['Gan Jin Leader', 'Jin Wei', 2], ['Gan Jin Leader', 'Wei Jin', 2], ['Gan Jin Leader', 'Jin', 2], ['Zhang Leader', 'Wei Jin', 1], ['Zhang Leader', 'Jin Wei', 1], ['Sokka', 'Jin', 2], ['Aang', 'Jin Wei', 1], ['Aang', 'Wei Jin', 1], ['Aang', 'Jin', 1], ['Gan Jin Leader', 'Aang', 1], ['Sokka', 'Wei Jin', 1], ['Jee', 'Aang', 1], ['Jee', 'Iroh', 2], ['Ozai', 'Zuko', 2], ['Shinu', 'Zhao', 4], ['Sokka', 'Appa', 3], ['Herbalist', 'Miyuki', 3], ['Iroh', 'Zhao', 7], ['Zuko', 'How', 1], ['Meng', 'Aang', 3], ['Aang', 'Wu', 4], ['Katara', 
'Wu', 4], ['Sokka', 'Wu', 2], ['Katara', 'Meng', 1], ['Hakoda', 'Sokka', 1], ['Bato', 'Sokka', 9], ['Katara', 'Bato', 6], ['Bato', 'Aang', 6], ['June', 'Iroh', 2], ['Aang', 'Ozai', 1], ['Jeong Jeong', 'Roku', 2], ['Zhao', 'Jeong Jeong', 2], ['Katara', 'Jeong Jeong', 1], ['Jeong Jeong', 'Aang', 3], ['Teo', 'Aang', 3], ['The Mechanist', 'Teo', 1], ['The Mechanist', 'Aang', 1], ['Zhao', 'Li', 1], ['Arnook', 'Aang', 3], ['Arnook', 'Pakku', 2], ['Aang', 'Pakku', 5], ['Katara', 'Pakku', 3], ['Sokka', 'Yue', 9], ['Yugoda', 'Kanna', 1], ['Pakku', 'Kanna', 1], ['Pakku', 
'Sangok', 2], ['Arnook', 'Hahn', 3], ['Sokka', 'Zhao', 3], ['Arnook', 'Sokka', 3], ['Yue', 'Aang', 2], ['Arnook', 'Yue', 2], ['Sokka', 'Zuko', 1], ['Roku', 'Koh', 2], ['Koh', 'Aang', 1]]
# len(edges_list_1) is 93

edges_list_2 = [['Sokka', 'Katara', 7], ['Sokka', 'Aang', 22], ['Aang', 'Momo', 3], ['Aang', 'Appa', 7], ['Katara', 'Aang', 17], ['Katara', 'Appa', 4], ['Katara', 'Momo', 2], ['Due', 'Tho', 3], ['Sokka', 'Yue', 2], ['Hue', 'Aang', 3], ['Sokka', 'Momo', 2], ['Due', 'Hue', 1], ['Sokka', 'Hue', 1], ['Sokka', 'Appa', 3], ['Sokka', 'Roku', 2], ['Tong', 'Kyoshi', 1], ['Katara', 'Koko', 1], ['Katara', 'Oyagi', 1], ['Sokka', 'Kyoshi', 1], ['Oyagi', 'Kyoshi', 2], ['Oyagi', 'Suki', 1], ['Oyagi', 'Aang', 1], ['Zuko', 'Aang', 4], ['Iroh', 'Aang', 1], ['Katara', 'Tong', 2], ['Zuko', 'Iroh', 14], ['Gansu', 'Sela', 1], ['Gansu', 'Zuko', 1], ['Ursa', 'Zuko', 5], ['Ty Lee', 'Azula', 3], ['Ursa', 'Azula', 1], ['Azula', 'Ozai', 1], ['Gansu', 'Gow', 1], ['Ursa', 'Azulon', 2], ['Azula', 'Azulon', 2], ['Azulon', 'Ozai', 1], ['Azulon', 'Iroh', 1], ['Zuko', 'Azula', 10], ['Sela', 'Zuko', 1], ['Zuko', 'Ozai', 2], ['Katara', 'Toph', 7], ['Katara', 'Zuko', 3], ['Toph', 'Zuko', 1], ['Sokka', 'Toph', 3], ['Aang', 'Toph', 2], ['Iroh', 'Lu Ten', 1], ['Iroh', 'Azula', 4], ['Azula', 'Qin', 2], ['Azula', 'Mai', 1], ['Smellerbee', 'Appa', 1], ['Smellerbee', 'Jet', 1], ['Sokka', 'Guru', 1], ['Hakoda', 'Sokka', 2], ['Kuei', 'Bosco', 3], ['Kuei', 'Long Feng', 1], ['Katara', 'How', 2], ['Aang', 'Guru', 7], ['Guru', 'Gyatso', 2], ['Aang', 'How', 1], ['Yu', 'Toph', 1], ['Azula', 'Kuei', 1], ['Azula', 'Li', 4], ['Hakoda', 'Bato', 1], ['Mai', 'Kuei', 1], ['Ty Lee', 'Aang', 1], ['Katara', 'Suki', 1], ['Katara', 'Iroh', 1], ['Long Feng', 'Aang', 1], ['Iroh', 'Kuei', 1], ['Azula', 'Long Feng', 1], ['Azula', 'Aang', 4], ['Toph', 'Guru', 1], ['Sokka', 'Suki', 2], ['Sokka', 'How', 2], ['Sokka', 'Kuei', 1], ['Long Feng', 'Li', 1]]
# len(edges_list_2) is 76

edges_list_3 = [['Sokka', 'Katara', 6], ['Aang', 'Momo', 8], ['Sokka', 'Aang', 17], ['Aang', 'Toph', 6], ['Aang', 'Piandao', 2], ['Katara', 'Pakku', 3], ['Piandao', 'Sokka', 7], ['Katara', 'Appa', 3], ['Toph', 'Sokka', 12], ['Aang', 'Ozai', 9], ['Hakoda', 'Sokka', 5], ['Tho', 'Due', 1], ['Haru', 'Katara', 2], ['Aang', 'Haru', 1], ['Tyro', 'Katara', 1], ['Teo', 'Aang', 1], ['Poon', 'Ming', 1], ['Iroh', 'Ming', 4], ['Hakoda', 'Ozai', 1], ['Hakoda', 'Katara', 3], ['Katara', 'Aang', 16], ['Zuko', 'Mai', 3], ['Tho', 'Hue', 1], ['Due', 'Hue', 1], ['Bato', 'Sokka', 2], ['Sokka', 'Ozai', 7], ['Ozai', 'Zuko', 5], ['Zuko', 'Aang', 18], ['Ozai', 'Azulon', 2], ['Bato', 'Hakoda', 1], ['Zuko', 'Iroh', 13], ['The Duke', 'Pipsqueak', 4], ['Haru', 'The Duke', 1], ['Katara', 'Jeong Jeong', 1], ['Aang', 'Zhao', 1], ['Katara', 'Toph', 6], ['Zuko', 'Sokka', 15], ['Zuko', 'Appa', 1], ['Sokka', 'Suki', 10], ['Aang', 'Jet', 1], ['Hakoda', 'Kya', 1], ['Zuko', 'Katara', 6], ['Actress Katara', 'Jet', 1], ['Actor Sokka', 'Yue', 1], ['Actor Zuko', 'Azula', 1], ['Actress Katara', 'Zuko', 2], ['Actress Katara', 'Aang', 1], ['Actor Sokka', 'Toph', 1], ['Actor Zuko', 'Aang', 1], ['Actor Zuko', 'Ozai', 1], ['Aang', 'Bosco', 1], ['Ozai', 'Shinu', 1], ['Ozai', 'Azula', 4], ['Ozai', 'Sozin', 2], ['Sokka', 'Appa', 1], ['Toph', 'Zuko', 1], ['Sokka', 'Momo', 1], ['Katara', 'Momo', 1], ['Zuko', 'June', 1], ['Roku', 'Aang', 2], ['Aang', 'Kyoshi', 3], ['Aang', 'Chin', 1], ['Kuruk', 'Aang', 1], ['Piandao', 'Zuko', 1], ['Aang', 'Yangchen', 4], ['Toph', 'Ozai', 2], ['Iroh', 'Ozai', 1], ['Zuko', 'Azula', 2], ['Katara', 'Iroh', 2], ['Katara', 'Azula', 2], ['Li', 'Azula', 2], ['Azula', 'Lo', 1], ['Ursa', 'Ty Lee', 1], ['Ursa', 'Zuko', 1], ['Ursa', 'Azula', 1], ['Aang', 'Lion Turtle', 1]]
# len(edges_list_3) is 76

true_edges_list = [['Sokka', 'Katara', 63], ['Zuko', 'Iroh', 78], ['Zuko', 'Aang', 36], ['Aang', 'Appa', 27], ['Katara', 'Aang', 149], ['Kanna', 'Katara', 7], ['Aang', 'Sokka', 79], ['Sokka', 'Kanna', 1], ['Kanna', 'Aang', 1], ['Katara', 'Appa', 14], ['Iroh', 'Ozai', 2], ['Gyatso', 'Aang', 7], ['Aang', 'Bumi', 7], ['Aang', 'Momo', 15], ['Bumi', 'Flopsy', 2], ['Aang', 'Flopsy', 5], ['Katara', 'Bumi', 1], ['Bumi', 'Ozai', 3], ['Katara', 'Haru', 10], ['Sokka', 'Haru', 2], ['Sokka', 'Momo', 6], ['Haru', 'Tyro', 1], ['Tyro', 'Katara', 3], ['Haru', 'Aang', 3], ['Aang', 'Hei-Bai', 2], ['Sokka', 'Hei-Bai', 1], ['Aang', 'Roku', 19], ['Iroh', 'Aang', 5], ['Shyu', 'Aang', 5], ['Shyu', 'Roku', 6], ['Aang', 'How', 3], ['Shyu', 'Ozai', 1], ['Zhao', 'Zuko', 9], ['Zhao', 'Aang', 14], ['Zhao', 'Ozai', 4], ['Katara', 'Momo', 12], ['Aang', 'The Duke', 1], ['Zhang Leader', 'Jin', 3], ['Gan Jin Leader', 'Katara', 1], ['Gan Jin Leader', 'Jin Wei', 2], ['Gan Jin Leader', 'Wei Jin', 2], ['Gan Jin Leader', 'Jin', 2], ['Zhang Leader', 'Wei Jin', 1], ['Zhang Leader', 'Jin Wei', 1], ['Sokka', 'Jin', 2], ['Aang', 'Jin Wei', 1], ['Aang', 'Wei Jin', 1], ['Aang', 'Jin', 1], ['Gan Jin Leader', 'Aang', 1], ['Sokka', 'Wei Jin', 1], ['Jee', 'Aang', 1], ['Jee', 'Iroh', 2], ['Ozai', 'Zuko', 9], ['Shinu', 'Zhao', 4], ['Sokka', 'Appa', 7], ['Herbalist', 'Miyuki', 3], ['Iroh', 'Zhao', 7], ['Zuko', 'How', 1], ['Meng', 'Aang', 3], ['Aang', 'Wu', 4], ['Katara', 'Wu', 4], ['Sokka', 'Wu', 2], ['Katara', 'Meng', 1], ['Hakoda', 'Sokka', 8], ['Bato', 'Sokka', 11], ['Katara', 'Bato', 6], ['Bato', 'Aang', 6], ['June', 'Iroh', 2], ['Aang', 'Ozai', 10], ['Jeong Jeong', 'Roku', 2], ['Zhao', 'Jeong Jeong', 2], ['Katara', 'Jeong Jeong', 2], ['Jeong Jeong', 'Aang', 3], ['Teo', 'Aang', 4], ['The Mechanist', 'Teo', 1], ['The Mechanist', 'Aang', 1], ['Zhao', 'Li', 1], ['Arnook', 'Aang', 3], ['Arnook', 'Pakku', 2], ['Aang', 'Pakku', 5], ['Katara', 'Pakku', 6], ['Sokka', 'Yue', 11], ['Yugoda', 'Kanna', 1], ['Pakku', 'Kanna', 1], ['Pakku', 'Sangok', 2], ['Arnook', 'Hahn', 3], ['Sokka', 'Zhao', 3], ['Arnook', 'Sokka', 3], ['Yue', 'Aang', 2], ['Arnook', 'Yue', 2], ['Sokka', 'Zuko', 16], ['Roku', 'Koh', 2], ['Koh', 'Aang', 1], ['Due', 'Tho', 4], ['Hue', 'Aang', 3], ['Due', 'Hue', 2], ['Sokka', 'Hue', 1], ['Sokka', 
'Roku', 2], ['Tong', 'Kyoshi', 1], ['Katara', 'Koko', 1], ['Katara', 'Oyagi', 1], ['Sokka', 'Kyoshi', 1], ['Oyagi', 'Kyoshi', 2], ['Oyagi', 'Suki', 1], ['Oyagi', 'Aang', 1], ['Katara', 'Tong', 2], ['Gansu', 'Sela', 1], ['Gansu', 'Zuko', 1], ['Ursa', 'Zuko', 6], ['Ty Lee', 'Azula', 3], ['Ursa', 'Azula', 2], ['Azula', 'Ozai', 5], ['Gansu', 'Gow', 1], ['Ursa', 'Azulon', 2], ['Azula', 'Azulon', 2], ['Azulon', 'Ozai', 3], ['Azulon', 'Iroh', 1], ['Zuko', 'Azula', 12], ['Sela', 'Zuko', 1], ['Katara', 'Toph', 13], ['Katara', 'Zuko', 9], ['Toph', 'Zuko', 2], ['Sokka', 'Toph', 15], ['Aang', 'Toph', 8], ['Iroh', 'Lu Ten', 1], ['Iroh', 'Azula', 4], ['Azula', 'Qin', 2], ['Azula', 'Mai', 1], ['Smellerbee', 'Appa', 1], ['Smellerbee', 'Jet', 1], ['Sokka', 'Guru', 1], ['Kuei', 'Bosco', 3], ['Kuei', 'Long Feng', 1], ['Katara', 'How', 2], ['Aang', 'Guru', 7], ['Guru', 'Gyatso', 2], ['Yu', 'Toph', 1], ['Azula', 'Kuei', 1], ['Azula', 'Li', 6], ['Hakoda', 'Bato', 2], ['Mai', 'Kuei', 1], ['Ty Lee', 'Aang', 1], ['Katara', 'Suki', 1], ['Katara', 'Iroh', 3], ['Long Feng', 'Aang', 1], ['Iroh', 'Kuei', 1], ['Azula', 'Long Feng', 1], ['Azula', 'Aang', 4], ['Toph', 'Guru', 1], ['Sokka', 'Suki', 12], ['Sokka', 'How', 2], ['Sokka', 'Kuei', 1], ['Long Feng', 'Li', 1], ['Aang', 'Piandao', 2], ['Piandao', 'Sokka', 7], ['Poon', 'Ming', 1], ['Iroh', 'Ming', 4], ['Hakoda', 'Ozai', 1], ['Hakoda', 'Katara', 3], ['Zuko', 'Mai', 3], ['Tho', 'Hue', 1], ['Sokka', 'Ozai', 7], ['The Duke', 'Pipsqueak', 4], ['Haru', 'The Duke', 1], ['Zuko', 'Appa', 1], ['Aang', 'Jet', 1], ['Hakoda', 'Kya', 1], ['Actress Katara', 'Jet', 1], ['Actor Sokka', 'Yue', 1], ['Actor Zuko', 'Azula', 1], ['Actress Katara', 'Zuko', 2], ['Actress Katara', 'Aang', 1], ['Actor Sokka', 'Toph', 1], ['Actor Zuko', 'Aang', 1], ['Actor Zuko', 'Ozai', 1], ['Aang', 'Bosco', 1], ['Ozai', 'Shinu', 1], ['Ozai', 'Sozin', 2], ['Zuko', 'June', 1], ['Aang', 'Kyoshi', 3], ['Aang', 'Chin', 1], ['Kuruk', 'Aang', 1], ['Piandao', 'Zuko', 1], ['Aang', 'Yangchen', 4], ['Toph', 'Ozai', 2], ['Katara', 'Azula', 2], ['Azula', 'Lo', 1], ['Ursa', 'Ty Lee', 1], ['Aang', 'Lion Turtle', 1]]
# len(true_edges_list) is 189





# before 'how' fix
true_edges_list = [['Sokka', 'Katara', 63], ['Zuko', 'Iroh', 78], ['Zuko', 'Aang', 36], ['Aang', 'Appa', 27], ['Katara', 'Aang', 149], ['Kanna', 'Katara', 7], ['Aang', 'Sokka', 79], ['Sokka', 'Kanna', 1], ['Kanna', 'Aang', 1], ['Katara', 'Appa', 14], ['Iroh', 'Ozai', 2], ['Gyatso', 'Aang', 7], ['Aang', 'Bumi', 7], ['Aang', 'Momo', 15], ['Bumi', 'Flopsy', 2], ['Aang', 'Flopsy', 5], ['Katara', 'Bumi', 1], ['Bumi', 'Ozai', 3], ['Katara', 'Haru', 10], ['Sokka', 'Haru', 2], ['Sokka', 'Momo', 6], ['Haru', 'Tyro', 1], ['Tyro', 'Katara', 3], ['Haru', 'Aang', 3], ['Aang', 'Hei-Bai', 2], ['Sokka', 'Hei-Bai', 1], ['Aang', 'Roku', 19], ['Iroh', 'Aang', 5], ['Shyu', 'Aang', 5], ['Shyu', 'Roku', 6], ['Aang', 'How', 3], ['Shyu', 'Ozai', 1], ['Zhao', 'Zuko', 9], ['Zhao', 'Aang', 14], ['Zhao', 'Ozai', 4], ['Katara', 'Momo', 12], ['Aang', 'The Duke', 1], ['Zhang Leader', 'Jin', 3], ['Gan Jin Leader', 'Katara', 1], ['Gan Jin Leader', 'Jin Wei', 2], ['Gan Jin Leader', 'Wei Jin', 2], ['Gan Jin Leader', 'Jin', 2], ['Zhang Leader', 'Wei Jin', 1], ['Zhang Leader', 'Jin Wei', 1], ['Sokka', 'Jin', 2], ['Aang', 'Jin Wei', 1], ['Aang', 'Wei Jin', 1], ['Aang', 'Jin', 1], ['Gan Jin Leader', 'Aang', 1], ['Sokka', 'Wei Jin', 1], ['Jee', 'Aang', 1], ['Jee', 'Iroh', 2], ['Ozai', 'Zuko', 9], ['Shinu', 'Zhao', 4], ['Sokka', 'Appa', 7], ['Iroh', 'Zhao', 7], ['Zuko', 'How', 1], ['Meng', 'Aang', 3], ['Aang', 'Wu', 4], ['Katara', 'Wu', 4], ['Sokka', 'Wu', 2], ['Katara', 'Meng', 1], ['Hakoda', 'Sokka', 8], ['Bato', 'Sokka', 11], ['Katara', 'Bato', 6], ['Bato', 'Aang', 6], ['June', 'Iroh', 2], ['Aang', 'Ozai', 10], ['Jeong Jeong', 'Roku', 2], ['Zhao', 'Jeong Jeong', 2], ['Katara', 'Jeong Jeong', 2], ['Jeong Jeong', 'Aang', 3], ['Teo', 'Aang', 4], ['The Mechanist', 'Teo', 1], ['The Mechanist', 'Aang', 1], ['Zhao', 'Li', 1], ['Arnook', 'Aang', 3], ['Arnook', 'Pakku', 2], ['Aang', 'Pakku', 5], ['Katara', 'Pakku', 6], ['Sokka', 'Yue', 11], ['Yugoda', 'Kanna', 1], ['Pakku', 'Kanna', 1], ['Pakku', 'Sangok', 2], ['Arnook', 'Hahn', 3], ['Sokka', 'Zhao', 3], ['Arnook', 'Sokka', 3], ['Yue', 'Aang', 2], ['Arnook', 'Yue', 2], ['Sokka', 'Zuko', 16], ['Roku', 'Koh', 2], ['Koh', 'Aang', 1], ['Due', 'Tho', 4], ['Hue', 'Aang', 3], ['Due', 'Hue', 2], ['Sokka', 'Hue', 1], ['Sokka', 
'Roku', 2], ['Tong', 'Kyoshi', 1], ['Katara', 'Koko', 1], ['Katara', 'Oyagi', 1], ['Sokka', 'Kyoshi', 1], ['Oyagi', 'Kyoshi', 2], ['Oyagi', 'Suki', 1], ['Oyagi', 'Aang', 1], ['Katara', 'Tong', 2], ['Gansu', 'Sela', 1], ['Gansu', 'Zuko', 1], ['Ursa', 'Zuko', 6], ['Ty Lee', 'Azula', 3], ['Ursa', 'Azula', 2], ['Azula', 'Ozai', 5], ['Gansu', 'Gow', 1], ['Ursa', 'Azulon', 2], ['Azula', 'Azulon', 2], ['Azulon', 'Ozai', 3], ['Azulon', 'Iroh', 1], ['Zuko', 'Azula', 12], ['Sela', 'Zuko', 1], ['Katara', 'Toph', 13], ['Katara', 'Zuko', 9], ['Toph', 'Zuko', 2], ['Sokka', 'Toph', 15], ['Aang', 'Toph', 8], ['Iroh', 'Lu Ten', 1], ['Iroh', 'Azula', 4], ['Azula', 'Qin', 2], ['Azula', 'Mai', 1], ['Smellerbee', 'Appa', 1], ['Smellerbee', 'Jet', 1], ['Sokka', 'Guru', 1], ['Kuei', 'Bosco', 3], ['Kuei', 'Long Feng', 1], ['Katara', 'How', 2], ['Aang', 'Guru', 7], ['Guru', 'Gyatso', 2], ['Yu', 'Toph', 1], ['Azula', 'Kuei', 1], ['Azula', 'Li', 6], ['Hakoda', 'Bato', 2], ['Mai', 'Kuei', 1], ['Ty Lee', 'Aang', 1], ['Katara', 'Suki', 1], ['Katara', 'Iroh', 3], ['Long Feng', 'Aang', 1], ['Iroh', 'Kuei', 1], ['Azula', 'Long Feng', 1], ['Azula', 'Aang', 4], ['Toph', 'Guru', 1], ['Sokka', 'Suki', 12], ['Sokka', 'How', 2], ['Sokka', 'Kuei', 1], ['Long Feng', 'Li', 1], ['Aang', 'Piandao', 2], ['Piandao', 'Sokka', 7], ['Poon', 'Ming', 1], ['Iroh', 'Ming', 4], ['Hakoda', 'Ozai', 1], ['Hakoda', 'Katara', 3], ['Zuko', 'Mai', 3], ['Tho', 'Hue', 1], ['Sokka', 'Ozai', 7], ['The Duke', 'Pipsqueak', 4], ['Haru', 'The Duke', 1], ['Zuko', 'Appa', 1], ['Aang', 'Jet', 1], ['Hakoda', 'Kya', 1], ['Actress Katara', 'Jet', 1], ['Actor Sokka', 'Yue', 1], ['Actor Zuko', 'Azula', 1], ['Actress Katara', 'Zuko', 2], ['Actress Katara', 'Aang', 1], ['Actor Sokka', 'Toph', 1], ['Actor Zuko', 'Aang', 1], ['Actor Zuko', 'Ozai', 1], ['Aang', 'Bosco', 1], ['Ozai', 'Shinu', 1], ['Ozai', 'Sozin', 2], ['Zuko', 'June', 1], ['Aang', 'Kyoshi', 3], ['Aang', 'Chin', 1], ['Kuruk', 'Aang', 1], ['Piandao', 'Zuko', 1], ['Aang', 'Yangchen', 4], ['Toph', 'Ozai', 2], ['Katara', 'Azula', 2], ['Azula', 'Lo', 1], ['Ursa', 'Ty Lee', 1], ['Aang', 'Lion Turtle', 1]]


# after 'how' fix
true_edges_list = [['Sokka', 'Katara', 63], ['Zuko', 'Iroh', 78], ['Zuko', 'Aang', 36], ['Aang', 'Appa', 27], ['Katara', 'Aang', 149], ['Kanna', 'Katara', 7], ['Aang', 'Sokka', 79], ['Sokka', 'Kanna', 1], ['Kanna', 'Aang', 1], ['Katara', 'Appa', 14], ['Iroh', 'Ozai', 2], ['Gyatso', 'Aang', 7], ['Aang', 'Bumi', 7], ['Aang', 'Momo', 15], ['Bumi', 'Flopsy', 2], ['Aang', 'Flopsy', 5], ['Katara', 'Bumi', 1], ['Bumi', 'Ozai', 3], ['Katara', 'Haru', 10], ['Sokka', 'Haru', 2], ['Sokka', 'Momo', 6], ['Haru', 'Tyro', 1], ['Tyro', 'Katara', 3], ['Haru', 'Aang', 3], ['Aang', 'Hei-Bai', 2], ['Sokka', 'Hei-Bai', 1], ['Aang', 'Roku', 19], ['Iroh', 'Aang', 5], ['Shyu', 'Aang', 5], ['Shyu', 'Roku', 6], ['Shyu', 'Ozai', 1], ['Zhao', 'Zuko', 9], ['Zhao', 'Aang', 14], ['Zhao', 'Ozai', 4], ['Katara', 'Momo', 12], ['Aang', 'The Duke', 1], ['Zhang Leader', 'Jin', 3], ['Gan Jin Leader', 'Katara', 1], ['Gan Jin Leader', 'Jin Wei', 2], ['Gan Jin Leader', 'Wei Jin', 2], ['Gan Jin Leader', 'Jin', 2], ['Zhang Leader', 'Wei Jin', 1], ['Zhang Leader', 'Jin Wei', 1], ['Sokka', 'Jin', 2], ['Aang', 'Jin Wei', 1], ['Aang', 'Wei Jin', 1], ['Aang', 'Jin', 1], ['Gan Jin Leader', 'Aang', 1], ['Sokka', 'Wei Jin', 1], ['Jee', 'Aang', 1], ['Jee', 'Iroh', 2], ['Ozai', 'Zuko', 9], ['Shinu', 'Zhao', 4], ['Sokka', 'Appa', 7], ['Iroh', 'Zhao', 7], ['Meng', 'Aang', 3], ['Aang', 'Wu', 4], ['Katara', 'Wu', 4], ['Sokka', 'Wu', 2], ['Katara', 'Meng', 1], ['Hakoda', 'Sokka', 8], ['Bato', 'Sokka', 11], ['Katara', 'Bato', 6], ['Bato', 'Aang', 6], ['June', 'Iroh', 2], ['Aang', 'Ozai', 10], ['Jeong Jeong', 'Roku', 2], ['Zhao', 'Jeong Jeong', 2], ['Katara', 'Jeong Jeong', 2], ['Jeong Jeong', 'Aang', 3], ['Teo', 'Aang', 4], ['The Mechanist', 'Teo', 1], ['The Mechanist', 'Aang', 1], ['Zhao', 'Li', 1], ['Arnook', 'Aang', 3], ['Arnook', 'Pakku', 2], ['Aang', 'Pakku', 5], ['Katara', 'Pakku', 6], ['Sokka', 'Yue', 11], ['Yugoda', 'Kanna', 1], ['Pakku', 'Kanna', 1], ['Pakku', 'Sangok', 2], ['Arnook', 'Hahn', 
3], ['Sokka', 'Zhao', 3], ['Arnook', 'Sokka', 3], ['Yue', 'Aang', 2], ['Arnook', 'Yue', 2], ['Sokka', 'Zuko', 16], ['Roku', 'Koh', 2], ['Koh', 'Aang', 1], ['Due', 'Tho', 4], ['Hue', 'Aang', 3], ['Due', 'Hue', 2], ['Sokka', 'Hue', 1], ['Sokka', 'Roku', 2], ['Tong', 'Kyoshi', 1], ['Katara', 'Koko', 1], ['Katara', 'Oyagi', 1], ['Sokka', 'Kyoshi', 1], ['Oyagi', 'Kyoshi', 2], ['Oyagi', 'Suki', 1], ['Oyagi', 'Aang', 1], ['Katara', 'Tong', 2], ['Gansu', 'Sela', 1], ['Gansu', 'Zuko', 1], ['Ursa', 'Zuko', 6], ['Ty Lee', 'Azula', 3], ['Ursa', 'Azula', 2], ['Azula', 'Ozai', 5], ['Gansu', 'Gow', 1], ['Ursa', 'Azulon', 2], ['Azula', 'Azulon', 2], ['Azulon', 'Ozai', 3], ['Azulon', 'Iroh', 1], ['Zuko', 'Azula', 12], ['Sela', 'Zuko', 1], ['Katara', 'Toph', 13], ['Katara', 'Zuko', 9], ['Toph', 'Zuko', 2], ['Sokka', 'Toph', 15], ['Aang', 'Toph', 8], ['Iroh', 'Lu Ten', 1], ['Iroh', 'Azula', 4], ['Azula', 'Qin', 2], ['Azula', 'Mai', 1], ['Smellerbee', 'Appa', 1], ['Smellerbee', 'Jet', 1], ['Sokka', 'Guru', 1], ['Kuei', 'Bosco', 3], ['Kuei', 'Long Feng', 1], ['Katara', 'General How', 1], ['Aang', 'Guru', 7], ['Guru', 'Gyatso', 2], ['Yu', 'Toph', 1], ['Azula', 'Kuei', 1], ['Azula', 'Li', 6], ['Hakoda', 'Bato', 2], ['Mai', 'Kuei', 1], ['Ty Lee', 'Aang', 1], ['Katara', 'Suki', 1], ['Katara', 'Iroh', 3], ['Long Feng', 'Aang', 1], ['Iroh', 'Kuei', 1], ['Azula', 'Long Feng', 1], ['Azula', 'Aang', 4], ['Toph', 'Guru', 1], ['Sokka', 'Suki', 12], ['Sokka', 'General How', 1], ['Sokka', 'Kuei', 1], ['Long Feng', 'Li', 1], ['Aang', 'Piandao', 2], ['Piandao', 'Sokka', 7], ['Poon', 'Ming', 1], ['Iroh', 'Ming', 4], ['Hakoda', 'Ozai', 1], ['Hakoda', 'Katara', 3], ['Zuko', 'Mai', 3], ['Tho', 'Hue', 1], ['Sokka', 
'Ozai', 7], ['The Duke', 'Pipsqueak', 4], ['Haru', 'The Duke', 1], ['Zuko', 'Appa', 1], ['Aang', 'Jet', 1], ['Hakoda', 'Kya', 1], ['Actress Katara', 'Jet', 1], ['Actor Sokka', 'Yue', 1], ['Actor Zuko', 'Azula', 1], ['Actress Katara', 'Zuko', 2], ['Actress Katara', 'Aang', 1], ['Actor Sokka', 'Toph', 1], ['Actor Zuko', 'Aang', 1], ['Actor Zuko', 'Ozai', 1], ['Aang', 'Bosco', 1], ['Ozai', 'Shinu', 1], ['Ozai', 'Sozin', 2], ['Zuko', 'June', 1], ['Aang', 'Kyoshi', 3], ['Aang', 'Chin', 1], ['Kuruk', 'Aang', 1], ['Piandao', 'Zuko', 1], ['Aang', 'Yangchen', 4], ['Toph', 'Ozai', 2], ['Katara', 'Azula', 2], ['Azula', 'Lo', 1], ['Ursa', 'Ty Lee', 1], ['Aang', 'Lion Turtle', 1], ['Herbalist', 'Miyuki', 3]]
# len(true_edges_list) is 187 - 1
# reinserted : ['Herbalist', 'Miyuki', 3]





# before 'how' fix
classic_edges_list = [['Sokka', 'Katara', 58], ['Aang', 'Katara', 58], ['Aang', 'Sokka', 58], ['Aang', 'Zuko', 47], ['Aang', 'Iroh', 43], ['Aang', 'Appa', 57], ['Aang', 'Kanna', 5], ['Katara', 'Zuko', 46], ['Katara', 'Iroh', 42], ['Katara', 'Appa', 56], ['Katara', 'Kanna', 5], ['Sokka', 'Zuko', 46], ['Sokka', 'Iroh', 42], ['Sokka', 'Appa', 56], ['Sokka', 'Kanna', 5], ['Zuko', 'Iroh', 43], ['Zuko', 'Appa', 45], ['Zuko', 'Kanna', 4], ['Iroh', 'Appa', 41], ['Iroh', 'Kanna', 4], ['Appa', 'Kanna', 5], ['Aang', 'How', 52], ['Kanna', 'How', 3], ['Katara', 'How', 52], ['Sokka', 'How', 52], 
['Appa', 'How', 50], ['Zuko', 'How', 41], ['Iroh', 'How', 37], ['Appa', 'Zhao', 10], ['Appa', 'Ozai', 27], ['Appa', 'Gyatso', 5], ['Appa', 'Roku', 14], ['Aang', 'Zhao', 10], ['Aang', 'Ozai', 27], ['Aang', 'Gyatso', 5], ['Aang', 'Roku', 14], ['Katara', 'Zhao', 10], ['Katara', 'Ozai', 
27], ['Katara', 'Gyatso', 5], ['Katara', 'Roku', 14], ['Sokka', 'Zhao', 10], ['Sokka', 'Ozai', 27], ['Sokka', 'Gyatso', 5], ['Sokka', 'Roku', 14], ['Zuko', 'Zhao', 9], ['Zuko', 'Ozai', 22], ['Zuko', 'Gyatso', 5], ['Zuko', 'Roku', 12], ['Iroh', 'Zhao', 9], ['Iroh', 'Ozai', 20], ['Iroh', 'Gyatso', 5], ['Iroh', 'Roku', 11], ['Zhao', 'Ozai', 9], ['Zhao', 'How', 9], ['Zhao', 'Gyatso', 2], ['Zhao', 'Roku', 4], ['Ozai', 'How', 24], ['Ozai', 'Gyatso', 4], ['Ozai', 'Roku', 11], ['How', 'Gyatso', 4], ['How', 'Roku', 11], ['Gyatso', 'Roku', 3], ['Kyoshi', 'Zuko', 9], ['Kyoshi', 'Iroh', 9], ['Kyoshi', 'How', 8], ['Kyoshi', 'Aang', 9], ['Kyoshi', 'Sokka', 8], ['Kyoshi', 'Appa', 9], ['Kyoshi', 'Katara', 8], ['Kyoshi', 'Momo', 8], ['Kyoshi', 'Oyagi', 2], ['Kyoshi', 'Suki', 6], ['Kyoshi', 'Koko', 2], ['Zuko', 'Momo', 40], ['Zuko', 'Oyagi', 2], ['Zuko', 'Suki', 12], ['Zuko', 'Koko', 2], ['Iroh', 'Momo', 36], ['Iroh', 'Oyagi', 2], ['Iroh', 'Suki', 11], ['Iroh', 'Koko', 2], ['How', 'Momo', 49], ['How', 'Oyagi', 2], ['How', 'Suki', 10], ['How', 'Koko', 2], ['Aang', 'Momo', 52], ['Aang', 'Oyagi', 2], ['Aang', 'Suki', 12], ['Aang', 'Koko', 
2], ['Sokka', 'Momo', 52], ['Sokka', 'Oyagi', 2], ['Sokka', 'Suki', 11], ['Sokka', 'Koko', 2], ['Appa', 'Momo', 51], ['Appa', 'Oyagi', 2], ['Appa', 'Suki', 11], ['Appa', 'Koko', 2], ['Katara', 'Momo', 52], ['Katara', 'Oyagi', 2], ['Katara', 'Suki', 11], ['Katara', 'Koko', 2], ['Momo', 'Oyagi', 2], ['Momo', 'Suki', 10], ['Momo', 'Koko', 2], ['Oyagi', 'Suki', 2], ['Oyagi', 'Koko', 2], ['Suki', 'Koko', 2], ['Sokka', 'Cabbage Merchant', 2], ['Sokka', 'Bumi', 10], ['Sokka', 'Flopsy', 3], ['Appa', 'Cabbage Merchant', 2], ['Appa', 'Bumi', 10], ['Appa', 'Flopsy', 3], ['Aang', 'Cabbage Merchant', 2], ['Aang', 'Bumi', 10], ['Aang', 'Flopsy', 3], ['Katara', 'Cabbage Merchant', 2], ['Katara', 'Bumi', 10], ['Katara', 'Flopsy', 3], ['How', 'Cabbage Merchant', 2], ['How', 'Bumi', 9], ['How', 'Flopsy', 3], ['Cabbage Merchant', 'Bumi', 2], ['Cabbage Merchant', 'Momo', 2], ['Cabbage Merchant', 'Flopsy', 1], ['Bumi', 'Momo', 10], ['Bumi', 'Flopsy', 3], ['Momo', 'Flopsy', 3], ['Aang', 'Haru', 8], ['Aang', 'Tyro', 3], ['Aang', 'Hope', 5], ['Katara', 'Haru', 8], ['Katara', 'Tyro', 3], ['Katara', 'Hope', 5], ['Sokka', 'Haru', 8], ['Sokka', 'Tyro', 3], ['Sokka', 'Hope', 5], ['Appa', 'Haru', 8], ['Appa', 'Tyro', 3], ['Appa', 'Hope', 5], ['Momo', 'Haru', 7], ['Momo', 'Ozai', 25], ['Momo', 'Tyro', 3], ['Momo', 'Hope', 5], ['Haru', 'How', 7], ['Haru', 'Ozai', 5], ['Haru', 'Tyro', 3], ['Haru', 'Hope', 1], ['How', 'Tyro', 3], 
['How', 'Hope', 5], ['Ozai', 'Tyro', 3], ['Ozai', 'Hope', 2], ['Tyro', 'Hope', 1], ['Appa', 'Hei-Bai', 2], ['Aang', 'Hei-Bai', 2], ['Katara', 'Hei-Bai', 2], ['Sokka', 'Hei-Bai', 2], ['How', 'Hei-Bai', 2], ['Gyatso', 'Momo', 3], ['Gyatso', 'Hei-Bai', 1], ['Roku', 'Momo', 11], ['Roku', 'Hei-Bai', 2], ['Zuko', 'Hei-Bai', 2], ['Iroh', 'Hei-Bai', 2], ['Momo', 'Hei-Bai', 2], ['Roku', 'Shyu', 1], ['Aang', 'Shyu', 1], ['Appa', 'Shyu', 1], ['Katara', 'Shyu', 1], ['Sokka', 'Shyu', 1], ['Momo', 'Zhao', 9], ['Momo', 'Shyu', 1], ['Zuko', 'Shyu', 1], ['Iroh', 'Shyu', 1], ['Ozai', 'Shyu', 1], ['Zhao', 'Shyu', 1], ['Shyu', 'How', 1], ['Roku', 'Bumi', 3], ['Roku', 'Cabbage Merchant', 1], ['Zuko', 'Bumi', 8], ['Zuko', 'Cabbage Merchant', 1], ['Iroh', 'Bumi', 8], ['Iroh', 'Cabbage Merchant', 1], ['Bumi', 'Ozai', 6], ['Cabbage Merchant', 'Ozai', 1], ['Jet', 'Momo', 7], ['Jet', 'Aang', 7], ['Jet', 'Katara', 7], ['Jet', 'Sokka', 7], ['Jet', 'Zuko', 7], ['Jet', 'Appa', 6], ['Jet', 'How', 7], ['Jet', 'The Duke', 3], ['Jet', 'Pipsqueak', 2], ['Jet', 'Smellerbee', 5], ['Jet', 'Longshot', 5], ['Momo', 'The Duke', 9], ['Momo', 'Pipsqueak', 6], ['Momo', 'Smellerbee', 5], ['Momo', 'Longshot', 5], ['Aang', 'The Duke', 10], ['Aang', 'Pipsqueak', 6], ['Aang', 'Smellerbee', 5], ['Aang', 'Longshot', 5], ['Katara', 'The Duke', 10], ['Katara', 'Pipsqueak', 6], ['Katara', 'Smellerbee', 5], ['Katara', 'Longshot', 5], ['Sokka', 'The Duke', 10], ['Sokka', 'Pipsqueak', 6], ['Sokka', 'Smellerbee', 5], ['Sokka', 'Longshot', 5], ['Zuko', 'The Duke', 10], ['Zuko', 'Pipsqueak', 6], ['Zuko', 'Smellerbee', 5], ['Zuko', 'Longshot', 5], ['Appa', 'The Duke', 10], ['Appa', 'Pipsqueak', 6], ['Appa', 'Smellerbee', 4], ['Appa', 'Longshot', 4], ['How', 'The Duke', 9], ['How', 'Pipsqueak', 6], ['How', 'Smellerbee', 5], ['How', 'Longshot', 5], ['The Duke', 'Pipsqueak', 6], ['The Duke', 'Smellerbee', 2], ['The Duke', 'Longshot', 2], ['Pipsqueak', 'Smellerbee', 2], ['Pipsqueak', 'Longshot', 2], ['Smellerbee', 'Longshot', 5], ['Sokka', 'Zhang Leader', 1], ['Sokka', 'Canyon Guide', 1], ['Sokka', 'Jin', 2], ['Sokka', 'Gan Jin Leader', 1], ['Sokka', 'Jin Wei', 1], ['Sokka', 'Wei Jin', 1], ['Katara', 'Zhang Leader', 1], ['Katara', 'Canyon Guide', 1], ['Katara', 'Jin', 2], ['Katara', 'Gan Jin Leader', 1], ['Katara', 'Jin Wei', 1], ['Katara', 'Wei Jin', 1], ['Aang', 'Zhang Leader', 1], ['Aang', 'Canyon Guide', 1], ['Aang', 'Jin', 2], ['Aang', 'Gan Jin Leader', 1], ['Aang', 'Jin Wei', 1], ['Aang', 'Wei Jin', 1], ['Appa', 'Zhang Leader', 1], ['Appa', 'Canyon Guide', 1], ['Appa', 
'Jin', 2], ['Appa', 'Gan Jin Leader', 1], ['Appa', 'Jin Wei', 1], ['Appa', 'Wei Jin', 1], ['Momo', 'Zhang Leader', 1], ['Momo', 'Canyon Guide', 1], ['Momo', 'Jin', 2], ['Momo', 'Gan Jin Leader', 1], ['Momo', 'Jin Wei', 1], ['Momo', 'Wei Jin', 1], ['How', 'Zhang Leader', 1], ['How', 'Canyon Guide', 1], ['How', 'Jin', 2], ['How', 'Gan Jin Leader', 1], ['How', 'Jin Wei', 1], ['How', 'Wei Jin', 1], ['Zhang Leader', 'Canyon Guide', 1], ['Zhang Leader', 'Jin', 1], ['Zhang Leader', 'Gan Jin Leader', 1], ['Zhang Leader', 'Hope', 1], ['Zhang Leader', 'Jin Wei', 1], ['Zhang Leader', 'Wei Jin', 1], ['Canyon Guide', 'Jin', 1], ['Canyon Guide', 'Gan Jin Leader', 1], ['Canyon Guide', 'Hope', 1], ['Canyon Guide', 'Jin Wei', 1], ['Canyon Guide', 'Wei Jin', 1], ['Jin', 'Gan Jin Leader', 1], ['Jin', 'Hope', 2], ['Jin', 'Jin Wei', 1], ['Jin', 'Wei Jin', 1], ['Gan Jin Leader', 'Hope', 1], ['Gan Jin Leader', 'Jin Wei', 1], ['Gan Jin Leader', 'Wei Jin', 1], ['Hope', 'Jin Wei', 1], ['Hope', 'Wei Jin', 1], ['Jin Wei', 'Wei Jin', 1], ['Aang', 'Jee', 2], ['Sokka', 'Jee', 2], ['Katara', 'Jee', 2], ['Gyatso', 'Jee', 1], ['Appa', 'Jee', 2], ['Momo', 'Jee', 2], ['Iroh', 'Jee', 2], ['Zuko', 'Jee', 2], ['How', 'Jee', 2], ['Jee', 'Ozai', 2], ['Jee', 'Zhao', 2], ['Zuko', 'Shinu', 2], ['Zuko', 'Herbalist', 2], ['Zuko', 'Miyuki', 1], ['Shinu', 'Zhao', 1], ['Shinu', 'Aang', 2], ['Shinu', 'Sokka', 2], ['Shinu', 'Katara', 2], ['Shinu', 'Momo', 2], ['Shinu', 'Appa', 2], ['Shinu', 'Jee', 1], ['Shinu', 'Iroh', 2], ['Shinu', 'Ozai', 2], ['Shinu', 'Herbalist', 1], ['Shinu', 'Miyuki', 1], ['Shinu', 'How', 2], ['Zhao', 'Herbalist', 1], ['Zhao', 'Miyuki', 1], ['Aang', 'Herbalist', 2], ['Aang', 'Miyuki', 1], ['Sokka', 'Herbalist', 2], ['Sokka', 'Miyuki', 1], ['Katara', 'Herbalist', 2], ['Katara', 'Miyuki', 1], ['Momo', 'Herbalist', 2], ['Momo', 'Miyuki', 1], ['Appa', 'Herbalist', 2], ['Appa', 'Miyuki', 1], ['Jee', 'Herbalist', 1], ['Jee', 'Miyuki', 1], ['Iroh', 'Herbalist', 2], ['Iroh', 'Miyuki', 1], 
['Ozai', 'Herbalist', 1], ['Ozai', 'Miyuki', 1], ['Herbalist', 'Miyuki', 1], ['Herbalist', 'How', 2], ['Miyuki', 'How', 1], ['Katara', 'Wu', 2], ['Katara', 'Meng', 1], ['Momo', 'Wu', 2], ['Momo', 'Meng', 1], ['Sokka', 'Wu', 2], ['Sokka', 'Meng', 1], ['Aang', 'Wu', 2], ['Aang', 'Meng', 1], ['Appa', 'Wu', 2], ['Appa', 'Meng', 1], ['Wu', 'Meng', 1], ['Wu', 'How', 2], ['Meng', 'How', 1], ['Bato', 'Aang', 6], ['Bato', 'Sokka', 6], ['Bato', 'Katara', 6], ['Bato', 'Zuko', 6], ['Bato', 'Iroh', 5], ['Bato', 'June', 1], ['Bato', 'Appa', 6], ['Bato', 'Hakoda', 6], ['Bato', 'Momo', 6], ['Bato', 'Herbalist', 1], ['Bato', 'How', 6], ['Bato', 'Wu', 1], ['Aang', 'June', 3], ['Aang', 'Hakoda', 10], ['Sokka', 'June', 3], ['Sokka', 'Hakoda', 9], ['Katara', 'June', 3], ['Katara', 'Hakoda', 9], ['Zuko', 'June', 3], ['Zuko', 'Hakoda', 10], ['Zuko', 'Wu', 1], ['Iroh', 'June', 3], ['Iroh', 'Hakoda', 8], ['Iroh', 'Wu', 1], ['June', 'Appa', 3], ['June', 'Hakoda', 1], ['June', 'Momo', 3], ['June', 'Herbalist', 1], ['June', 'How', 3], ['June', 'Wu', 1], ['Appa', 'Hakoda', 9], ['Hakoda', 'Momo', 8], ['Hakoda', 'Herbalist', 1], ['Hakoda', 'How', 9], ['Hakoda', 'Wu', 1], ['Herbalist', 'Wu', 1], ['Jeong Jeong', 'Momo', 4], ['Jeong Jeong', 'Appa', 4], ['Jeong Jeong', 'Katara', 4], ['Jeong Jeong', 'Sokka', 4], ['Jeong Jeong', 'Aang', 4], ['Jeong Jeong', 'Ozai', 4], ['Jeong Jeong', 'How', 3], ['Jeong Jeong', 'Chey', 1], ['Jeong Jeong', 'Zhao', 2], ['Jeong Jeong', 'Roku', 2], ['Momo', 'Chey', 1], ['Appa', 'Chey', 1], ['Katara', 'Chey', 1], ['Sokka', 'Chey', 1], ['Aang', 'Chey', 1], ['Ozai', 'Chey', 1], ['How', 'Chey', 1], ['Chey', 'Zhao', 1], ['Chey', 'Roku', 1], ['Katara', 'Teo', 7], ['Katara', 'The Mechanist', 4], ['Sokka', 'Teo', 7], ['Sokka', 'The Mechanist', 4], ['Aang', 'Teo', 7], ['Aang', 'The Mechanist', 4], ['Momo', 'Teo', 7], ['Momo', 'The Mechanist', 4], ['Appa', 'Teo', 7], ['Appa', 'The Mechanist', 4], ['Teo', 'The Mechanist', 4], ['Teo', 'How', 7], ['The Mechanist', 'How', 4], ['Appa', 'Li', 10], ['Appa', 'Arnook', 3], ['Appa', 'Yue', 7], ['Appa', 'Pakku', 6], ['Appa', 'Yugoda', 1], ['Sokka', 'Li', 10], ['Sokka', 'Arnook', 3], ['Sokka', 'Yue', 7], ['Sokka', 'Pakku', 6], ['Sokka', 'Yugoda', 1], ['Aang', 'Li', 11], ['Aang', 'Arnook', 3], ['Aang', 'Yue', 7], ['Aang', 'Pakku', 6], ['Aang', 'Yugoda', 1], ['Katara', 'Li', 10], ['Katara', 'Arnook', 3], ['Katara', 'Yue', 7], ['Katara', 'Pakku', 6], ['Katara', 'Yugoda', 1], ['Zhao', 'Li', 1], ['Zhao', 'Arnook', 3], ['Zhao', 'Yue', 4], ['Zhao', 'Pakku', 3], ['Zhao', 'Yugoda', 1], ['Li', 'Iroh', 9], ['Li', 'Arnook', 1], ['Li', 'Yue', 2], ['Li', 'Pakku', 2], ['Li', 'Zuko', 11], ['Li', 'Yugoda', 1], ['Li', 'Momo', 10], ['Li', 'Ozai', 5], ['Iroh', 'Arnook', 3], ['Iroh', 'Yue', 6], ['Iroh', 'Pakku', 6], ['Iroh', 'Yugoda', 1], ['Arnook', 'Yue', 3], ['Arnook', 'Pakku', 3], ['Arnook', 'Zuko', 3], ['Arnook', 'Yugoda', 1], ['Arnook', 'Momo', 3], ['Arnook', 'Ozai', 2], ['Yue', 'Pakku', 3], ['Yue', 'Zuko', 7], ['Yue', 'Yugoda', 1], ['Yue', 'Momo', 7], ['Yue', 'Ozai', 4], ['Pakku', 'Zuko', 6], ['Pakku', 'Yugoda', 1], ['Pakku', 'Momo', 6], ['Pakku', 'Ozai', 5], ['Zuko', 'Yugoda', 1], ['Yugoda', 'Momo', 1], ['Yugoda', 'Ozai', 1], ['Katara', 'Sangok', 1], ['Katara', 'Hahn', 2], ['Pakku', 'Sangok', 1], ['Pakku', 'Hahn', 2], ['Pakku', 'How', 3], ['Sangok', 'Aang', 1], ['Sangok', 'Momo', 1], ['Sangok', 'Yue', 1], ['Sangok', 'Sokka', 1], ['Sangok', 'Iroh', 1], ['Sangok', 'Appa', 1], ['Sangok', 'Zhao', 1], ['Sangok', 'Zuko', 1], ['Sangok', 'Arnook', 1], ['Sangok', 'Hahn', 1], ['Sangok', 'How', 1], ['Aang', 'Hahn', 2], ['Momo', 'Hahn', 2], ['Yue', 'Hahn', 2], ['Yue', 'How', 6], ['Sokka', 'Hahn', 2], ['Iroh', 'Hahn', 2], ['Appa', 'Hahn', 2], ['Zhao', 'Hahn', 2], ['Zuko', 'Hahn', 2], ['Arnook', 'Hahn', 2], ['Arnook', 'How', 2], ['Hahn', 'How', 2], ['Appa', 'Shu', 1], ['Appa', 'Koh', 1], ['Katara', 'Shu', 1], ['Katara', 'Koh', 1], ['Momo', 'Shu', 1], ['Momo', 'Koh', 1], ['Sokka', 'Shu', 1], ['Sokka', 'Koh', 1], ['Yue', 'Roku', 2], ['Yue', 'Shu', 1], ['Yue', 'Koh', 1], ['Yue', 'Hei-Bai', 1], ['Zuko', 'Shu', 1], ['Zuko', 'Koh', 1], ['Aang', 'Shu', 1], ['Aang', 'Koh', 1], ['Roku', 'Hahn', 1], ['Roku', 'Shu', 1], ['Roku', 'Koh', 1], ['Roku', 'Pakku', 3], ['Roku', 'Arnook', 1], ['Iroh', 'Shu', 1], ['Iroh', 'Koh', 1], ['Zhao', 'Shu', 1], ['Zhao', 'Koh', 1], ['Zhao', 'Hei-Bai', 1], ['Hahn', 'Shu', 1], ['Hahn', 'Koh', 1], ['Hahn', 'Hei-Bai', 1], ['Hahn', 'Ozai', 1], ['Shu', 'Koh', 1], ['Shu', 'How', 1], ['Shu', 'Hei-Bai', 1], ['Shu', 'Pakku', 1], ['Shu', 'Arnook', 1], ['Shu', 'Ozai', 1], ['Koh', 'How', 1], ['Koh', 'Hei-Bai', 1], ['Koh', 'Pakku', 1], ['Koh', 'Arnook', 1], ['Koh', 'Ozai', 1], ['Hei-Bai', 'Pakku', 1], ['Hei-Bai', 'Arnook', 1], ['Hei-Bai', 'Ozai', 1], ['Aang', 'Fong', 4], ['Aang', 'Azula', 23], ['Sokka', 'Fong', 4], ['Sokka', 'Azula', 22], 
['Katara', 'Fong', 4], ['Katara', 'Azula', 22], ['Pakku', 'Fong', 1], ['Pakku', 'Kanna', 2], ['Pakku', 'Azula', 3], ['Appa', 'Fong', 3], ['Appa', 'Azula', 22], ['Fong', 'Kanna', 1], ['Fong', 'Iroh', 3], ['Fong', 'Zuko', 3], ['Fong', 'Ozai', 2], ['Fong', 'Azula', 1], ['Fong', 'Momo', 
4], ['Fong', 'Roku', 1], ['Kanna', 'Ozai', 2], ['Kanna', 'Azula', 2], ['Kanna', 'Momo', 3], ['Kanna', 'Roku', 2], ['Iroh', 'Azula', 20], ['Zuko', 'Azula', 24], ['Ozai', 'Azula', 14], ['Azula', 'Momo', 20], ['Azula', 'Roku', 5], ['Aang', 'Chong', 1], ['Aang', 'Moku', 1], ['Aang', 'Song', 1], ['Aang', 'Oma', 1], ['Katara', 'Chong', 1], ['Katara', 'Moku', 1], ['Katara', 'Song', 1], ['Katara', 'Oma', 1], ['Sokka', 'Chong', 1], ['Sokka', 'Moku', 1], ['Sokka', 'Song', 1], ['Sokka', 'Oma', 1], ['Momo', 'Chong', 1], ['Momo', 'Moku', 1], ['Momo', 'Song', 1], ['Momo', 'Oma', 1], ['Chong', 'Iroh', 1], ['Chong', 'Appa', 1], ['Chong', 'Bumi', 1], ['Chong', 'Zuko', 1], ['Chong', 'How', 1], ['Chong', 'Moku', 1], ['Chong', 'Song', 1], ['Chong', 'Oma', 1], ['Iroh', 'Moku', 1], ['Iroh', 'Song', 1], ['Iroh', 'Oma', 1], ['Appa', 'Moku', 1], ['Appa', 'Song', 1], ['Appa', 'Oma', 1], ['Bumi', 'Moku', 1], ['Bumi', 'Song', 1], ['Bumi', 'Oma', 1], ['Zuko', 'Moku', 1], ['Zuko', 'Song', 1], ['Zuko', 'Oma', 1], ['How', 'Moku', 1], ['How', 'Song', 1], ['How', 'Oma', 1], ['Moku', 'Song', 1], ['Moku', 'Oma', 1], ['Song', 'Oma', 1], ['Aang', 'Mai', 15], ['Aang', 'Ty Lee', 13], ['Aang', 'Circus Master', 1], ['Aang', 'Governor', 1], ['Momo', 'Mai', 13], ['Momo', 'Ty Lee', 11], ['Momo', 'Circus Master', 1], ['Momo', 'Governor', 1], ['Appa', 'Mai', 14], ['Appa', 'Ty Lee', 12], ['Appa', 'Circus Master', 1], ['Appa', 'Governor', 1], ['Sokka', 'Mai', 14], ['Sokka', 'Ty Lee', 12], ['Sokka', 'Circus Master', 1], ['Sokka', 'Governor', 1], ['Katara', 'Mai', 14], ['Katara', 'Ty Lee', 12], ['Katara', 'Circus Master', 1], ['Katara', 'Governor', 1], ['Azula', 'Bumi', 5], ['Azula', 'Mai', 15], ['Azula', 'Ty Lee', 13], ['Azula', 'How', 20], ['Azula', 'Flopsy', 2], ['Azula', 'Circus Master', 1], ['Azula', 'Governor', 1], ['Bumi', 'Mai', 4], ['Bumi', 'Ty Lee', 4], ['Bumi', 'Circus Master', 1], ['Bumi', 'Governor', 1], ['Mai', 'Ty Lee', 13], ['Mai', 'Zuko', 16], ['Mai', 'How', 14], ['Mai', 'Flopsy', 2], ['Mai', 'Circus Master', 1], ['Mai', 'Governor', 1], ['Mai', 'Iroh', 13], ['Ty Lee', 'Zuko', 14], ['Ty Lee', 'How', 12], ['Ty Lee', 'Flopsy', 2], ['Ty Lee', 'Circus Master', 1], ['Ty Lee', 'Governor', 1], ['Ty Lee', 'Iroh', 13], ['Zuko', 'Flopsy', 2], ['Zuko', 'Circus Master', 1], ['Zuko', 'Governor', 1], ['How', 'Circus Master', 1], ['How', 'Governor', 1], ['Flopsy', 'Circus Master', 1], ['Flopsy', 'Governor', 1], ['Flopsy', 'Iroh', 2], ['Circus Master', 'Governor', 1], ['Circus Master', 'Iroh', 1], ['Governor', 'Iroh', 1], ['Iroh', 'Due', 3], ['Iroh', 'Tho', 3], ['Iroh', 'Hue', 3], ['Zuko', 'Due', 3], ['Zuko', 'Tho', 3], ['Zuko', 'Hue', 3], ['How', 'Due', 3], ['How', 'Tho', 3], ['How', 'Hue', 3], ['Appa', 'Due', 3], ['Appa', 'Tho', 3], ['Appa', 'Hue', 3], ['Momo', 'Due', 3], ['Momo', 'Tho', 3], ['Momo', 'Hue', 3], ['Katara', 'Due', 3], ['Katara', 'Tho', 3], ['Katara', 'Hue', 3], ['Sokka', 'Due', 3], ['Sokka', 'Tho', 3], ['Sokka', 'Hue', 3], ['Aang', 'Due', 3], ['Aang', 'Tho', 3], ['Aang', 'Hue', 3], ['Bumi', 'Due', 1], ['Bumi', 'Tho', 1], ['Bumi', 'Yue', 2], ['Bumi', 'Hue', 1], ['Due', 'Tho', 3], ['Due', 'Yue', 1], ['Due', 'Hue', 3], ['Tho', 'Yue', 1], ['Tho', 'Hue', 3], ['Yue', 'Hue', 1], ['Katara', 'Mongke', 2], ['Katara', 'Tong', 2], ['Katara', 'Chin', 2], ['Sokka', 'Mongke', 2], ['Sokka', 'Tong', 2], ['Sokka', 'Chin', 2], ['Momo', 'Mongke', 2], ['Momo', 'Tong', 2], ['Momo', 'Chin', 2], ['Aang', 'Mongke', 2], ['Aang', 'Tong', 2], ['Aang', 'Chin', 2], ['Mongke', 'Appa', 2], ['Mongke', 'Kyoshi', 1], ['Mongke', 'Roku', 1], ['Mongke', 'Zuko', 2], ['Mongke', 'Iroh', 2], ['Mongke', 'Tong', 1], ['Mongke', 'Chin', 1], ['Mongke', 'How', 2], ['Mongke', 'Oyagi', 1], ['Mongke', 'Koko', 1], ['Mongke', 'Suki', 1], ['Appa', 'Tong', 2], ['Appa', 'Chin', 2], ['Kyoshi', 'Roku', 3], ['Kyoshi', 'Tong', 1], ['Kyoshi', 'Chin', 2], ['Roku', 'Tong', 2], ['Roku', 'Chin', 2], ['Roku', 'Oyagi', 1], ['Roku', 'Koko', 1], ['Roku', 'Suki', 3], ['Zuko', 'Tong', 1], ['Zuko', 'Chin', 
2], ['Iroh', 'Tong', 1], ['Iroh', 'Chin', 2], ['Tong', 'Chin', 1], ['Tong', 'How', 2], ['Tong', 'Oyagi', 1], ['Tong', 'Koko', 1], ['Tong', 'Suki', 1], ['Chin', 'How', 2], ['Chin', 'Oyagi', 1], ['Chin', 'Koko', 1], ['Chin', 'Suki', 2], ['Toph', 'Sokka', 33], ['Toph', 'Momo', 30], ['Toph', 'Aang', 34], ['Toph', 'Katara', 33], ['Toph', 'Yu', 4], ['Toph', 'The Boulder', 4], ['Toph', 'How', 30], ['Toph', 'Xin Fu', 3], ['Toph', 'Hippo', 4], ['Toph', 'Bumi', 5], ['Toph', 'Fong', 3], ['Toph', 'Lao', 1], ['Toph', 'Ozai', 17], ['Toph', 'Appa', 32], ['Sokka', 'Yu', 4], ['Sokka', 'The Boulder', 4], ['Sokka', 'Xin Fu', 3], ['Sokka', 'Hippo', 4], ['Sokka', 'Lao', 1], ['Momo', 'Yu', 4], ['Momo', 'The Boulder', 4], ['Momo', 'Xin Fu', 3], ['Momo', 'Hippo', 4], ['Momo', 'Lao', 1], ['Aang', 'Yu', 4], ['Aang', 'The Boulder', 4], ['Aang', 'Xin Fu', 3], ['Aang', 'Hippo', 4], ['Aang', 'Lao', 1], ['Katara', 'Yu', 4], ['Katara', 'The Boulder', 4], ['Katara', 'Xin Fu', 3], ['Katara', 'Hippo', 4], ['Katara', 'Lao', 1], ['Yu', 'The Boulder', 1], ['Yu', 'How', 4], ['Yu', 'Xin Fu', 3], ['Yu', 'Hippo', 1], ['Yu', 'Bumi', 1], ['Yu', 'Fong', 1], ['Yu', 'Lao', 1], ['Yu', 'Ozai', 2], ['Yu', 'Appa', 4], ['The Boulder', 'How', 4], ['The Boulder', 'Xin Fu', 1], ['The Boulder', 'Hippo', 4], ['The Boulder', 'Bumi', 2], ['The Boulder', 'Fong', 1], ['The Boulder', 'Lao', 1], ['The Boulder', 'Ozai', 4], ['The Boulder', 'Appa', 4], ['How', 
'Xin Fu', 3], ['How', 'Hippo', 4], ['How', 'Fong', 3], ['How', 'Lao', 1], ['Xin Fu', 'Hippo', 1], ['Xin Fu', 'Bumi', 1], ['Xin Fu', 'Fong', 1], ['Xin Fu', 'Lao', 1], ['Xin Fu', 'Ozai', 2], ['Xin Fu', 'Appa', 3], ['Hippo', 'Bumi', 2], ['Hippo', 'Fong', 1], ['Hippo', 'Lao', 1], ['Hippo', 'Ozai', 4], ['Hippo', 'Appa', 4], ['Bumi', 'Fong', 1], ['Bumi', 'Lao', 1], ['Fong', 'Lao', 1], ['Lao', 'Ozai', 1], ['Lao', 'Appa', 1], ['Zuko', 'Gow', 1], ['Zuko', 'Gansu', 1], ['Zuko', 'Sela', 1], ['Zuko', 'Ursa', 3], ['Zuko', 'Azulon', 2], ['Zuko', 'Lu Ten', 2], ['Zuko', 'Sozin', 5], ['Gow', 'Gansu', 1], ['Gow', 'Sela', 1], ['Gow', 'Azula', 1], ['Gow', 'Ursa', 1], ['Gow', 'Ty Lee', 1], ['Gow', 'Mai', 1], ['Gow', 'Iroh', 1], ['Gow', 'Azulon', 1], ['Gow', 'How', 1], ['Gow', 'Lu Ten', 1], ['Gow', 'Ozai', 1], ['Gow', 'Sozin', 1], ['Gansu', 'Sela', 1], ['Gansu', 'Azula', 1], ['Gansu', 'Ursa', 1], ['Gansu', 'Ty Lee', 1], ['Gansu', 'Mai', 1], ['Gansu', 'Iroh', 1], ['Gansu', 'Azulon', 1], ['Gansu', 'How', 1], ['Gansu', 'Lu Ten', 1], ['Gansu', 'Ozai', 1], ['Gansu', 'Sozin', 1], ['Sela', 'Azula', 1], ['Sela', 'Ursa', 1], ['Sela', 'Ty Lee', 1], ['Sela', 'Mai', 1], ['Sela', 'Iroh', 1], ['Sela', 'Azulon', 1], ['Sela', 'How', 1], ['Sela', 'Lu Ten', 1], ['Sela', 'Ozai', 1], ['Sela', 'Sozin', 1], ['Azula', 'Ursa', 3], ['Azula', 'Azulon', 2], ['Azula', 'Lu Ten', 2], ['Azula', 'Sozin', 3], ['Ursa', 'Ty Lee', 3], ['Ursa', 'Mai', 3], ['Ursa', 'Iroh', 2], ['Ursa', 'Azulon', 1], ['Ursa', 'How', 2], ['Ursa', 'Lu Ten', 1], ['Ursa', 'Ozai', 2], ['Ursa', 'Sozin', 1], ['Ty Lee', 'Azulon', 1], ['Ty Lee', 'Lu Ten', 1], ['Ty Lee', 'Ozai', 6], ['Ty Lee', 'Sozin', 2], ['Mai', 'Azulon', 2], ['Mai', 'Lu Ten', 1], ['Mai', 'Ozai', 9], ['Mai', 'Sozin', 2], ['Iroh', 'Azulon', 2], ['Iroh', 'Lu Ten', 2], ['Iroh', 'Sozin', 5], ['Azulon', 'How', 2], ['Azulon', 'Lu Ten', 1], ['Azulon', 'Ozai', 2], ['Azulon', 'Sozin', 1], ['How', 'Lu Ten', 2], ['How', 'Sozin', 3], ['Lu Ten', 'Ozai', 1], ['Lu Ten', 'Sozin', 1], ['Ozai', 'Sozin', 4], ['Toph', 'Ty Lee', 12], ['Toph', 'Zuko', 28], ['Toph', 'Mai', 14], ['Toph', 'Azula', 21], ['Toph', 'Iroh', 25], ['Appa', 'Lu Ten', 1], ['Aang', 'Lu Ten', 1], ['Toph', 'Lu Ten', 1], ['Katara', 'Lu Ten', 1], ['Sokka', 'Lu Ten', 1], ['Lu Ten', 'Momo', 1], ['Roku', 'Toph', 6], ['Roku', 'Zei', 1], ['Roku', 'Wan Shi Tong', 1], ['Roku', 'Kuei', 2], ['Aang', 'Zei', 1], ['Aang', 'Wan Shi Tong', 1], ['Aang', 'Kuei', 10], ['Katara', 'Zei', 1], ['Katara', 'Wan Shi Tong', 1], ['Katara', 'Kuei', 10], ['Momo', 'Zei', 1], ['Momo', 'Wan Shi Tong', 1], ['Momo', 'Kuei', 10], ['Sokka', 'Zei', 1], ['Sokka', 'Wan Shi Tong', 1], ['Sokka', 'Kuei', 10], ['Toph', 'Zei', 1], ['Toph', 'Wan Shi Tong', 1], ['Toph', 'Tong', 1], ['Toph', 'Kuei', 10], ['How', 'Zei', 1], ['How', 'Wan Shi Tong', 1], ['How', 'Kuei', 10], ['Appa', 'Zei', 1], ['Appa', 'Wan Shi Tong', 1], ['Appa', 'Kuei', 9], ['Zei', 'Wan Shi Tong', 1], ['Zei', 'Tong', 1], ['Zei', 'Kuei', 1], ['Zei', 'Ozai', 1], ['Wan Shi Tong', 'Tong', 1], ['Wan Shi Tong', 'Kuei', 1], ['Wan Shi Tong', 'Ozai', 1], ['Tong', 'Kuei', 1], ['Tong', 'Ozai', 1], ['Kuei', 'Ozai', 5], ['Toph', 'Mongke', 1], ['Toph', 'Yue', 3], ['Zuko', 'Xin Fu', 2], ['Zuko', 'Yu', 3], ['Iroh', 'Xin Fu', 2], ['Iroh', 'Yu', 3], ['Mongke', 'Xin Fu', 1], ['Mongke', 'Yu', 1], ['Mongke', 'Yue', 1], ['Xin Fu', 'Yue', 1], ['Yu', 'Yue', 1], ['Aang', 'Than', 3], ['Aang', 'Ying', 2], ['Sokka', 'Than', 3], ['Sokka', 'Ying', 2], ['Momo', 'Than', 3], ['Momo', 'Ying', 2], ['Toph', 'Suki', 10], ['Toph', 'Kyoshi', 7], ['Toph', 'Than', 3], ['Toph', 'Ying', 2], ['Toph', 'Hope', 3], ['Toph', 'Jet', 6], ['Toph', 'Smellerbee', 4], ['Toph', 'Longshot', 4], ['Katara', 'Than', 3], ['Katara', 'Ying', 2], ['Appa', 'Than', 3], ['Appa', 'Ying', 2], ['Kuei', 'Fong', 2], ['Kuei', 'Suki', 3], ['Kuei', 'Kyoshi', 3], ['Kuei', 'Than', 2], ['Kuei', 'Ying', 2], ['Kuei', 'Hope', 2], ['Kuei', 'Zuko', 9], ['Kuei', 'Jet', 4], ['Kuei', 'Smellerbee', 3], ['Kuei', 'Longshot', 3], ['Kuei', 'Iroh', 8], ['Fong', 'Suki', 1], ['Fong', 'Kyoshi', 1], ['Fong', 'Than', 1], ['Fong', 'Ying', 1], ['Fong', 'Hope', 1], ['Fong', 'Jet', 2], ['Fong', 'Smellerbee', 2], ['Fong', 'Longshot', 2], ['Suki', 'Than', 1], ['Suki', 'Ying', 1], ['Suki', 'Hope', 1], ['Suki', 'Jet', 3], ['Suki', 'Smellerbee', 1], ['Suki', 'Longshot', 1], ['Kyoshi', 'Than', 1], ['Kyoshi', 'Ying', 1], ['Kyoshi', 'Hope', 1], ['Kyoshi', 'Jet', 1], ['Kyoshi', 'Smellerbee', 1], ['Kyoshi', 'Longshot', 1], ['Than', 'Ying', 2], ['Than', 'How', 3], ['Than', 'Hope', 3], ['Than', 'Zuko', 3], ['Than', 'Jet', 2], ['Than', 'Smellerbee', 2], ['Than', 'Longshot', 2], ['Than', 'Iroh', 2], ['Ying', 'How', 2], ['Ying', 'Hope', 2], ['Ying', 'Zuko', 2], ['Ying', 'Jet', 1], ['Ying', 'Smellerbee', 1], ['Ying', 'Longshot', 1], ['Ying', 'Iroh', 1], ['Hope', 'Zuko', 3], ['Hope', 'Jet', 2], ['Hope', 'Smellerbee', 2], ['Hope', 'Longshot', 2], ['Hope', 'Iroh', 2], ['Jet', 'Iroh', 5], ['Smellerbee', 'Iroh', 4], ['Longshot', 'Iroh', 4], ['Azula', 'Than', 2], ['Azula', 'Smellerbee', 1], ['Azula', 'Longshot', 1], ['Azula', 'Sung', 2], ['Azula', 'Jet', 3], ['Azula', 'Qin', 2], ['Azula', 'Hope', 2], ['Mai', 'Than', 2], ['Mai', 'Smellerbee', 1], ['Mai', 'Longshot', 1], ['Mai', 'Sung', 2], ['Mai', 'Jet', 2], ['Mai', 'Qin', 1], ['Mai', 'Hope', 2], ['Sokka', 'Sung', 2], ['Sokka', 'Qin', 2], ['Toph', 'Sung', 2], ['Toph', 'Qin', 2], ['Than', 'Ty Lee', 1], ['Than', 'Sung', 1], ['Than', 'Qin', 1], ['Aang', 'Sung', 2], ['Aang', 'Qin', 2], ['Momo', 'Sung', 2], ['Momo', 'Qin', 2], ['Appa', 'Sung', 2], ['Appa', 'Qin', 2], ['Ty Lee', 'Smellerbee', 1], ['Ty Lee', 'Longshot', 1], ['Ty Lee', 'Sung', 2], ['Ty Lee', 'Jet', 2], ['Ty Lee', 'Qin', 1], ['Ty Lee', 'Hope', 1], ['Zuko', 'Sung', 2], ['Zuko', 'Qin', 2], ['Iroh', 'Sung', 2], ['Iroh', 'Qin', 2], ['Smellerbee', 'Sung', 1], ['Smellerbee', 'Qin', 1], ['Longshot', 'Sung', 1], ['Longshot', 'Qin', 1], ['Katara', 'Sung', 2], ['Katara', 'Qin', 2], ['Sung', 'Jet', 1], ['Sung', 'Qin', 1], ['Sung', 'Hope', 1], ['Sung', 'How', 2], ['Jet', 'Qin', 1], ['Qin', 'Hope', 1], ['Qin', 'How', 2], ['Toph', 'Joo Dee', 2], ['Toph', 'Long Feng', 7], ['Toph', 'Li', 10], ['Momo', 'Joo Dee', 2], ['Momo', 'Long Feng', 6], ['Katara', 'Joo Dee', 2], ['Katara', 'Long Feng', 6], ['Aang', 'Joo Dee', 2], ['Aang', 'Long Feng', 7], ['Kuei', 'Joo Dee', 2], ['Kuei', 'Long Feng', 5], ['Kuei', 'Li', 6], ['Zuko', 'Joo Dee', 2], ['Zuko', 'Long Feng', 7], ['Iroh', 'Joo Dee', 2], ['Iroh', 'Long Feng', 7], ['Jet', 'Joo Dee', 2], ['Jet', 'Long Feng', 2], ['Jet', 'Li', 2], ['Longshot', 'Joo Dee', 2], ['Longshot', 'Long Feng', 2], ['Longshot', 'Li', 2], ['Joo Dee', 'Sokka', 2], ['Joo Dee', 'How', 2], ['Joo Dee', 'Smellerbee', 2], ['Joo Dee', 'Fong', 1], ['Joo Dee', 'Long Feng', 2], ['Joo Dee', 'Li', 2], ['Sokka', 'Long Feng', 6], ['How', 'Long Feng', 5], ['How', 'Li', 8], ['Smellerbee', 'Long Feng', 2], ['Smellerbee', 'Li', 2], ['Fong', 'Long Feng', 1], ['Fong', 'Li', 1], ['Long Feng', 'Li', 7], ['Toph', 'Hakoda', 9], ['Toph', 'Guru', 4], ['Appa', 'Guru', 4], ['Appa', 'Long Feng', 6], ['Aang', 'Guru', 4], ['Iroh', 'Guru', 3], ['Zuko', 'Guru', 4], ['Kyoshi', 'Mai', 4], ['Kyoshi', 'Ty Lee', 4], ['Kyoshi', 'Azula', 6], ['Kyoshi', 'Hakoda', 4], ['Kyoshi', 'Guru', 2], ['Kyoshi', 'Li', 3], ['Kyoshi', 'Long Feng', 3], ['Suki', 'Mai', 5], ['Suki', 'Ty Lee', 5], ['Suki', 'Azula', 8], ['Suki', 'Hakoda', 5], ['Suki', 'Guru', 1], ['Suki', 'Li', 2], ['Suki', 'Long Feng', 2], ['Mai', 'Hakoda', 6], ['Mai', 'Guru', 4], ['Mai', 'Li', 6], ['Mai', 'Long Feng', 4], ['Ty Lee', 'Hakoda', 4], ['Ty Lee', 'Guru', 3], ['Ty Lee', 'Li', 6], ['Ty Lee', 'Long Feng', 5], ['Azula', 'Hakoda', 8], ['Azula', 'Guru', 4], ['Azula', 'Li', 8], ['Azula', 'Long Feng', 5], ['Hakoda', 'Guru', 2], ['Hakoda', 'Li', 4], ['Hakoda', 'Long Feng', 2], ['Guru', 'Li', 3], ['Guru', 'Long Feng', 3], ['Appa', 'Pao', 2], ['Appa', 'Quon', 1], ['Appa', 'Joo Dee', 1], ['Sokka', 'Pao', 2], ['Sokka', 'Quon', 1], ['Toph', 'Pao', 2], ['Toph', 
'Quon', 1], ['Toph', 'The Duke', 9], ['Toph', 'Pipsqueak', 5], ['Momo', 'Pao', 2], ['Momo', 'Quon', 1], ['Katara', 'Pao', 2], ['Katara', 'Quon', 1], ['Aang', 'Pao', 2], ['Aang', 'Quon', 1], ['Iroh', 'Pao', 1], ['Iroh', 'Quon', 1], ['Iroh', 'The Duke', 7], ['Iroh', 'Pipsqueak', 4], ['Zuko', 'Pao', 2], ['Zuko', 'Quon', 1], ['Pao', 'How', 2], ['Pao', 'Quon', 1], ['Pao', 'Li', 2], ['Pao', 'Joo Dee', 1], ['Pao', 'Kuei', 2], ['Pao', 'Jet', 1], ['Pao', 'Smellerbee', 1], ['Pao', 'Longshot', 1], ['Pao', 'Long Feng', 1], ['Pao', 'The Duke', 2], ['Pao', 'Pipsqueak', 2], ['How', 'Quon', 1], ['Quon', 'Li', 1], ['Quon', 'Joo Dee', 1], ['Quon', 'Kuei', 1], ['Quon', 'Jet', 1], ['Quon', 'Smellerbee', 1], ['Quon', 'Longshot', 1], ['Quon', 'Long Feng', 1], ['Quon', 'The Duke', 1], ['Quon', 'Pipsqueak', 1], ['Li', 'The Duke', 3], ['Li', 'Pipsqueak', 3], ['Joo Dee', 'The Duke', 1], ['Joo Dee', 'Pipsqueak', 1], ['Kuei', 'The Duke', 2], ['Kuei', 'Pipsqueak', 2], ['Long Feng', 'The Duke', 1], ['Long Feng', 'Pipsqueak', 1], ['Kuei', 'Bosco', 4], ['Kuei', 'Yu', 2], ['Kuei', 'Azula', 6], ['Kuei', 'Ty Lee', 4], ['Appa', 'Bosco', 4], ['Momo', 'Bosco', 4], ['Aang', 'Bosco', 4], ['Sokka', 'Bosco', 4], ['Katara', 'Bosco', 4], ['Long Feng', 'Bosco', 3], ['Long Feng', 'Yu', 2], ['Li', 'Bosco', 3], ['Li', 'Yu', 2], ['Toph', 'Bosco', 4], ['How', 'Bosco', 4], ['Zuko', 'Bosco', 4], ['Iroh', 'Bosco', 4], ['Bosco', 'Kyoshi', 2], ['Bosco', 'Yu', 2], ['Bosco', 'Azula', 4], ['Bosco', 'Ty Lee', 3], ['Kyoshi', 'Yu', 2], ['Yu', 'Azula', 2], ['Yu', 'Ty Lee', 2], ['Guru', 'Sokka', 3], ['Guru', 'Bosco', 2], ['Guru', 'Kuei', 2], ['Guru', 'Katara', 3], ['Guru', 'Momo', 3], ['Guru', 'How', 3], ['Guru', 'Xin Fu', 1], ['Guru', 'Yu', 1], ['Guru', 'Ozai', 2], ['Guru', 'Bato', 1], ['Guru', 'Gyatso', 1], ['Hakoda', 'Bosco', 1], ['Hakoda', 'Kuei', 2], ['Hakoda', 'Xin Fu', 1], ['Hakoda', 'Yu', 1], ['Hakoda', 'Ozai', 5], ['Hakoda', 'Gyatso', 1], ['Bosco', 'Mai', 2], ['Bosco', 'Xin Fu', 1], ['Bosco', 'Ozai', 2], ['Bosco', 'Bato', 1], ['Bosco', 'Gyatso', 1], ['Ty Lee', 'Xin Fu', 1], ['Ty Lee', 'Bato', 2], ['Ty Lee', 'Gyatso', 1], ['Mai', 'Kuei', 4], ['Mai', 'Xin Fu', 1], ['Mai', 'Yu', 1], ['Mai', 'Bato', 4], ['Mai', 'Gyatso', 1], ['Kyoshi', 'Xin Fu', 1], ['Kyoshi', 'Ozai', 4], ['Kyoshi', 'Bato', 3], ['Kyoshi', 'Gyatso', 1], ['Kuei', 'Xin Fu', 1], ['Kuei', 'Bato', 2], ['Kuei', 'Gyatso', 1], ['Li', 'Xin Fu', 1], ['Li', 'Bato', 3], ['Li', 'Gyatso', 1], ['Azula', 'Xin Fu', 1], ['Azula', 'Bato', 5], ['Azula', 'Gyatso', 2], ['Xin Fu', 'Bato', 1], ['Xin Fu', 'Gyatso', 1], ['Xin Fu', 'Long Feng', 1], ['Yu', 'Bato', 1], ['Yu', 'Gyatso', 1], ['Toph', 'Bato', 5], ['Toph', 'Gyatso', 2], ['Ozai', 'Bato', 5], ['Ozai', 'Long Feng', 2], ['Bato', 'Gyatso', 1], ['Bato', 'Long Feng', 1], ['Gyatso', 'Long Feng', 1], ['Li', 'Sung', 1], ['Kuei', 'Sung', 1], ['Long Feng', 'Sung', 1], ['Guru', 'Sung', 1], ['Bosco', 'Sung', 1], ['Aang', 'Lo', 3], ['Aang', 'Chan', 2], ['Hakoda', 'Lo', 1], ['Hakoda', 'Pao', 1], ['Hakoda', 'Jin', 1], ['Hakoda', 'Than', 1], ['Hakoda', 'Ying', 1], ['Hakoda', 'Hope', 1], ['Hakoda', 'Pipsqueak', 4], ['Hakoda', 'The Duke', 6], ['Hakoda', 'Chan', 1], ['Hakoda', 'Roku', 2], ['Hakoda', 'Yue', 1], ['Bato', 'Lo', 1], ['Bato', 'Pao', 1], ['Bato', 'Jin', 1], ['Bato', 'Than', 1], ['Bato', 'Ying', 1], ['Bato', 'Hope', 1], ['Bato', 'Pipsqueak', 4], ['Bato', 'The Duke', 4], ['Bato', 'Chan', 1], ['Bato', 'Roku', 2], ['Bato', 'Yue', 1], ['Momo', 'Lo', 3], ['Momo', 'Chan', 2], ['Toph', 'Lo', 3], ['Toph', 'Jin', 1], ['Toph', 'Chan', 2], ['Katara', 'Lo', 3], ['Katara', 'Chan', 2], ['Appa', 'Lo', 3], ['Appa', 'Chan', 2], ['Zuko', 'Lo', 3], ['Zuko', 'Jin', 1], ['Zuko', 'Chan', 2], ['Mai', 'Lo', 3], ['Mai', 'Pao', 1], ['Mai', 'Jin', 1], ['Mai', 'Ying', 1], ['Mai', 'Pipsqueak', 3], ['Mai', 'The Duke', 3], ['Mai', 'Chan', 2], ['Mai', 'Roku', 2], ['Mai', 'Yue', 2], ['How', 'Lo', 2], ['How', 'Chan', 2], ['Lo', 'Li', 3], ['Lo', 'Pao', 1], ['Lo', 'Jin', 1], ['Lo', 'Than', 1], ['Lo', 'Ying', 1], ['Lo', 'Hope', 1], ['Lo', 'Sokka', 3], ['Lo', 'Kuei', 1], ['Lo', 'Pipsqueak', 1], ['Lo', 'The Duke', 1], ['Lo', 'Chan', 2], ['Lo', 'Azula', 3], ['Lo', 'Ozai', 2], ['Lo', 'Roku', 1], ['Lo', 'Yue', 1], ['Li', 'Jin', 1], ['Li', 'Than', 1], ['Li', 'Ying', 1], ['Li', 'Hope', 1], ['Li', 'Chan', 2], ['Li', 'Roku', 1], ['Pao', 'Jin', 1], ['Pao', 'Than', 1], ['Pao', 'Ying', 1], ['Pao', 'Hope', 1], ['Pao', 'Chan', 1], ['Pao', 'Azula', 1], ['Pao', 'Ozai', 1], ['Pao', 'Roku', 1], ['Pao', 'Yue', 1], ['Jin', 'Than', 1], ['Jin', 'Ying', 1], ['Jin', 'Kuei', 1], ['Jin', 'Pipsqueak', 1], ['Jin', 'The Duke', 1], ['Jin', 'Chan', 1], ['Jin', 'Azula', 1], ['Jin', 'Ozai', 1], ['Jin', 'Roku', 1], ['Jin', 'Yue', 1], ['Than', 'Pipsqueak', 1], ['Than', 'The Duke', 1], ['Than', 'Chan', 1], ['Than', 'Ozai', 1], ['Than', 'Roku', 1], ['Than', 'Yue', 1], ['Ying', 'Pipsqueak', 1], ['Ying', 'The Duke', 1], ['Ying', 'Chan', 1], ['Ying', 'Azula', 1], ['Ying', 'Ozai', 1], ['Ying', 'Roku', 1], ['Ying', 'Yue', 1], ['Hope', 'Pipsqueak', 1], ['Hope', 'The Duke', 1], ['Hope', 'Chan', 1], ['Hope', 'Roku', 1], ['Hope', 'Yue', 1], ['Sokka', 'Chan', 2], ['Kuei', 'Chan', 1], ['Kuei', 'Yue', 2], ['Pipsqueak', 'Chan', 1], ['Pipsqueak', 'Azula', 4], ['Pipsqueak', 'Ozai', 4], ['Pipsqueak', 'Roku', 2], ['Pipsqueak', 'Yue', 1], ['The Duke', 'Chan', 1], ['The Duke', 'Azula', 6], ['The Duke', 'Ozai', 5], ['The Duke', 'Roku', 3], ['The Duke', 'Yue', 1], ['Chan', 'Azula', 2], ['Chan', 'Ozai', 1], ['Chan', 'Roku', 1], ['Chan', 'Yue', 1], ['Azula', 'Yue', 2], ['Zuko', 'Kwan', 2], ['Zuko', 'Hide', 1], ['Zuko', 'On Ji', 1], ['Zuko', 'Shoji', 1], ['Sokka', 'Kwan', 2], ['Sokka', 'Hide', 1], ['Sokka', 'Sozin', 4], ['Sokka', 'On Ji', 1], ['Sokka', 'Shoji', 1], ['Momo', 'Kwan', 1], ['Momo', 'Hide', 1], ['Momo', 'Sozin', 2], ['Momo', 'On Ji', 1], ['Momo', 'Shoji', 1], ['Aang', 'Kwan', 2], ['Aang', 'Hide', 1], ['Aang', 'Sozin', 4], ['Aang', 'On Ji', 1], ['Aang', 'Shoji', 1], ['How', 'Kwan', 1], ['How', 'Hide', 1], ['How', 'On Ji', 1], ['How', 'Shoji', 1], ['Katara', 'Kwan', 2], ['Katara', 'Hide', 1], ['Katara', 'Sozin', 4], ['Katara', 'On Ji', 1], ['Katara', 'Shoji', 1], ['Toph', 'Kwan', 2], ['Toph', 'Hide', 1], ['Toph', 'Sozin', 4], ['Toph', 'On Ji', 1], ['Toph', 'Shoji', 1], ['Kwan', 'Hide', 1], ['Kwan', 'Iroh', 2], ['Kwan', 'Ozai', 1], ['Kwan', 'Sozin', 2], ['Kwan', 'On Ji', 1], ['Kwan', 'Mai', 1], ['Kwan', 'Ty Lee', 1], ['Kwan', 'Appa', 2], ['Kwan', 'Shoji', 1], ['Hide', 'Iroh', 1], ['Hide', 'Ozai', 1], ['Hide', 'Sozin', 1], ['Hide', 'On Ji', 1], ['Hide', 'Mai', 1], 
['Hide', 'Ty Lee', 1], ['Hide', 'Appa', 1], ['Hide', 'Shoji', 1], ['Iroh', 'On Ji', 1], ['Iroh', 'Shoji', 1], ['Ozai', 'On Ji', 1], ['Ozai', 'Shoji', 1], ['Sozin', 'On Ji', 1], ['Sozin', 'Appa', 4], ['Sozin', 'Shoji', 1], ['On Ji', 'Mai', 1], ['On Ji', 'Ty Lee', 1], ['On Ji', 'Appa', 1], ['On Ji', 'Shoji', 1], ['Mai', 'Shoji', 1], ['Ty Lee', 'Shoji', 1], ['Appa', 'Shoji', 1], ['Painted Lady', 'Aang', 2], ['Painted Lady', 'Momo', 2], ['Painted Lady', 'Appa', 2], ['Painted Lady', 'Dock', 1], ['Painted Lady', 'How', 2], ['Painted Lady', 'Ozai', 2], ['Painted Lady', 'Sokka', 2], ['Painted Lady', 'Katara', 2], ['Painted Lady', 'Toph', 2], ['Painted Lady', 'Mung', 1], ['Aang', 'Dock', 1], ['Aang', 'Mung', 1], ['Momo', 'Dock', 1], ['Momo', 'Mung', 1], ['Appa', 'Dock', 1], ['Appa', 'Mung', 1], ['Dock', 'How', 1], ['Dock', 'Ozai', 1], ['Dock', 'Sokka', 1], ['Dock', 'Katara', 1], ['Dock', 'Toph', 1], ['Dock', 'Mung', 1], ['How', 'Mung', 1], ['Ozai', 'Mung', 1], ['Sokka', 'Mung', 1], ['Katara', 'Mung', 1], ['Toph', 'Mung', 1], ['Katara', 'Poon', 3], ['Katara', 'Fat', 1], ['Katara', 'Piandao', 3], ['Aang', 'Poon', 3], ['Aang', 'Fat', 1], ['Aang', 'Piandao', 3], ['Appa', 'Poon', 3], ['Appa', 'Fat', 1], ['Appa', 'Piandao', 3], ['Sokka', 'Poon', 3], ['Sokka', 'Fat', 1], ['Sokka', 'Piandao', 3], ['Toph', 'Poon', 3], ['Toph', 'Fat', 1], ['Toph', 'Piandao', 3], ['Momo', 'Poon', 3], ['Momo', 'Fat', 1], ['Momo', 'Piandao', 3], ['Poon', 'Iroh', 3], ['Poon', 'Fat', 1], ['Poon', 'Piandao', 1], ['Poon', 'How', 3], ['Iroh', 'Fat', 1], ['Iroh', 'Piandao', 3], ['Fat', 'Piandao', 1], ['Fat', 'How', 1], ['Piandao', 'How', 2], ['Ty Lee', 'Lo', 2], ['Ty Lee', 'Ruon-Jian', 1], ['Ty Lee', 'Chan', 1], ['Ty Lee', 'Combustion Man', 2], ['Zuko', 'Ruon-Jian', 1], ['Zuko', 'Combustion Man', 3], ['Azula', 'Ruon-Jian', 1], ['Azula', 'Combustion Man', 3], ['Mai', 'Ruon-Jian', 1], ['Mai', 'Combustion Man', 2], ['Li', 'Ruon-Jian', 1], ['Li', 'Ursa', 2], ['Li', 'Combustion Man', 1], ['Lo', 'Ruon-Jian', 1], ['Lo', 'Ursa', 2], ['Lo', 'Combustion Man', 1], ['Sokka', 'Ruon-Jian', 1], ['Sokka', 'Ursa', 2], ['Sokka', 'Combustion Man', 4], ['Aang', 'Ruon-Jian', 1], ['Aang', 'Ursa', 2], ['Aang', 'Combustion Man', 4], ['Momo', 'Ruon-Jian', 1], ['Momo', 'Ursa', 2], ['Momo', 'Combustion Man', 4], ['Toph', 'Ruon-Jian', 1], ['Toph', 'Ursa', 2], ['Toph', 'Combustion Man', 4], ['Katara', 'Ruon-Jian', 1], ['Katara', 'Ursa', 2], ['Katara', 'Combustion Man', 4], ['Ruon-Jian', 'Chan', 1], ['Ruon-Jian', 'How', 1], ['Ruon-Jian', 'Ursa', 1], ['Ruon-Jian', 'Combustion Man', 1], ['Ruon-Jian', 'Appa', 1], ['Chan', 'Ursa', 1], ['Chan', 'Combustion Man', 1], ['How', 'Combustion Man', 4], ['Ursa', 'Combustion Man', 1], ['Ursa', 'Appa', 2], ['Combustion Man', 'Appa', 4], ['Aang', 'Fang', 1], ['Aang', 'Ta Min', 1], ['Roku', 'Sozin', 3], ['Roku', 'Fang', 1], ['Roku', 'Ta Min', 1], ['Zuko', 'Fang', 1], ['Zuko', 'Ta Min', 1], ['Appa', 'Fang', 1], ['Appa', 'Ta Min', 1], ['Katara', 'Fang', 1], ['Katara', 'Ta Min', 1], ['Sokka', 'Fang', 1], ['Sokka', 'Ta Min', 1], ['Azula', 'Fang', 1], ['Azula', 'Ta Min', 1], ['Sozin', 'Fang', 1], ['Sozin', 'Gyatso', 1], ['Sozin', 'Ta Min', 1], ['Fang', 'Gyatso', 1], ['Fang', 'Ta Min', 1], ['Fang', 'Iroh', 1], ['Fang', 'Toph', 1], ['Fang', 'Ozai', 1], ['Gyatso', 'Ta Min', 1], ['Ta Min', 'Iroh', 1], ['Ta Min', 'Toph', 1], ['Ta Min', 'Ozai', 1], ['Toph', 'Hawky', 1], ['Ozai', 'Hawky', 1], ['Ozai', 'Combustion Man', 3], ['How', 'Hawky', 1], ['Katara', 'Hawky', 1], ['Aang', 'Hawky', 1], ['Sokka', 'Hawky', 1], ['Momo', 'Hawky', 1], ['Hawky', 'Combustion Man', 1], ['Hawky', 'Appa', 1], ['Appa', 'Hama', 1], ['Appa', 'Ding', 1], ['Aang', 'Hama', 1], ['Aang', 'Ding', 1], ['Toph', 'Hama', 1], ['Toph', 'Kanna', 2], ['Toph', 'Ding', 1], ['Sokka', 'Hama', 1], ['Sokka', 'Ding', 1], ['Momo', 'Hama', 1], ['Momo', 'Ding', 1], ['Hama', 'Katara', 1], ['Hama', 'How', 1], ['Hama', 'Kanna', 1], ['Hama', 'Ding', 1], ['Katara', 'Ding', 1], ['How', 'Ding', 1], ['Kanna', 'Ding', 1], ['Aang', 'Ming', 1], ['Aang', 'Azulon', 1], ['Sokka', 'Ming', 1], ['Sokka', 'Azulon', 1], ['Katara', 'Ming', 1], ['Katara', 'Azulon', 1], ['Appa', 'Ming', 1], ['Appa', 'Azulon', 1], ['Toph', 'Due', 2], ['Toph', 'Tho', 2], ['Toph', 'Hue', 2], ['Toph', 'Haru', 7], ['Toph', 'Tyro', 2], ['Toph', 'The Mechanist', 3], ['Toph', 'Teo', 6], ['Toph', 'Ming', 1], ['Toph', 'Azulon', 1], ['Momo', 'Ming', 1], ['Momo', 'Azulon', 1], ['Azula', 'Due', 2], ['Azula', 'Tho', 2], ['Azula', 'Hue', 2], ['Azula', 'Haru', 5], ['Azula', 'Tyro', 2], ['Azula', 'Hippo', 3], ['Azula', 'The Boulder', 3], ['Azula', 'The Mechanist', 3], ['Azula', 'Teo', 5], ['Azula', 'Poon', 2], ['Azula', 'Ming', 1], ['Hakoda', 'Due', 2], ['Hakoda', 'Tho', 2], ['Hakoda', 'Hue', 2], ['Hakoda', 'Haru', 5], ['Hakoda', 'Tyro', 2], ['Hakoda', 'Hippo', 3], ['Hakoda', 'The Boulder', 3], 
['Hakoda', 'The Mechanist', 3], ['Hakoda', 'Teo', 5], ['Hakoda', 'Poon', 2], ['Hakoda', 'Ming', 1], ['Hakoda', 'Azulon', 1], ['Bato', 'Due', 2], ['Bato', 'Tho', 2], ['Bato', 'Hue', 2], ['Bato', 'Haru', 3], ['Bato', 'Tyro', 2], ['Bato', 'Hippo', 3], ['Bato', 'The Boulder', 3], ['Bato', 'The Mechanist', 3], ['Bato', 'Teo', 3], ['Bato', 'Poon', 2], ['Bato', 'Ming', 1], ['Bato', 'Azulon', 1], ['Due', 'Haru', 2], ['Due', 'Tyro', 2], ['Due', 'Hippo', 2], ['Due', 'The Boulder', 2], ['Due', 'The Mechanist', 2], ['Due', 'Teo', 2], ['Due', 'The Duke', 2], ['Due', 'Pipsqueak', 2], ['Due', 'Poon', 2], ['Due', 'Ming', 1], ['Due', 'Ozai', 2], ['Due', 'Kyoshi', 1], ['Due', 'Azulon', 1], ['Due', 'Mai', 1], ['Tho', 'Haru', 2], ['Tho', 'Tyro', 2], ['Tho', 'Hippo', 2], ['Tho', 'The Boulder', 2], ['Tho', 'The Mechanist', 2], ['Tho', 'Teo', 2], ['Tho', 'The Duke', 2], ['Tho', 'Pipsqueak', 2], ['Tho', 'Poon', 2], ['Tho', 'Ming', 1], ['Tho', 'Ozai', 2], ['Tho', 'Kyoshi', 1], ['Tho', 'Azulon', 1], ['Tho', 'Mai', 1], ['Hue', 'Haru', 2], ['Hue', 'Tyro', 2], ['Hue', 'Hippo', 2], ['Hue', 'The Boulder', 2], ['Hue', 'The Mechanist', 2], ['Hue', 'Teo', 2], ['Hue', 'The Duke', 2], ['Hue', 'Pipsqueak', 2], ['Hue', 'Poon', 2], ['Hue', 'Ming', 1], ['Hue', 'Ozai', 2], ['Hue', 'Kyoshi', 1], ['Hue', 'Azulon', 1], ['Hue', 'Mai', 1], ['Haru', 'Hippo', 3], ['Haru', 'The Boulder', 3], ['Haru', 'The Mechanist', 3], ['Haru', 'Teo', 6], ['Haru', 'The Duke', 7], ['Haru', 'Pipsqueak', 3], ['Haru', 'Poon', 2], ['Haru', 'Iroh', 6], ['Haru', 'Ming', 1], ['Haru', 'Kyoshi', 2], ['Haru', 'Zuko', 7], ['Haru', 'Azulon', 1], ['Haru', 'Mai', 2], ['Tyro', 'Hippo', 2], ['Tyro', 'The Boulder', 2], ['Tyro', 'The Mechanist', 2], ['Tyro', 'Teo', 2], ['Tyro', 'The Duke', 2], ['Tyro', 'Pipsqueak', 2], ['Tyro', 'Poon', 2], ['Tyro', 'Iroh', 2], ['Tyro', 'Ming', 1], ['Tyro', 'Kyoshi', 1], ['Tyro', 'Zuko', 2], ['Tyro', 'Azulon', 1], ['Tyro', 'Mai', 1], ['Hippo', 'The Mechanist', 3], ['Hippo', 'Teo', 3], ['Hippo', 'The Duke', 3], ['Hippo', 'Pipsqueak', 3], ['Hippo', 'Poon', 2], ['Hippo', 'Iroh', 3], ['Hippo', 'Ming', 1], ['Hippo', 'Kyoshi', 2], ['Hippo', 'Zuko', 3], ['Hippo', 'Azulon', 1], ['Hippo', 'Mai', 2], ['The Boulder', 'The Mechanist', 3], ['The Boulder', 'Teo', 3], ['The Boulder', 'The Duke', 
3], ['The Boulder', 'Pipsqueak', 3], ['The Boulder', 'Poon', 2], ['The Boulder', 'Iroh', 3], ['The Boulder', 'Ming', 1], ['The Boulder', 'Kyoshi', 2], ['The Boulder', 'Zuko', 3], ['The Boulder', 'Azulon', 1], ['The Boulder', 'Mai', 2], ['The Mechanist', 'The Duke', 3], ['The Mechanist', 'Pipsqueak', 3], ['The Mechanist', 'Poon', 2], ['The Mechanist', 'Iroh', 3], ['The Mechanist', 'Ming', 1], ['The Mechanist', 'Ozai', 3], ['The Mechanist', 'Kyoshi', 2], ['The Mechanist', 'Zuko', 3], ['The Mechanist', 'Azulon', 1], ['The Mechanist', 'Mai', 2], ['Teo', 'The Duke', 
6], ['Teo', 'Pipsqueak', 3], ['Teo', 'Poon', 2], ['Teo', 'Iroh', 5], ['Teo', 'Ming', 1], ['Teo', 'Ozai', 4], ['Teo', 'Kyoshi', 2], ['Teo', 'Zuko', 6], ['Teo', 'Azulon', 1], ['Teo', 'Mai', 2], ['The Duke', 'Poon', 2], ['The Duke', 'Ming', 1], ['The Duke', 'Kyoshi', 2], ['The Duke', 'Azulon', 1], ['Pipsqueak', 'Poon', 2], ['Pipsqueak', 'Ming', 1], ['Pipsqueak', 'Kyoshi', 2], ['Pipsqueak', 'Azulon', 1], ['Poon', 'Ming', 1], ['Poon', 'Ozai', 2], ['Poon', 'Kyoshi', 1], ['Poon', 'Zuko', 2], ['Poon', 'Azulon', 1], ['Poon', 'Mai', 1], ['Iroh', 'Ming', 1], ['Ming', 'Ozai', 1], ['Ming', 'Kyoshi', 1], ['Ming', 'Zuko', 1], ['Ming', 'How', 1], ['Ming', 'Azulon', 1], ['Ming', 'Mai', 1], ['Kyoshi', 'Azulon', 1], ['Hue', 'Qin', 1], ['Hue', 'Li', 1], ['Hakoda', 'Qin', 1], ['Ozai', 'Qin', 1], ['The Mechanist', 'Qin', 1], ['The Mechanist', 'Li', 1], ['The Boulder', 'Qin', 1], ['The Boulder', 'Li', 1], ['Hippo', 'Qin', 1], ['Hippo', 'Li', 1], ['Bato', 'Qin', 1], ['Qin', 'Li', 1], ['Qin', 'Tyro', 1], ['Qin', 'Poon', 1], ['Qin', 'Due', 1], ['Qin', 'Tho', 1], ['Qin', 'Teo', 1], ['Qin', 'The Duke', 1], ['Qin', 'Pipsqueak', 1], ['Qin', 'Haru', 1], ['Li', 'Tyro', 1], ['Li', 'Poon', 1], ['Li', 'Due', 1], ['Li', 'Tho', 1], ['Li', 'Teo', 1], ['Li', 'Haru', 1], ['Toph', 'Jeong Jeong', 3], ['Toph', 'Zhao', 2], ['Haru', 'Jeong Jeong', 1], ['Haru', 'Combustion Man', 1], ['Haru', 'Zhao', 1], ['Teo', 'Jeong Jeong', 1], ['Teo', 'Combustion Man', 1], ['Teo', 'Zhao', 1], ['The Duke', 'Jeong Jeong', 1], ['The Duke', 'Combustion Man', 1], ['The Duke', 'Zhao', 1], ['Zuko', 'Jeong Jeong', 3], ['Iroh', 'Jeong Jeong', 3], ['Iroh', 'Combustion Man', 2], ['Jeong Jeong', 'Azula', 3], ['Jeong Jeong', 'Combustion Man', 1], 
['Azula', 'Zhao', 2], ['Combustion Man', 'Zhao', 2], ['Zuko', 'Ham Ghao', 1], ['Aang', 'Ham Ghao', 1], ['Sokka', 'Ham Ghao', 1], ['Appa', 'Ham Ghao', 1], ['Toph', 'Ham Ghao', 1], ['Haru', 'Roku', 2], ['Haru', 'Sozin', 1], ['Haru', 'Ham Ghao', 1], ['Haru', 'Kwan', 1], ['The Duke', 'Sozin', 1], ['The Duke', 'Ham Ghao', 1], ['The Duke', 'Kwan', 1], ['Katara', 'Ham Ghao', 1], ['Roku', 'Ham Ghao', 1], ['Roku', 'Kwan', 1], ['Sozin', 'Ham Ghao', 1], ['Iroh', 'Ham Ghao', 1], ['Ham Ghao', 'Kwan', 1], ['Zuko', 'Chit Sang', 3], ['Katara', 'Chit Sang', 3], ['Aang', 'Chit Sang', 3], ['Toph', 'Chit Sang', 3], ['The Duke', 'Chit Sang', 2], ['The Duke', 'Suki', 3], ['Haru', 'Chit Sang', 2], ['Haru', 'Suki', 3], ['Iroh', 'Chit Sang', 2], ['Teo', 'Chit Sang', 2], ['Teo', 'Suki', 3], ['Sokka', 'Chit Sang', 3], ['Appa', 'Chit Sang', 2], ['How', 'Chit Sang', 3], ['Momo', 'Chit Sang', 2], ['Chit Sang', 'Suki', 3], ['Chit Sang', 'Hakoda', 3], ['Chit Sang', 'Mai', 1], ['Chit Sang', 'Azula', 2], ['Chit Sang', 'Ty Lee', 1], ['Chit Sang', 'Jet', 1], ['Chit Sang', 'Yon Rha', 1], ['Chit Sang', 'Kya', 1], ['Teo', 'Jet', 1], ['Teo', 'Yon Rha', 1], ['Teo', 'Kya', 1], ['The Duke', 'Yon Rha', 1], ['The Duke', 'Kya', 1], ['Zuko', 'Yon Rha', 1], ['Zuko', 'Kya', 1], ['Aang', 'Yon Rha', 1], ['Aang', 'Kya', 1], ['Appa', 'Yon Rha', 1], ['Appa', 'Kya', 1], ['Katara', 'Yon Rha', 1], ['Katara', 'Kya', 1], ['Haru', 'Jet', 1], ['Haru', 'Yon Rha', 1], ['Haru', 'Kya', 1], ['Toph', 'Yon Rha', 1], ['Toph', 'Kya', 1], ['Sokka', 'Yon Rha', 1], ['Sokka', 'Kya', 1], ['Azula', 'Yon Rha', 1], ['Azula', 'Kya', 1], ['Hakoda', 'Jet', 1], ['Hakoda', 'Yon Rha', 1], ['Hakoda', 'Kya', 1], ['Suki', 'Yon Rha', 1], ['Suki', 'Kya', 1], ['How', 'Yon Rha', 1], ['How', 'Kya', 1], ['Jet', 'Yon Rha', 1], ['Jet', 'Kya', 1], ['Momo', 'Yon Rha', 1], ['Momo', 'Kya', 1], ['Yon Rha', 'Kya', 1], ['Katara', 'Actress Katara', 1], ['Katara', 'Actor Sokka', 1], ['Katara', 'Actor Zuko', 1], ['Katara', 'Actor Bumi', 1], ['Katara', 'Actor Jet', 1], ['Katara', 'Actress Yue', 1], ['Katara', 'Actor Toph', 2], ['Katara', 'Actress Azula', 1], ['Toph', 'Actress Katara', 1], ['Toph', 'Actor Sokka', 1], ['Toph', 'Actor Zuko', 1], ['Toph', 'Actor Bumi', 1], ['Toph', 'Flopsy', 1], ['Toph', 'Actor Jet', 1], ['Toph', 'Actress Yue', 1], ['Toph', 'Actor Toph', 2], ['Toph', 'Actress Azula', 1], ['Zuko', 'Painted Lady', 1], ['Zuko', 'Actress Katara', 1], ['Zuko', 'Actor Sokka', 1], ['Zuko', 'Actor Zuko', 1], ['Zuko', 'Actor Bumi', 1], ['Zuko', 'Actor Jet', 1], ['Zuko', 'Actress Yue', 1], ['Zuko', 'Actor Toph', 2], ['Zuko', 'Actress Azula', 1], ['Aang', 'Actress Katara', 1], ['Aang', 'Actor Sokka', 1], ['Aang', 'Actor Zuko', 1], ['Aang', 'Actor Bumi', 1], ['Aang', 'Actor Jet', 1], ['Aang', 'Actress Yue', 1], ['Aang', 'Actor Toph', 2], ['Aang', 'Actress Azula', 1], ['Ozai', 'Suki', 5], ['Ozai', 'Actress Katara', 1], ['Ozai', 'Actor Sokka', 1], ['Ozai', 'Actor Zuko', 1], ['Ozai', 'Actor Bumi', 1], ['Ozai', 'Flopsy', 1], ['Ozai', 'Jet', 1], ['Ozai', 'Actor Jet', 1], ['Ozai', 'Actress Yue', 1], ['Ozai', 'Actor Toph', 2], ['Ozai', 'Actress Azula', 1], ['Sokka', 'Actress Katara', 1], ['Sokka', 'Actor Sokka', 1], ['Sokka', 'Actor Zuko', 1], ['Sokka', 'Actor Bumi', 1], ['Sokka', 'Actor Jet', 1], ['Sokka', 'Actress Yue', 1], ['Sokka', 'Actor Toph', 2], ['Sokka', 'Actress Azula', 1], ['Suki', 'Painted Lady', 1], ['Suki', 'Actress Katara', 1], ['Suki', 'Actor Sokka', 1], ['Suki', 'Actor Zuko', 1], ['Suki', 'Bumi', 4], ['Suki', 'Actor Bumi', 1], ['Suki', 'Flopsy', 1], ['Suki', 'Actor Jet', 1], ['Suki', 'Yue', 1], ['Suki', 'Actress Yue', 1], ['Suki', 'Zhao', 1], ['Suki', 'Actor Toph', 2], ['Suki', 'Actress Azula', 1], ['Suki', 'Combustion Man', 1], ['How', 'Actress Katara', 1], ['How', 'Actor Sokka', 1], ['How', 'Actor Zuko', 1], ['How', 'Actor Bumi', 1], ['How', 'Actor Jet', 1], ['How', 'Actress Yue', 1], ['How', 'Actor Toph', 2], ['How', 'Actress Azula', 1], ['Painted Lady', 'Actress Katara', 1], ['Painted Lady', 
'Actor Sokka', 1], ['Painted Lady', 'Iroh', 1], ['Painted Lady', 'Actor Zuko', 1], ['Painted Lady', 'Bumi', 1], ['Painted Lady', 'Actor Bumi', 1], ['Painted Lady', 'Flopsy', 1], ['Painted Lady', 'Jet', 1], ['Painted Lady', 'Actor Jet', 1], ['Painted Lady', 'Yue', 1], ['Painted Lady', 'Actress Yue', 1], ['Painted Lady', 'Zhao', 1], ['Painted Lady', 'Actor Toph', 1], ['Painted Lady', 'Actress Azula', 1], ['Painted Lady', 'Azula', 1], ['Painted Lady', 'Mai', 1], ['Painted Lady', 'Kuei', 1], ['Painted Lady', 'Ty Lee', 1], ['Painted Lady', 'Combustion Man', 1], ['Actress Katara', 'Actor Sokka', 1], ['Actress Katara', 'Appa', 1], ['Actress Katara', 'Iroh', 1], ['Actress Katara', 'Actor Zuko', 1], ['Actress Katara', 'Momo', 1], ['Actress Katara', 'Bumi', 1], ['Actress Katara', 'Actor Bumi', 1], ['Actress Katara', 'Flopsy', 1], ['Actress Katara', 'Jet', 1], ['Actress Katara', 'Actor Jet', 1], ['Actress Katara', 'Yue', 1], ['Actress Katara', 'Actress Yue', 1], ['Actress Katara', 'Zhao', 1], ['Actress Katara', 'Actor Toph', 1], ['Actress Katara', 'Actress Azula', 1], ['Actress Katara', 'Azula', 1], ['Actress Katara', 'Mai', 1], 
['Actress Katara', 'Kuei', 1], ['Actress Katara', 'Ty Lee', 1], ['Actress Katara', 'Combustion Man', 1], ['Actor Sokka', 'Appa', 1], ['Actor Sokka', 'Iroh', 1], ['Actor Sokka', 'Actor Zuko', 1], ['Actor Sokka', 'Momo', 1], ['Actor Sokka', 'Bumi', 1], ['Actor Sokka', 'Actor Bumi', 1], ['Actor Sokka', 'Flopsy', 1], ['Actor Sokka', 'Jet', 1], ['Actor Sokka', 'Actor Jet', 1], ['Actor Sokka', 'Yue', 1], ['Actor Sokka', 'Actress Yue', 1], ['Actor Sokka', 'Zhao', 1], ['Actor Sokka', 'Actor Toph', 1], ['Actor Sokka', 'Actress Azula', 1], ['Actor Sokka', 'Azula', 1], ['Actor Sokka', 'Mai', 1], ['Actor Sokka', 'Kuei', 1], ['Actor Sokka', 'Ty Lee', 1], ['Actor Sokka', 'Combustion Man', 1], ['Appa', 'Actor Zuko', 1], ['Appa', 'Actor Bumi', 1], ['Appa', 'Actor Jet', 1], ['Appa', 'Actress Yue', 1], ['Appa', 'Actor Toph', 2], ['Appa', 'Actress Azula', 1], ['Iroh', 'Actor Zuko', 1], ['Iroh', 'Actor Bumi', 1], ['Iroh', 'Actor Jet', 1], ['Iroh', 'Actress Yue', 1], ['Iroh', 'Actor Toph', 2], ['Iroh', 'Actress Azula', 1], ['Actor Zuko', 'Momo', 1], ['Actor Zuko', 'Bumi', 1], ['Actor Zuko', 'Actor Bumi', 1], ['Actor Zuko', 'Flopsy', 1], ['Actor Zuko', 'Jet', 1], ['Actor Zuko', 'Actor Jet', 1], ['Actor Zuko', 'Yue', 1], ['Actor Zuko', 'Actress Yue', 1], ['Actor Zuko', 'Zhao', 1], ['Actor Zuko', 'Actor Toph', 1], ['Actor Zuko', 'Actress Azula', 1], ['Actor Zuko', 'Azula', 1], ['Actor Zuko', 'Mai', 1], ['Actor Zuko', 'Kuei', 1], ['Actor Zuko', 'Ty Lee', 1], ['Actor Zuko', 'Combustion Man', 1], ['Momo', 'Actor Bumi', 1], ['Momo', 'Actor Jet', 1], ['Momo', 'Actress Yue', 1], ['Momo', 'Actor Toph', 2], ['Momo', 'Actress Azula', 1], ['Bumi', 'Actor Bumi', 1], ['Bumi', 'Jet', 1], ['Bumi', 'Actor Jet', 1], ['Bumi', 'Actress Yue', 1], ['Bumi', 'Zhao', 1], ['Bumi', 'Actor Toph', 1], ['Bumi', 'Actress Azula', 1], ['Bumi', 'Kuei', 1], ['Bumi', 'Combustion Man', 1], ['Actor Bumi', 'Flopsy', 1], ['Actor Bumi', 'Jet', 1], ['Actor Bumi', 'Actor Jet', 1], ['Actor Bumi', 'Yue', 1], ['Actor Bumi', 'Actress Yue', 1], ['Actor Bumi', 'Zhao', 1], ['Actor Bumi', 'Actor Toph', 1], ['Actor Bumi', 'Actress Azula', 1], ['Actor Bumi', 'Azula', 1], ['Actor Bumi', 'Mai', 1], ['Actor Bumi', 'Kuei', 1], ['Actor Bumi', 'Ty Lee', 1], ['Actor Bumi', 'Combustion Man', 1], ['Flopsy', 'Jet', 
1], ['Flopsy', 'Actor Jet', 1], ['Flopsy', 'Yue', 1], ['Flopsy', 'Actress Yue', 1], ['Flopsy', 'Zhao', 1], ['Flopsy', 'Actor Toph', 1], ['Flopsy', 'Actress Azula', 1], ['Flopsy', 'Kuei', 1], ['Flopsy', 'Combustion Man', 1], ['Jet', 'Actor Jet', 1], ['Jet', 'Yue', 1], ['Jet', 'Actress Yue', 1], ['Jet', 'Zhao', 1], ['Jet', 'Actor Toph', 1], ['Jet', 'Actress Azula', 1], ['Jet', 'Combustion Man', 1], ['Actor Jet', 'Yue', 1], ['Actor Jet', 'Actress Yue', 1], ['Actor Jet', 'Zhao', 1], ['Actor Jet', 'Actor Toph', 1], ['Actor Jet', 'Actress Azula', 1], ['Appa', 'Nyla', 1], ['Appa', 'Kuruk', 1], ['Appa', 'Yangchen', 1], ['Appa', 'Lion Turtle', 2], ['Nyla', 'Toph', 1], ['Nyla', 'Momo', 1], ['Nyla', 'Aang', 1], ['Nyla', 'Suki', 1], ['Nyla', 'Roku', 1], ['Nyla', 'Pakku', 1], ['Nyla', 'Bumi', 1], ['Nyla', 'Sozin', 1], ['Nyla', 'Ozai', 1], ['Nyla', 'Kanna', 1], ['Nyla', 'How', 1], ['Nyla', 'Jeong Jeong', 1], ['Nyla', 'Piandao', 1], ['Nyla', 'Iroh', 1], ['Nyla', 'Kyoshi', 1], ['Nyla', 'Chin', 1], ['Nyla', 'Kuruk', 1], ['Nyla', 'Yangchen', 1], ['Nyla', 'Azula', 1], ['Nyla', 'Lion Turtle', 1], ['Toph', 'Pakku', 2], ['Toph', 'Chin', 1], ['Toph', 'Kuruk', 1], ['Toph', 'Yangchen', 1], ['Toph', 'Lion Turtle', 2], ['Momo', 'Kuruk', 1], ['Momo', 'Yangchen', 1], ['Momo', 'Lion Turtle', 2], ['Aang', 'Kuruk', 1], ['Aang', 'Yangchen', 1], ['Aang', 'Lion Turtle', 2], ['Suki', 'Pakku', 2], ['Suki', 
'Sozin', 1], ['Suki', 'Kanna', 1], ['Suki', 'Jeong Jeong', 2], ['Suki', 'Piandao', 2], ['Suki', 'Kuruk', 1], ['Suki', 'Yangchen', 1], ['Suki', 'Lion Turtle', 2], ['Roku', 'Piandao', 1], ['Roku', 'Kuruk', 1], ['Roku', 'Yangchen', 1], ['Roku', 'Lion Turtle', 2], ['Pakku', 'Bumi', 2], ['Pakku', 'Sozin', 1], ['Pakku', 'Jeong Jeong', 2], ['Pakku', 'Piandao', 2], ['Pakku', 'Kyoshi', 1], ['Pakku', 'Chin', 1], ['Pakku', 'Kuruk', 1], ['Pakku', 'Yangchen', 1], ['Pakku', 'Lion Turtle', 1], ['Bumi', 'Sozin', 1], ['Bumi', 'Kanna', 1], ['Bumi', 'Jeong Jeong', 2], ['Bumi', 'Piandao', 2], ['Bumi', 'Kyoshi', 2], ['Bumi', 'Chin', 1], ['Bumi', 'Kuruk', 1], ['Bumi', 'Yangchen', 1], ['Bumi', 'Lion Turtle', 2], ['Sozin', 'Kanna', 1], ['Sozin', 'Jeong Jeong', 1], ['Sozin', 'Piandao', 1], ['Sozin', 'Kyoshi', 1], ['Sozin', 'Chin', 1], ['Sozin', 'Kuruk', 1], ['Sozin', 'Yangchen', 1], ['Sozin', 'Lion Turtle', 1], ['Ozai', 'Piandao', 2], ['Ozai', 'Chin', 1], ['Ozai', 'Kuruk', 1], ['Ozai', 'Yangchen', 1], ['Ozai', 'Lion Turtle', 2], ['Kanna', 'Jeong Jeong', 1], ['Kanna', 'Piandao', 1], ['Kanna', 'Kyoshi', 1], ['Kanna', 'Chin', 1], ['Kanna', 'Kuruk', 1], ['Kanna', 'Yangchen', 1], ['Kanna', 'Lion Turtle', 1], ['How', 'Kuruk', 1], ['How', 'Yangchen', 1], ['How', 'Lion Turtle', 2], ['Jeong Jeong', 'Piandao', 2], ['Jeong Jeong', 'Kyoshi', 1], ['Jeong Jeong', 'Chin', 1], ['Jeong Jeong', 'Kuruk', 1], ['Jeong Jeong', 'Yangchen', 1], 
['Jeong Jeong', 'Lion Turtle', 1], ['Piandao', 'Kyoshi', 1], ['Piandao', 'Chin', 1], ['Piandao', 'Kuruk', 1], ['Piandao', 'Yangchen', 1], ['Piandao', 'Azula', 2], ['Piandao', 'Lion Turtle', 1], ['Iroh', 'Kuruk', 1], ['Iroh', 'Yangchen', 1], ['Iroh', 'Lion Turtle', 2], ['Kyoshi', 'Kuruk', 1], ['Kyoshi', 'Yangchen', 1], ['Kyoshi', 'Lion Turtle', 2], ['Chin', 'Kuruk', 1], ['Chin', 'Yangchen', 1], ['Chin', 'Azula', 1], ['Chin', 'Lion Turtle', 1], ['Kuruk', 'Yangchen', 1], ['Kuruk', 'Azula', 1], ['Kuruk', 'Lion Turtle', 1], ['Yangchen', 'Azula', 1], ['Yangchen', 'Lion Turtle', 1], ['Azula', 'Lion Turtle', 2], ['Suki', 'Lo', 1], ['Suki', 'Ursa', 1], ['Li', 'Piandao', 1], ['Li', 'Bumi', 1], ['Li', 'Jeong Jeong', 1], ['Long Feng', 'Lo', 1], ['Long Feng', 'Piandao', 1], ['Long Feng', 'Bumi', 1], ['Long Feng', 'Pakku', 1], ['Long Feng', 'Jeong Jeong', 1], ['Long Feng', 'Ursa', 1], ['Lo', 'Piandao', 1], ['Lo', 'Bumi', 1], ['Lo', 'Pakku', 1], ['Lo', 'Iroh', 1], ['Lo', 'Jeong Jeong', 1], ['Mai', 'Piandao', 1], ['Mai', 'Pakku', 1], ['Mai', 'Jeong Jeong', 1], ['Ty Lee', 'Piandao', 1], ['Ty Lee', 'Pakku', 1], ['Ty Lee', 'Jeong Jeong', 1], ['Piandao', 'Ursa', 1], ['Bumi', 'Ursa', 1], ['Pakku', 'Ursa', 1], ['Jeong Jeong', 'Ursa', 1], ['Suki', 'Hippo', 1], ['Suki', 'The Boulder', 1], ['Suki', 'Bato', 1], ['Suki', 'Pipsqueak', 1], ['Suki', 'The Mechanist', 1], ['Roku', 'Hippo', 1], ['Roku', 'The Boulder', 1], ['Roku', 'Ty Lee', 1], ['Roku', 'Teo', 1], ['Roku', 'The Mechanist', 1], ['Bumi', 'The Duke', 1], ['Bumi', 'Haru', 1], ['Bumi', 'Hakoda', 1], ['Bumi', 'Bato', 1], ['Bumi', 'Pipsqueak', 1], ['Bumi', 'Teo', 1], ['Bumi', 'The Mechanist', 1], ['Lion Turtle', 'Mai', 1], ['Lion Turtle', 'The Duke', 1], ['Lion Turtle', 'Hippo', 1], ['Lion Turtle', 'The Boulder', 1], ['Lion Turtle', 'Haru', 1], ['Lion Turtle', 'Hakoda', 1], ['Lion Turtle', 'Bato', 1], ['Lion Turtle', 'Ty Lee', 1], ['Lion Turtle', 'Pipsqueak', 1], ['Lion Turtle', 'Teo', 1], ['Lion Turtle', 'The Mechanist', 1], 
['The Duke', 'Ty Lee', 1], ['Hippo', 'Ty Lee', 1], ['The Boulder', 'Ty Lee', 1], ['Haru', 'Ty Lee', 1], ['Ty Lee', 'Pipsqueak', 1], ['Ty Lee', 'Teo', 1], ['Ty Lee', 'The Mechanist', 1]]
# len(classic_edges_list) is 2383

# after 'how' fix
classic_edges_list = [['Sokka', 'Katara', 58], ['Aang', 'Katara', 58], ['Aang', 'Sokka', 58], ['Aang', 'Zuko', 47], ['Aang', 'Iroh', 43], ['Aang', 'Appa', 57], ['Aang', 'Kanna', 5], ['Katara', 'Zuko', 46], ['Katara', 'Iroh', 42], ['Katara', 'Appa', 56], ['Katara', 'Kanna', 5], ['Sokka', 'Zuko', 46], ['Sokka', 'Iroh', 42], ['Sokka', 'Appa', 56], ['Sokka', 'Kanna', 5], ['Zuko', 'Iroh', 43], ['Zuko', 'Appa', 45], ['Zuko', 'Kanna', 4], ['Iroh', 'Appa', 41], ['Iroh', 'Kanna', 4], ['Appa', 'Kanna', 5], ['Appa', 'Zhao', 10], ['Appa', 'Ozai', 27], ['Appa', 'Gyatso', 5], ['Appa', 'Roku', 14], ['Aang', 'Zhao', 10], ['Aang', 'Ozai', 27], ['Aang', 'Gyatso', 5], ['Aang', 'Roku', 14], ['Katara', 'Zhao', 10], ['Katara', 'Ozai', 27], ['Katara', 'Gyatso', 5], ['Katara', 'Roku', 14], ['Sokka', 'Zhao', 10], ['Sokka', 'Ozai', 27], ['Sokka', 'Gyatso', 5], ['Sokka', 'Roku', 14], ['Zuko', 'Zhao', 9], ['Zuko', 'Ozai', 22], ['Zuko', 'Gyatso', 5], ['Zuko', 'Roku', 12], ['Iroh', 'Zhao', 9], ['Iroh', 'Ozai', 20], ['Iroh', 'Gyatso', 5], ['Iroh', 'Roku', 11], ['Zhao', 'Ozai', 9], ['Zhao', 'Gyatso', 2], ['Zhao', 'Roku', 4], ['Ozai', 'Gyatso', 4], ['Ozai', 'Roku', 11], ['Gyatso', 'Roku', 3], ['Kyoshi', 'Zuko', 9], ['Kyoshi', 'Iroh', 9], ['Kyoshi', 'Aang', 9], ['Kyoshi', 'Sokka', 8], ['Kyoshi', 'Appa', 9], ['Kyoshi', 'Katara', 8], ['Kyoshi', 'Momo', 8], ['Kyoshi', 'Oyagi', 2], ['Kyoshi', 'Suki', 6], ['Kyoshi', 'Koko', 2], ['Zuko', 'Momo', 40], ['Zuko', 'Oyagi', 2], ['Zuko', 'Suki', 12], ['Zuko', 'Koko', 2], ['Iroh', 'Momo', 36], ['Iroh', 'Oyagi', 2], ['Iroh', 'Suki', 11], ['Iroh', 'Koko', 2], ['Aang', 'Momo', 52], ['Aang', 'Oyagi', 2], ['Aang', 'Suki', 12], ['Aang', 'Koko', 2], ['Sokka', 'Momo', 52], ['Sokka', 'Oyagi', 2], ['Sokka', 'Suki', 11], ['Sokka', 'Koko', 2], ['Appa', 'Momo', 51], ['Appa', 'Oyagi', 2], ['Appa', 'Suki', 11], ['Appa', 'Koko', 2], ['Katara', 'Momo', 52], ['Katara', 'Oyagi', 2], ['Katara', 'Suki', 11], ['Katara', 'Koko', 2], ['Momo', 'Oyagi', 2], ['Momo', 'Suki', 10], ['Momo', 'Koko', 2], ['Oyagi', 'Suki', 2], ['Oyagi', 'Koko', 2], ['Suki', 'Koko', 2], ['Sokka', 'Cabbage Merchant', 2], ['Sokka', 'Bumi', 10], ['Sokka', 'Flopsy', 3], ['Appa', 'Cabbage Merchant', 2], ['Appa', 'Bumi', 10], ['Appa', 'Flopsy', 3], ['Aang', 'Cabbage Merchant', 2], ['Aang', 'Bumi', 10], ['Aang', 'Flopsy', 3], ['Katara', 'Cabbage Merchant', 2], ['Katara', 'Bumi', 10], ['Katara', 'Flopsy', 3], ['Cabbage Merchant', 'Bumi', 2], ['Cabbage Merchant', 'Momo', 2], ['Cabbage Merchant', 'Flopsy', 1], ['Bumi', 'Momo', 10], ['Bumi', 'Flopsy', 3], ['Momo', 'Flopsy', 3], ['Aang', 'Haru', 8], ['Aang', 'Tyro', 3], ['Aang', 'Hope', 5], ['Katara', 'Haru', 8], ['Katara', 'Tyro', 3], ['Katara', 'Hope', 5], ['Sokka', 'Haru', 8], ['Sokka', 'Tyro', 3], ['Sokka', 'Hope', 5], ['Appa', 'Haru', 8], ['Appa', 'Tyro', 3], ['Appa', 'Hope', 5], ['Momo', 'Haru', 7], ['Momo', 'Ozai', 25], ['Momo', 'Tyro', 3], ['Momo', 'Hope', 5], ['Haru', 'Ozai', 5], ['Haru', 'Tyro', 3], ['Haru', 'Hope', 1], ['Ozai', 'Tyro', 3], ['Ozai', 'Hope', 2], ['Tyro', 'Hope', 1], ['Appa', 'Hei-Bai', 2], ['Aang', 'Hei-Bai', 2], ['Katara', 'Hei-Bai', 2], ['Sokka', 'Hei-Bai', 2], ['Gyatso', 'Momo', 3], ['Gyatso', 'Hei-Bai', 1], ['Roku', 'Momo', 11], ['Roku', 'Hei-Bai', 2], ['Zuko', 'Hei-Bai', 2], ['Iroh', 'Hei-Bai', 2], ['Momo', 'Hei-Bai', 2], ['Roku', 'Shyu', 1], ['Aang', 'Shyu', 1], ['Appa', 'Shyu', 1], ['Katara', 'Shyu', 1], ['Sokka', 'Shyu', 1], ['Momo', 'Zhao', 9], ['Momo', 'Shyu', 1], ['Zuko', 'Shyu', 1], ['Iroh', 'Shyu', 1], ['Ozai', 'Shyu', 1], ['Zhao', 'Shyu', 1], ['Roku', 'Bumi', 3], ['Roku', 'Cabbage Merchant', 1], ['Zuko', 'Bumi', 8], ['Zuko', 'Cabbage Merchant', 1], ['Iroh', 'Bumi', 8], ['Iroh', 'Cabbage Merchant', 1], ['Bumi', 'Ozai', 6], ['Cabbage Merchant', 'Ozai', 1], ['Jet', 'Momo', 7], ['Jet', 'Aang', 7], ['Jet', 'Katara', 7], ['Jet', 'Sokka', 7], ['Jet', 'Zuko', 7], ['Jet', 'Appa', 6], ['Jet', 'The Duke', 3], ['Jet', 'Pipsqueak', 2], ['Jet', 'Smellerbee', 5], ['Jet', 'Longshot', 5], ['Momo', 'The Duke', 9], ['Momo', 'Pipsqueak', 6], ['Momo', 'Smellerbee', 5], ['Momo', 'Longshot', 5], ['Aang', 'The Duke', 10], ['Aang', 'Pipsqueak', 6], ['Aang', 'Smellerbee', 5], ['Aang', 'Longshot', 5], ['Katara', 'The Duke', 10], ['Katara', 'Pipsqueak', 6], ['Katara', 'Smellerbee', 5], ['Katara', 'Longshot', 5], ['Sokka', 'The Duke', 10], ['Sokka', 'Pipsqueak', 6], ['Sokka', 'Smellerbee', 5], ['Sokka', 'Longshot', 5], ['Zuko', 'The Duke', 10], ['Zuko', 'Pipsqueak', 6], ['Zuko', 'Smellerbee', 5], ['Zuko', 'Longshot', 5], ['Appa', 'The Duke', 10], ['Appa', 'Pipsqueak', 6], ['Appa', 'Smellerbee', 4], ['Appa', 'Longshot', 4], ['The Duke', 'Pipsqueak', 6], ['The Duke', 'Smellerbee', 2], ['The Duke', 'Longshot', 2], ['Pipsqueak', 'Smellerbee', 2], ['Pipsqueak', 'Longshot', 2], ['Smellerbee', 'Longshot', 5], ['Sokka', 'Zhang Leader', 1], ['Sokka', 'Canyon Guide', 1], ['Sokka', 'Jin', 2], ['Sokka', 'Gan Jin Leader', 1], ['Sokka', 'Jin Wei', 1], ['Sokka', 'Wei Jin', 1], ['Katara', 'Zhang Leader', 1], ['Katara', 'Canyon Guide', 1], ['Katara', 'Jin', 2], ['Katara', 'Gan Jin Leader', 1], ['Katara', 'Jin Wei', 1], ['Katara', 'Wei Jin', 1], ['Aang', 'Zhang Leader', 1], ['Aang', 'Canyon Guide', 1], ['Aang', 'Jin', 2], ['Aang', 'Gan Jin Leader', 1], ['Aang', 'Jin Wei', 1], ['Aang', 'Wei Jin', 1], ['Appa', 'Zhang Leader', 1], ['Appa', 'Canyon Guide', 1], ['Appa', 'Jin', 2], ['Appa', 'Gan Jin Leader', 1], ['Appa', 'Jin Wei', 1], 
['Appa', 'Wei Jin', 1], ['Momo', 'Zhang Leader', 1], ['Momo', 'Canyon Guide', 1], ['Momo', 'Jin', 2], ['Momo', 'Gan Jin Leader', 1], ['Momo', 'Jin Wei', 1], ['Momo', 'Wei Jin', 1], ['Zhang Leader', 'Canyon Guide', 1], ['Zhang Leader', 'Jin', 1], ['Zhang Leader', 'Gan Jin Leader', 1], ['Zhang Leader', 'Hope', 1], ['Zhang Leader', 'Jin Wei', 1], ['Zhang Leader', 'Wei Jin', 1], ['Canyon Guide', 'Jin', 1], ['Canyon Guide', 'Gan Jin Leader', 1], ['Canyon Guide', 'Hope', 1], ['Canyon Guide', 'Jin Wei', 1], ['Canyon Guide', 'Wei Jin', 1], ['Jin', 'Gan Jin Leader', 1], 
['Jin', 'Hope', 2], ['Jin', 'Jin Wei', 1], ['Jin', 'Wei Jin', 1], ['Gan Jin Leader', 'Hope', 1], ['Gan Jin Leader', 'Jin Wei', 1], ['Gan Jin Leader', 'Wei Jin', 1], ['Hope', 'Jin Wei', 1], ['Hope', 'Wei Jin', 1], ['Jin Wei', 'Wei Jin', 1], ['Aang', 'Jee', 2], ['Sokka', 'Jee', 2], ['Katara', 'Jee', 2], ['Gyatso', 'Jee', 1], ['Appa', 'Jee', 2], ['Momo', 'Jee', 2], ['Iroh', 'Jee', 2], ['Zuko', 'Jee', 2], ['Jee', 'Ozai', 2], ['Jee', 'Zhao', 2], ['Zuko', 'Shinu', 2], ['Zuko', 'Herbalist', 2], ['Zuko', 'Miyuki', 1], ['Shinu', 'Zhao', 1], ['Shinu', 'Aang', 2], ['Shinu', 'Sokka', 2], ['Shinu', 'Katara', 2], ['Shinu', 'Momo', 2], ['Shinu', 'Appa', 2], ['Shinu', 'Jee', 1], ['Shinu', 'Iroh', 2], ['Shinu', 'Ozai', 2], ['Shinu', 'Herbalist', 1], ['Shinu', 'Miyuki', 1], ['Zhao', 'Herbalist', 1], ['Zhao', 'Miyuki', 1], ['Aang', 'Herbalist', 2], ['Aang', 'Miyuki', 1], ['Sokka', 'Herbalist', 2], ['Sokka', 'Miyuki', 1], ['Katara', 'Herbalist', 2], ['Katara', 'Miyuki', 1], ['Momo', 'Herbalist', 2], ['Momo', 'Miyuki', 1], ['Appa', 'Herbalist', 2], ['Appa', 'Miyuki', 1], ['Jee', 'Herbalist', 1], ['Jee', 'Miyuki', 1], ['Iroh', 'Herbalist', 
2], ['Iroh', 'Miyuki', 1], ['Ozai', 'Herbalist', 1], ['Ozai', 'Miyuki', 1], ['Herbalist', 'Miyuki', 1], ['Katara', 'Wu', 2], ['Katara', 'Meng', 1], ['Momo', 'Wu', 2], ['Momo', 'Meng', 1], ['Sokka', 'Wu', 2], ['Sokka', 'Meng', 1], ['Aang', 'Wu', 2], ['Aang', 'Meng', 1], ['Appa', 'Wu', 2], ['Appa', 'Meng', 1], ['Wu', 'Meng', 1], ['Bato', 'Aang', 6], ['Bato', 'Sokka', 6], ['Bato', 'Katara', 6], ['Bato', 'Zuko', 6], ['Bato', 'Iroh', 5], ['Bato', 'June', 1], ['Bato', 'Appa', 6], ['Bato', 'Hakoda', 6], ['Bato', 'Momo', 6], ['Bato', 'Herbalist', 1], ['Bato', 'Wu', 1], 
['Aang', 'June', 3], ['Aang', 'Hakoda', 10], ['Sokka', 'June', 3], ['Sokka', 'Hakoda', 9], ['Katara', 'June', 3], ['Katara', 'Hakoda', 9], ['Zuko', 'June', 3], ['Zuko', 'Hakoda', 10], ['Zuko', 'Wu', 1], ['Iroh', 'June', 3], ['Iroh', 'Hakoda', 8], ['Iroh', 'Wu', 1], ['June', 'Appa', 3], ['June', 'Hakoda', 1], ['June', 'Momo', 3], ['June', 'Herbalist', 1], ['June', 'Wu', 1], ['Appa', 'Hakoda', 9], ['Hakoda', 'Momo', 8], ['Hakoda', 'Herbalist', 1], ['Hakoda', 'Wu', 1], ['Herbalist', 'Wu', 1], ['Jeong Jeong', 'Momo', 4], ['Jeong Jeong', 'Appa', 4], ['Jeong Jeong', 'Katara', 4], ['Jeong Jeong', 'Sokka', 4], ['Jeong Jeong', 'Aang', 4], ['Jeong Jeong', 'Ozai', 4], ['Jeong Jeong', 'Chey', 1], ['Jeong Jeong', 'Zhao', 2], ['Jeong Jeong', 'Roku', 2], ['Momo', 'Chey', 1], ['Appa', 'Chey', 1], ['Katara', 'Chey', 1], ['Sokka', 'Chey', 1], ['Aang', 'Chey', 1], ['Ozai', 'Chey', 1], ['Chey', 'Zhao', 1], ['Chey', 'Roku', 1], ['Katara', 'Teo', 7], ['Katara', 'The Mechanist', 4], ['Sokka', 'Teo', 7], ['Sokka', 'The Mechanist', 4], ['Aang', 'Teo', 7], ['Aang', 'The Mechanist', 4], ['Momo', 'Teo', 7], ['Momo', 'The Mechanist', 4], ['Appa', 
'Teo', 7], ['Appa', 'The Mechanist', 4], ['Teo', 'The Mechanist', 4], ['Appa', 'Li', 10], ['Appa', 'Arnook', 3], ['Appa', 'Yue', 7], ['Appa', 'Pakku', 6], ['Appa', 'Yugoda', 1], ['Sokka', 'Li', 10], ['Sokka', 'Arnook', 3], ['Sokka', 'Yue', 7], ['Sokka', 'Pakku', 6], ['Sokka', 'Yugoda', 1], ['Aang', 'Li', 11], ['Aang', 'Arnook', 3], ['Aang', 'Yue', 7], ['Aang', 'Pakku', 6], ['Aang', 'Yugoda', 1], ['Katara', 'Li', 10], ['Katara', 'Arnook', 3], ['Katara', 'Yue', 7], ['Katara', 'Pakku', 6], ['Katara', 'Yugoda', 1], ['Zhao', 'Li', 1], ['Zhao', 'Arnook', 3], ['Zhao', 
'Yue', 4], ['Zhao', 'Pakku', 3], ['Zhao', 'Yugoda', 1], ['Li', 'Iroh', 9], ['Li', 'Arnook', 1], ['Li', 'Yue', 2], ['Li', 'Pakku', 2], ['Li', 'Zuko', 11], ['Li', 'Yugoda', 1], ['Li', 'Momo', 10], ['Li', 'Ozai', 5], ['Iroh', 'Arnook', 3], ['Iroh', 'Yue', 6], ['Iroh', 'Pakku', 6], ['Iroh', 'Yugoda', 1], ['Arnook', 'Yue', 3], ['Arnook', 'Pakku', 3], ['Arnook', 'Zuko', 3], ['Arnook', 'Yugoda', 1], ['Arnook', 'Momo', 3], ['Arnook', 'Ozai', 2], ['Yue', 'Pakku', 3], ['Yue', 'Zuko', 7], ['Yue', 'Yugoda', 1], ['Yue', 'Momo', 7], ['Yue', 'Ozai', 4], ['Pakku', 'Zuko', 6], ['Pakku', 'Yugoda', 1], ['Pakku', 'Momo', 6], ['Pakku', 'Ozai', 5], ['Zuko', 'Yugoda', 1], ['Yugoda', 'Momo', 1], ['Yugoda', 'Ozai', 1], ['Katara', 'Sangok', 1], ['Katara', 'Hahn', 2], ['Pakku', 'Sangok', 1], ['Pakku', 'Hahn', 2], ['Sangok', 'Aang', 1], ['Sangok', 'Momo', 1], ['Sangok', 'Yue', 1], ['Sangok', 'Sokka', 1], ['Sangok', 'Iroh', 1], ['Sangok', 'Appa', 1], ['Sangok', 'Zhao', 1], ['Sangok', 'Zuko', 1], ['Sangok', 'Arnook', 1], ['Sangok', 'Hahn', 1], ['Aang', 'Hahn', 2], ['Momo', 'Hahn', 2], ['Yue', 'Hahn', 2], ['Sokka', 'Hahn', 2], ['Iroh', 'Hahn', 2], ['Appa', 'Hahn', 2], ['Zhao', 'Hahn', 2], ['Zuko', 'Hahn', 2], ['Arnook', 'Hahn', 2], ['Appa', 'Shu', 1], ['Appa', 'Koh', 1], ['Katara', 'Shu', 1], ['Katara', 'Koh', 1], ['Momo', 'Shu', 1], ['Momo', 'Koh', 1], ['Sokka', 'Shu', 1], ['Sokka', 'Koh', 1], ['Yue', 'Roku', 2], ['Yue', 'Shu', 1], ['Yue', 'Koh', 1], ['Yue', 'Hei-Bai', 1], ['Zuko', 'Shu', 1], ['Zuko', 'Koh', 1], ['Aang', 'Shu', 1], ['Aang', 'Koh', 1], ['Roku', 'Hahn', 1], ['Roku', 'Shu', 1], ['Roku', 'Koh', 1], ['Roku', 'Pakku', 3], ['Roku', 'Arnook', 1], ['Iroh', 'Shu', 1], ['Iroh', 'Koh', 1], ['Zhao', 'Shu', 1], ['Zhao', 'Koh', 1], ['Zhao', 'Hei-Bai', 1], ['Hahn', 'Shu', 1], ['Hahn', 'Koh', 1], ['Hahn', 'Hei-Bai', 1], ['Hahn', 'Ozai', 1], ['Shu', 'Koh', 1], ['Shu', 'Hei-Bai', 1], ['Shu', 'Pakku', 1], ['Shu', 'Arnook', 1], ['Shu', 'Ozai', 1], ['Koh', 'Hei-Bai', 1], ['Koh', 'Pakku', 
1], ['Koh', 'Arnook', 1], ['Koh', 'Ozai', 1], ['Hei-Bai', 'Pakku', 1], ['Hei-Bai', 'Arnook', 1], ['Hei-Bai', 'Ozai', 1], ['Aang', 'Fong', 4], ['Aang', 'Azula', 23], ['Sokka', 'Fong', 4], ['Sokka', 'Azula', 22], ['Katara', 'Fong', 4], ['Katara', 'Azula', 22], ['Pakku', 'Fong', 1], ['Pakku', 'Kanna', 2], ['Pakku', 'Azula', 3], ['Appa', 'Fong', 3], ['Appa', 'Azula', 22], ['Fong', 'Kanna', 1], ['Fong', 'Iroh', 3], ['Fong', 'Zuko', 3], ['Fong', 'Ozai', 2], ['Fong', 'Azula', 1], ['Fong', 'Momo', 4], ['Fong', 'Roku', 1], ['Kanna', 'Ozai', 2], ['Kanna', 'Azula', 2], ['Kanna', 'Momo', 3], ['Kanna', 'Roku', 2], ['Iroh', 'Azula', 20], ['Zuko', 'Azula', 24], ['Ozai', 'Azula', 14], ['Azula', 'Momo', 20], ['Azula', 'Roku', 5], ['Aang', 'Chong', 1], ['Aang', 'Moku', 1], ['Aang', 'Song', 1], ['Aang', 'Oma', 1], ['Katara', 'Chong', 1], ['Katara', 'Moku', 1], ['Katara', 'Song', 1], ['Katara', 'Oma', 1], ['Sokka', 'Chong', 1], ['Sokka', 'Moku', 1], ['Sokka', 'Song', 1], ['Sokka', 'Oma', 1], ['Momo', 'Chong', 1], ['Momo', 'Moku', 1], ['Momo', 'Song', 1], ['Momo', 'Oma', 1], ['Chong', 'Iroh', 1], ['Chong', 'Appa', 1], ['Chong', 'Bumi', 1], ['Chong', 'Zuko', 1], ['Chong', 'Moku', 1], ['Chong', 'Song', 1], ['Chong', 'Oma', 1], ['Iroh', 'Moku', 1], ['Iroh', 'Song', 1], ['Iroh', 'Oma', 1], ['Appa', 'Moku', 1], ['Appa', 'Song', 1], ['Appa', 'Oma', 1], ['Bumi', 'Moku', 1], ['Bumi', 'Song', 1], ['Bumi', 'Oma', 1], ['Zuko', 'Moku', 1], ['Zuko', 'Song', 1], ['Zuko', 'Oma', 1], ['Moku', 'Song', 1], ['Moku', 'Oma', 1], ['Song', 'Oma', 1], ['Aang', 'Mai', 15], ['Aang', 'Ty Lee', 13], ['Aang', 'Circus Master', 1], ['Aang', 'Governor', 1], ['Momo', 'Mai', 13], ['Momo', 'Ty Lee', 11], ['Momo', 'Circus Master', 
1], ['Momo', 'Governor', 1], ['Appa', 'Mai', 14], ['Appa', 'Ty Lee', 12], ['Appa', 'Circus Master', 1], ['Appa', 'Governor', 1], ['Sokka', 'Mai', 14], ['Sokka', 'Ty Lee', 12], ['Sokka', 'Circus Master', 1], ['Sokka', 'Governor', 1], ['Katara', 'Mai', 14], ['Katara', 'Ty Lee', 12], ['Katara', 'Circus Master', 1], ['Katara', 'Governor', 1], ['Azula', 'Bumi', 5], ['Azula', 'Mai', 15], ['Azula', 'Ty Lee', 13], ['Azula', 'Flopsy', 2], ['Azula', 'Circus Master', 1], ['Azula', 'Governor', 1], ['Bumi', 'Mai', 4], ['Bumi', 'Ty Lee', 4], ['Bumi', 'Circus Master', 1], ['Bumi', 'Governor', 1], ['Mai', 'Ty Lee', 13], ['Mai', 'Zuko', 16], ['Mai', 'Flopsy', 2], ['Mai', 'Circus Master', 1], ['Mai', 'Governor', 1], ['Mai', 'Iroh', 13], ['Ty Lee', 'Zuko', 14], ['Ty Lee', 'Flopsy', 2], ['Ty Lee', 'Circus Master', 1], ['Ty Lee', 'Governor', 1], ['Ty Lee', 'Iroh', 13], ['Zuko', 'Flopsy', 2], ['Zuko', 'Circus Master', 1], ['Zuko', 'Governor', 1], ['Flopsy', 'Circus Master', 1], ['Flopsy', 'Governor', 1], ['Flopsy', 'Iroh', 2], ['Circus Master', 'Governor', 1], ['Circus Master', 'Iroh', 1], ['Governor', 'Iroh', 1], ['Iroh', 'Due', 3], ['Iroh', 'Tho', 3], ['Iroh', 'Hue', 3], ['Zuko', 'Due', 3], ['Zuko', 'Tho', 3], ['Zuko', 'Hue', 3], ['Appa', 'Due', 3], ['Appa', 'Tho', 3], ['Appa', 'Hue', 3], ['Momo', 'Due', 3], ['Momo', 'Tho', 3], ['Momo', 'Hue', 3], ['Katara', 'Due', 3], ['Katara', 'Tho', 3], ['Katara', 'Hue', 3], ['Sokka', 'Due', 3], ['Sokka', 'Tho', 3], ['Sokka', 'Hue', 3], ['Aang', 'Due', 3], ['Aang', 'Tho', 3], ['Aang', 'Hue', 3], ['Bumi', 'Due', 1], ['Bumi', 'Tho', 1], ['Bumi', 'Yue', 2], ['Bumi', 'Hue', 1], ['Due', 'Tho', 3], ['Due', 'Yue', 1], ['Due', 'Hue', 3], ['Tho', 'Yue', 1], ['Tho', 'Hue', 3], ['Yue', 'Hue', 1], ['Katara', 'Mongke', 2], ['Katara', 'Tong', 2], ['Katara', 'Chin', 2], ['Sokka', 'Mongke', 2], ['Sokka', 'Tong', 2], ['Sokka', 'Chin', 2], ['Momo', 'Mongke', 2], ['Momo', 'Tong', 2], ['Momo', 'Chin', 2], ['Aang', 'Mongke', 2], ['Aang', 'Tong', 2], ['Aang', 'Chin', 2], ['Mongke', 'Appa', 2], ['Mongke', 'Kyoshi', 1], ['Mongke', 'Roku', 1], ['Mongke', 'Zuko', 2], ['Mongke', 'Iroh', 2], ['Mongke', 'Tong', 1], ['Mongke', 'Chin', 1], ['Mongke', 'Oyagi', 1], ['Mongke', 'Koko', 1], ['Mongke', 'Suki', 1], ['Appa', 'Tong', 2], ['Appa', 'Chin', 2], ['Kyoshi', 'Roku', 3], ['Kyoshi', 'Tong', 1], ['Kyoshi', 'Chin', 2], ['Roku', 'Tong', 2], ['Roku', 'Chin', 2], ['Roku', 'Oyagi', 1], ['Roku', 'Koko', 1], ['Roku', 'Suki', 3], ['Zuko', 'Tong', 1], ['Zuko', 'Chin', 2], ['Iroh', 'Tong', 1], ['Iroh', 'Chin', 2], ['Tong', 'Chin', 1], ['Tong', 'Oyagi', 1], ['Tong', 'Koko', 1], ['Tong', 'Suki', 1], ['Chin', 'Oyagi', 1], ['Chin', 'Koko', 1], ['Chin', 'Suki', 2], ['Toph', 'Sokka', 33], ['Toph', 'Momo', 30], ['Toph', 'Aang', 34], ['Toph', 'Katara', 33], ['Toph', 'Yu', 4], ['Toph', 'The Boulder', 4], ['Toph', 'Xin Fu', 3], ['Toph', 'Hippo', 4], ['Toph', 'Bumi', 5], ['Toph', 'Fong', 3], ['Toph', 'Lao', 1], ['Toph', 'Ozai', 17], ['Toph', 'Appa', 32], ['Sokka', 'Yu', 4], ['Sokka', 'The Boulder', 4], ['Sokka', 'Xin Fu', 3], ['Sokka', 'Hippo', 4], ['Sokka', 'Lao', 1], ['Momo', 'Yu', 4], ['Momo', 'The Boulder', 4], ['Momo', 'Xin Fu', 3], ['Momo', 'Hippo', 4], ['Momo', 'Lao', 1], ['Aang', 'Yu', 4], ['Aang', 'The Boulder', 4], ['Aang', 'Xin Fu', 3], ['Aang', 'Hippo', 4], ['Aang', 'Lao', 1], ['Katara', 'Yu', 4], ['Katara', 'The Boulder', 4], ['Katara', 'Xin Fu', 3], ['Katara', 'Hippo', 4], ['Katara', 'Lao', 1], ['Yu', 'The Boulder', 1], ['Yu', 'Xin Fu', 3], ['Yu', 'Hippo', 1], ['Yu', 'Bumi', 1], ['Yu', 'Fong', 1], ['Yu', 'Lao', 1], ['Yu', 'Ozai', 2], ['Yu', 'Appa', 4], ['The Boulder', 'Xin Fu', 1], ['The Boulder', 'Hippo', 4], ['The Boulder', 'Bumi', 2], ['The Boulder', 'Fong', 1], ['The Boulder', 'Lao', 1], ['The Boulder', 'Ozai', 4], ['The Boulder', 'Appa', 4], ['Xin Fu', 'Hippo', 1], ['Xin Fu', 'Bumi', 1], ['Xin Fu', 'Fong', 1], ['Xin Fu', 'Lao', 1], ['Xin Fu', 'Ozai', 2], ['Xin Fu', 'Appa', 3], ['Hippo', 'Bumi', 2], ['Hippo', 'Fong', 1], ['Hippo', 'Lao', 1], ['Hippo', 'Ozai', 4], ['Hippo', 'Appa', 4], ['Bumi', 'Fong', 1], ['Bumi', 'Lao', 1], ['Fong', 'Lao', 1], ['Lao', 'Ozai', 1], ['Lao', 'Appa', 1], ['Zuko', 'Gow', 1], ['Zuko', 'Gansu', 1], ['Zuko', 'Sela', 1], ['Zuko', 'Ursa', 3], ['Zuko', 'Azulon', 2], ['Zuko', 
'Lu Ten', 2], ['Zuko', 'Sozin', 5], ['Gow', 'Gansu', 1], ['Gow', 'Sela', 1], ['Gow', 'Azula', 1], ['Gow', 'Ursa', 1], ['Gow', 'Ty Lee', 1], ['Gow', 'Mai', 1], ['Gow', 'Iroh', 1], ['Gow', 'Azulon', 1], ['Gow', 'Lu Ten', 1], ['Gow', 'Ozai', 1], ['Gow', 'Sozin', 1], ['Gansu', 'Sela', 1], ['Gansu', 'Azula', 1], ['Gansu', 'Ursa', 1], ['Gansu', 'Ty Lee', 1], ['Gansu', 'Mai', 1], ['Gansu', 'Iroh', 1], ['Gansu', 'Azulon', 1], ['Gansu', 'Lu Ten', 1], ['Gansu', 'Ozai', 1], ['Gansu', 'Sozin', 1], ['Sela', 'Azula', 1], ['Sela', 'Ursa', 1], ['Sela', 'Ty Lee', 1], ['Sela', 'Mai', 1], ['Sela', 'Iroh', 1], ['Sela', 'Azulon', 1], ['Sela', 'Lu Ten', 1], ['Sela', 'Ozai', 1], ['Sela', 'Sozin', 1], ['Azula', 'Ursa', 3], ['Azula', 'Azulon', 2], ['Azula', 'Lu Ten', 2], ['Azula', 'Sozin', 3], ['Ursa', 'Ty Lee', 3], ['Ursa', 'Mai', 3], ['Ursa', 'Iroh', 2], ['Ursa', 'Azulon', 1], ['Ursa', 'Lu Ten', 1], ['Ursa', 'Ozai', 2], ['Ursa', 'Sozin', 1], ['Ty Lee', 'Azulon', 1], ['Ty Lee', 'Lu Ten', 1], ['Ty Lee', 'Ozai', 6], ['Ty Lee', 'Sozin', 2], ['Mai', 'Azulon', 2], ['Mai', 'Lu Ten', 1], ['Mai', 'Ozai', 9], ['Mai', 'Sozin', 2], ['Iroh', 'Azulon', 2], ['Iroh', 'Lu Ten', 2], ['Iroh', 'Sozin', 5], ['Azulon', 'Lu Ten', 1], ['Azulon', 'Ozai', 2], ['Azulon', 'Sozin', 1], ['Lu Ten', 'Ozai', 1], ['Lu Ten', 'Sozin', 1], ['Ozai', 'Sozin', 4], ['Toph', 'Ty Lee', 12], ['Toph', 'Zuko', 28], ['Toph', 'Mai', 14], ['Toph', 'Azula', 21], ['Toph', 'Iroh', 25], ['Appa', 'Lu Ten', 1], ['Aang', 'Lu Ten', 1], ['Toph', 'Lu Ten', 1], ['Katara', 'Lu Ten', 1], ['Sokka', 'Lu Ten', 1], ['Lu Ten', 'Momo', 1], ['Roku', 'Toph', 6], ['Roku', 'Zei', 1], ['Roku', 'Wan Shi Tong', 1], ['Roku', 'Kuei', 2], ['Aang', 'Zei', 1], ['Aang', 'Wan Shi Tong', 1], ['Aang', 'Kuei', 10], ['Katara', 'Zei', 1], ['Katara', 'Wan Shi Tong', 1], ['Katara', 'Kuei', 10], ['Momo', 'Zei', 1], ['Momo', 'Wan Shi Tong', 1], ['Momo', 'Kuei', 10], ['Sokka', 'Zei', 1], ['Sokka', 'Wan Shi Tong', 1], ['Sokka', 'Kuei', 10], ['Toph', 'Zei', 1], ['Toph', 'Wan Shi Tong', 1], ['Toph', 'Tong', 1], ['Toph', 'Kuei', 10], ['Appa', 'Zei', 1], ['Appa', 'Wan Shi Tong', 1], ['Appa', 'Kuei', 9], ['Zei', 'Wan Shi Tong', 1], ['Zei', 'Tong', 1], ['Zei', 'Kuei', 1], ['Zei', 'Ozai', 1], ['Wan Shi Tong', 'Tong', 1], ['Wan Shi Tong', 'Kuei', 1], ['Wan Shi Tong', 'Ozai', 1], ['Tong', 'Kuei', 1], ['Tong', 'Ozai', 1], ['Kuei', 'Ozai', 5], ['Toph', 'Mongke', 1], ['Toph', 'Yue', 3], ['Zuko', 'Xin Fu', 2], ['Zuko', 'Yu', 3], ['Iroh', 'Xin Fu', 2], ['Iroh', 'Yu', 3], ['Mongke', 'Xin Fu', 1], ['Mongke', 'Yu', 1], ['Mongke', 'Yue', 1], 
['Xin Fu', 'Yue', 1], ['Yu', 'Yue', 1], ['Aang', 'Than', 3], ['Aang', 'Ying', 2], ['Sokka', 'Than', 3], ['Sokka', 'Ying', 2], ['Momo', 'Than', 3], ['Momo', 'Ying', 2], ['Toph', 'Suki', 10], ['Toph', 'Kyoshi', 7], ['Toph', 'Than', 3], ['Toph', 'Ying', 2], ['Toph', 'Hope', 3], ['Toph', 'Jet', 6], ['Toph', 'Smellerbee', 4], ['Toph', 'Longshot', 4], ['Katara', 'Than', 3], ['Katara', 'Ying', 2], ['Appa', 'Than', 3], ['Appa', 'Ying', 2], ['Kuei', 'Fong', 2], ['Kuei', 'Suki', 3], ['Kuei', 'Kyoshi', 3], ['Kuei', 'Than', 2], ['Kuei', 'Ying', 2], ['Kuei', 'Hope', 2], ['Kuei', 'Zuko', 9], ['Kuei', 'Jet', 4], ['Kuei', 'Smellerbee', 3], ['Kuei', 'Longshot', 3], ['Kuei', 'Iroh', 8], ['Fong', 'Suki', 1], ['Fong', 'Kyoshi', 1], ['Fong', 'Than', 1], ['Fong', 'Ying', 1], ['Fong', 'Hope', 1], ['Fong', 'Jet', 2], ['Fong', 'Smellerbee', 2], ['Fong', 'Longshot', 2], ['Suki', 'Than', 1], ['Suki', 'Ying', 1], ['Suki', 'Hope', 1], ['Suki', 'Jet', 3], ['Suki', 'Smellerbee', 1], ['Suki', 'Longshot', 1], ['Kyoshi', 'Than', 1], ['Kyoshi', 'Ying', 1], ['Kyoshi', 'Hope', 1], ['Kyoshi', 'Jet', 1], ['Kyoshi', 'Smellerbee', 1], ['Kyoshi', 'Longshot', 1], ['Than', 'Ying', 2], ['Than', 'Hope', 3], ['Than', 'Zuko', 3], ['Than', 'Jet', 2], ['Than', 'Smellerbee', 2], ['Than', 'Longshot', 2], ['Than', 'Iroh', 2], ['Ying', 'Hope', 2], ['Ying', 'Zuko', 2], ['Ying', 'Jet', 1], ['Ying', 'Smellerbee', 1], ['Ying', 'Longshot', 1], ['Ying', 'Iroh', 1], ['Hope', 'Zuko', 3], ['Hope', 'Jet', 2], ['Hope', 'Smellerbee', 2], ['Hope', 'Longshot', 2], ['Hope', 'Iroh', 2], ['Jet', 'Iroh', 5], ['Smellerbee', 'Iroh', 4], ['Longshot', 'Iroh', 4], ['Azula', 'Than', 2], ['Azula', 'Smellerbee', 1], ['Azula', 'Longshot', 1], ['Azula', 'Sung', 2], ['Azula', 'Jet', 3], ['Azula', 'Qin', 2], ['Azula', 'Hope', 2], ['Mai', 'Than', 2], ['Mai', 'Smellerbee', 1], ['Mai', 'Longshot', 1], ['Mai', 'Sung', 2], ['Mai', 'Jet', 2], ['Mai', 'Qin', 1], ['Mai', 'Hope', 2], ['Sokka', 'Sung', 2], ['Sokka', 'Qin', 2], ['Toph', 'Sung', 2], ['Toph', 'Qin', 2], ['Than', 'Ty Lee', 1], ['Than', 'Sung', 1], ['Than', 'Qin', 1], ['Aang', 'Sung', 2], ['Aang', 'Qin', 2], ['Momo', 'Sung', 2], ['Momo', 'Qin', 2], ['Appa', 'Sung', 2], ['Appa', 'Qin', 2], ['Ty Lee', 'Smellerbee', 1], ['Ty Lee', 'Longshot', 1], ['Ty Lee', 'Sung', 
2], ['Ty Lee', 'Jet', 2], ['Ty Lee', 'Qin', 1], ['Ty Lee', 'Hope', 1], ['Zuko', 'Sung', 2], ['Zuko', 'Qin', 2], ['Iroh', 'Sung', 2], ['Iroh', 'Qin', 2], ['Smellerbee', 'Sung', 1], ['Smellerbee', 'Qin', 1], ['Longshot', 'Sung', 1], ['Longshot', 'Qin', 1], ['Katara', 'Sung', 2], ['Katara', 'Qin', 2], ['Sung', 'Jet', 1], ['Sung', 'Qin', 1], ['Sung', 'Hope', 1], ['Jet', 'Qin', 1], ['Qin', 'Hope', 1], ['Toph', 'Joo Dee', 2], ['Toph', 'Long Feng', 7], ['Toph', 'Li', 10], ['Momo', 'Joo Dee', 2], ['Momo', 'Long Feng', 6], ['Katara', 'Joo Dee', 2], ['Katara', 'Long Feng', 6], ['Aang', 'Joo Dee', 2], ['Aang', 'Long Feng', 7], ['Kuei', 'Joo Dee', 2], ['Kuei', 'Long Feng', 5], ['Kuei', 'Li', 6], ['Zuko', 'Joo Dee', 2], ['Zuko', 'Long Feng', 7], ['Iroh', 'Joo Dee', 2], ['Iroh', 'Long Feng', 7], ['Jet', 'Joo Dee', 2], ['Jet', 'Long Feng', 2], ['Jet', 'Li', 2], ['Longshot', 'Joo Dee', 2], ['Longshot', 'Long Feng', 2], ['Longshot', 'Li', 2], ['Joo Dee', 'Sokka', 2], ['Joo Dee', 'Smellerbee', 2], ['Joo Dee', 'Fong', 1], ['Joo Dee', 'Long Feng', 2], ['Joo Dee', 'Li', 2], ['Sokka', 'Long Feng', 6], ['Smellerbee', 'Long Feng', 2], ['Smellerbee', 'Li', 2], ['Fong', 'Long Feng', 1], ['Fong', 'Li', 1], ['Long Feng', 'Li', 7], ['Toph', 'Hakoda', 9], ['Toph', 'Guru', 4], ['Appa', 'Guru', 4], ['Appa', 'Long Feng', 6], ['Aang', 'Guru', 4], ['Iroh', 'Guru', 3], ['Zuko', 'Guru', 4], ['Kyoshi', 'Mai', 4], ['Kyoshi', 'Ty Lee', 
4], ['Kyoshi', 'Azula', 6], ['Kyoshi', 'Hakoda', 4], ['Kyoshi', 'Guru', 2], ['Kyoshi', 'Li', 3], ['Kyoshi', 'Long Feng', 3], ['Suki', 'Mai', 5], ['Suki', 'Ty Lee', 5], ['Suki', 'Azula', 8], ['Suki', 'Hakoda', 5], ['Suki', 'Guru', 1], ['Suki', 'Li', 2], ['Suki', 'Long Feng', 2], ['Mai', 'Hakoda', 6], ['Mai', 'Guru', 4], ['Mai', 'Li', 6], ['Mai', 'Long Feng', 4], ['Ty Lee', 'Hakoda', 4], ['Ty Lee', 'Guru', 3], ['Ty Lee', 'Li', 6], ['Ty Lee', 'Long Feng', 5], ['Azula', 'Hakoda', 8], ['Azula', 'Guru', 4], ['Azula', 'Li', 8], ['Azula', 'Long Feng', 5], ['Hakoda', 'Guru', 2], ['Hakoda', 'Li', 4], ['Hakoda', 'Long Feng', 2], ['Guru', 'Li', 3], ['Guru', 'Long Feng', 3], ['Appa', 'Pao', 2], ['Appa', 'Quon', 1], ['Appa', 'Joo Dee', 1], ['Sokka', 'Pao', 2], ['Sokka', 'Quon', 1], ['Toph', 'Pao', 2], ['Toph', 'Quon', 1], ['Toph', 'The Duke', 9], ['Toph', 'Pipsqueak', 5], ['Momo', 'Pao', 2], ['Momo', 'Quon', 1], ['Katara', 'Pao', 2], ['Katara', 'Quon', 1], ['Aang', 'Pao', 2], ['Aang', 'Quon', 1], ['Iroh', 'Pao', 1], ['Iroh', 'Quon', 1], ['Iroh', 'The Duke', 7], ['Iroh', 'Pipsqueak', 4], ['Zuko', 'Pao', 2], ['Zuko', 'Quon', 1], ['Pao', 'Quon', 1], ['Pao', 'Li', 2], ['Pao', 'Joo Dee', 1], ['Pao', 'Kuei', 2], ['Pao', 'Jet', 1], ['Pao', 'Smellerbee', 1], ['Pao', 'Longshot', 1], ['Pao', 'Long Feng', 1], ['Pao', 'The Duke', 2], ['Pao', 'Pipsqueak', 2], ['Quon', 'Li', 1], ['Quon', 'Joo Dee', 1], ['Quon', 'Kuei', 1], ['Quon', 'Jet', 1], ['Quon', 'Smellerbee', 1], ['Quon', 'Longshot', 1], ['Quon', 'Long Feng', 1], ['Quon', 'The Duke', 1], ['Quon', 'Pipsqueak', 1], ['Li', 'The Duke', 3], ['Li', 'Pipsqueak', 3], ['Joo Dee', 'The Duke', 1], ['Joo Dee', 'Pipsqueak', 1], ['Kuei', 'The Duke', 2], ['Kuei', 'Pipsqueak', 2], ['Long Feng', 'The Duke', 1], ['Long Feng', 'Pipsqueak', 1], ['Kuei', 'Bosco', 4], ['Kuei', 'Yu', 2], ['Kuei', 'Azula', 6], ['Kuei', 'Ty Lee', 4], ['Appa', 'Bosco', 4], ['Momo', 'Bosco', 4], ['Aang', 'Bosco', 4], ['Sokka', 'Bosco', 4], ['Katara', 'Bosco', 4], ['Long Feng', 'Bosco', 3], ['Long Feng', 'Yu', 2], ['Li', 'Bosco', 3], ['Li', 'Yu', 2], ['Toph', 'Bosco', 4], ['Zuko', 'Bosco', 4], ['Iroh', 'Bosco', 4], ['Bosco', 'Kyoshi', 2], ['Bosco', 'Yu', 2], ['Bosco', 'Azula', 4], ['Bosco', 'Ty Lee', 3], ['Kyoshi', 'Yu', 2], ['Yu', 'Azula', 2], ['Yu', 'Ty Lee', 2], ['Guru', 'Sokka', 3], ['Guru', 'Bosco', 2], ['Guru', 'Kuei', 2], ['Guru', 'Katara', 3], ['Guru', 'Momo', 3], ['Guru', 'General How', 2], ['Guru', 'Xin Fu', 1], ['Guru', 'Yu', 1], ['Guru', 'Ozai', 2], ['Guru', 'Bato', 1], ['Guru', 'Gyatso', 1], ['Iroh', 'General How', 2], ['Zuko', 'General How', 2], ['Appa', 'General How', 2], ['Aang', 'General How', 2], ['Sokka', 'General How', 2], ['Hakoda', 'Bosco', 1], ['Hakoda', 'Kuei', 2], ['Hakoda', 'General How', 1], ['Hakoda', 'Xin Fu', 1], ['Hakoda', 'Yu', 1], ['Hakoda', 'Ozai', 5], ['Hakoda', 'Gyatso', 1], ['Bosco', 'Mai', 2], ['Bosco', 'General How', 2], ['Bosco', 'Xin Fu', 1], ['Bosco', 'Ozai', 2], ['Bosco', 'Bato', 1], ['Bosco', 'Gyatso', 1], ['Ty Lee', 'General How', 2], ['Ty Lee', 'Xin Fu', 1], ['Ty Lee', 'Bato', 2], ['Ty Lee', 'Gyatso', 1], ['Mai', 'Kuei', 4], ['Mai', 'General How', 2], ['Mai', 'Xin Fu', 1], ['Mai', 'Yu', 1], ['Mai', 'Bato', 4], ['Mai', 'Gyatso', 1], ['Kyoshi', 'General How', 1], ['Kyoshi', 'Xin Fu', 1], ['Kyoshi', 'Ozai', 4], ['Kyoshi', 'Bato', 3], ['Kyoshi', 'Gyatso', 1], ['Kuei', 'General How', 2], ['Kuei', 'Xin Fu', 1], ['Kuei', 'Bato', 2], ['Kuei', 'Gyatso', 1], ['Li', 'General How', 2], ['Li', 'Xin Fu', 1], ['Li', 'Bato', 3], ['Li', 'Gyatso', 1], ['Azula', 'General How', 2], ['Azula', 'Xin Fu', 1], ['Azula', 'Bato', 5], ['Azula', 'Gyatso', 2], ['Katara', 'General How', 2], ['Momo', 'General How', 2], ['General How', 'Xin Fu', 1], ['General How', 'Yu', 1], ['General How', 'Toph', 2], ['General How', 'Ozai', 1], ['General How', 'Bato', 1], ['General How', 'Gyatso', 1], ['General How', 'Long Feng', 2], ['Xin Fu', 'Bato', 1], ['Xin Fu', 'Gyatso', 1], ['Xin Fu', 'Long Feng', 1], ['Yu', 'Bato', 1], ['Yu', 'Gyatso', 1], ['Toph', 'Bato', 5], ['Toph', 'Gyatso', 2], ['Ozai', 'Bato', 5], ['Ozai', 'Long Feng', 2], ['Bato', 'Gyatso', 1], ['Bato', 'Long Feng', 1], ['Gyatso', 'Long Feng', 1], ['Li', 'Sung', 1], ['Kuei', 'Sung', 1], ['Long Feng', 'Sung', 1], ['Guru', 'Sung', 1], ['Bosco', 'Sung', 1], ['General How', 'Sung', 1], ['Aang', 'Lo', 3], ['Aang', 'Chan', 2], ['Hakoda', 'Lo', 1], ['Hakoda', 'Pao', 1], ['Hakoda', 'Jin', 1], ['Hakoda', 'Than', 1], ['Hakoda', 'Ying', 1], ['Hakoda', 'Hope', 1], ['Hakoda', 'Pipsqueak', 4], ['Hakoda', 'The Duke', 6], ['Hakoda', 'Chan', 1], ['Hakoda', 'Roku', 2], ['Hakoda', 'Yue', 1], ['Bato', 'Lo', 1], ['Bato', 'Pao', 1], ['Bato', 'Jin', 1], ['Bato', 'Than', 1], ['Bato', 'Ying', 1], ['Bato', 'Hope', 1], ['Bato', 'Pipsqueak', 4], ['Bato', 'The Duke', 4], ['Bato', 'Chan', 1], ['Bato', 'Roku', 2], ['Bato', 'Yue', 1], ['Momo', 'Lo', 3], ['Momo', 'Chan', 2], ['Toph', 'Lo', 3], ['Toph', 'Jin', 1], ['Toph', 'Chan', 2], ['Katara', 'Lo', 3], ['Katara', 'Chan', 2], ['Appa', 'Lo', 3], ['Appa', 'Chan', 2], ['Zuko', 'Lo', 3], ['Zuko', 'Jin', 1], ['Zuko', 'Chan', 2], ['Mai', 'Lo', 3], ['Mai', 'Pao', 1], ['Mai', 'Jin', 1], ['Mai', 'Ying', 1], ['Mai', 'Pipsqueak', 3], ['Mai', 'The Duke', 3], ['Mai', 'Chan', 2], ['Mai', 'Roku', 2], ['Mai', 'Yue', 2], ['Lo', 'Li', 3], ['Lo', 'Pao', 1], ['Lo', 'Jin', 1], ['Lo', 'Than', 1], ['Lo', 'Ying', 1], ['Lo', 'Hope', 1], ['Lo', 'Sokka', 3], ['Lo', 'Kuei', 1], ['Lo', 'Pipsqueak', 1], ['Lo', 'The Duke', 1], ['Lo', 'Chan', 2], ['Lo', 'Azula', 3], ['Lo', 'Ozai', 2], ['Lo', 'Roku', 1], ['Lo', 'Yue', 1], ['Li', 'Jin', 1], ['Li', 'Than', 1], ['Li', 'Ying', 1], ['Li', 'Hope', 1], ['Li', 'Chan', 2], ['Li', 'Roku', 1], ['Pao', 'Jin', 1], ['Pao', 'Than', 1], ['Pao', 'Ying', 1], ['Pao', 'Hope', 1], ['Pao', 'Chan', 1], ['Pao', 'Azula', 1], ['Pao', 'Ozai', 1], ['Pao', 'Roku', 1], ['Pao', 'Yue', 1], ['Jin', 'Than', 1], ['Jin', 'Ying', 1], ['Jin', 'Kuei', 1], ['Jin', 'Pipsqueak', 1], ['Jin', 'The Duke', 1], ['Jin', 'Chan', 1], ['Jin', 'Azula', 1], ['Jin', 'Ozai', 1], ['Jin', 'Roku', 1], ['Jin', 'Yue', 1], ['Than', 'Pipsqueak', 1], ['Than', 'The Duke', 1], ['Than', 'Chan', 1], ['Than', 'Ozai', 1], ['Than', 'Roku', 1], ['Than', 'Yue', 1], ['Ying', 'Pipsqueak', 1], ['Ying', 'The Duke', 1], ['Ying', 'Chan', 1], ['Ying', 'Azula', 1], ['Ying', 'Ozai', 1], ['Ying', 'Roku', 1], ['Ying', 'Yue', 1], ['Hope', 'Pipsqueak', 1], ['Hope', 'The Duke', 1], ['Hope', 'Chan', 1], ['Hope', 'Roku', 1], ['Hope', 'Yue', 1], ['Sokka', 'Chan', 2], ['Kuei', 'Chan', 1], ['Kuei', 'Yue', 2], ['Pipsqueak', 'Chan', 1], ['Pipsqueak', 'Azula', 4], ['Pipsqueak', 'Ozai', 4], ['Pipsqueak', 'Roku', 2], ['Pipsqueak', 'Yue', 1], ['The Duke', 'Chan', 1], ['The Duke', 'Azula', 6], ['The Duke', 'Ozai', 5], ['The Duke', 'Roku', 3], ['The Duke', 'Yue', 1], ['Chan', 'Azula', 2], ['Chan', 'Ozai', 1], ['Chan', 'Roku', 1], ['Chan', 'Yue', 1], ['Azula', 'Yue', 2], ['Zuko', 'Kwan', 2], ['Zuko', 'Hide', 1], ['Zuko', 'On Ji', 1], ['Zuko', 'Shoji', 1], ['Sokka', 'Kwan', 2], ['Sokka', 'Hide', 1], ['Sokka', 'Sozin', 4], ['Sokka', 'On Ji', 1], ['Sokka', 'Shoji', 1], ['Momo', 'Kwan', 1], ['Momo', 'Hide', 1], ['Momo', 'Sozin', 2], ['Momo', 'On Ji', 1], ['Momo', 'Shoji', 1], ['Aang', 'Kwan', 2], ['Aang', 'Hide', 1], ['Aang', 'Sozin', 4], ['Aang', 'On Ji', 1], ['Aang', 'Shoji', 1], ['Katara', 'Kwan', 2], ['Katara', 'Hide', 1], ['Katara', 'Sozin', 4], ['Katara', 'On Ji', 1], ['Katara', 'Shoji', 1], ['Toph', 'Kwan', 2], ['Toph', 'Hide', 1], ['Toph', 'Sozin', 4], ['Toph', 'On Ji', 1], ['Toph', 'Shoji', 1], ['Kwan', 'Hide', 1], ['Kwan', 'Iroh', 2], ['Kwan', 'Ozai', 1], ['Kwan', 'Sozin', 2], ['Kwan', 'On Ji', 1], ['Kwan', 'Mai', 1], ['Kwan', 'Ty Lee', 1], ['Kwan', 'Appa', 2], ['Kwan', 'Shoji', 1], ['Hide', 'Iroh', 1], ['Hide', 'Ozai', 1], ['Hide', 'Sozin', 1], ['Hide', 'On Ji', 1], ['Hide', 'Mai', 1], ['Hide', 'Ty Lee', 1], ['Hide', 'Appa', 1], ['Hide', 'Shoji', 1], ['Iroh', 'On Ji', 1], ['Iroh', 'Shoji', 1], ['Ozai', 'On Ji', 1], ['Ozai', 'Shoji', 1], ['Sozin', 'On Ji', 1], ['Sozin', 'Appa', 4], ['Sozin', 'Shoji', 1], ['On Ji', 'Mai', 1], ['On Ji', 'Ty Lee', 1], ['On Ji', 'Appa', 1], ['On Ji', 'Shoji', 1], ['Mai', 'Shoji', 1], ['Ty Lee', 'Shoji', 1], ['Appa', 'Shoji', 1], ['Painted Lady', 'Aang', 2], ['Painted Lady', 'Momo', 2], ['Painted Lady', 'Appa', 2], ['Painted Lady', 'Dock', 1], ['Painted Lady', 'Ozai', 2], ['Painted Lady', 'Sokka', 2], ['Painted Lady', 'Katara', 2], ['Painted Lady', 'Toph', 2], ['Painted Lady', 'Mung', 1], ['Aang', 'Dock', 1], ['Aang', 'Mung', 1], ['Momo', 'Dock', 1], ['Momo', 'Mung', 1], ['Appa', 'Dock', 1], ['Appa', 'Mung', 1], ['Dock', 'Ozai', 1], ['Dock', 'Sokka', 1], ['Dock', 'Katara', 1], ['Dock', 'Toph', 1], ['Dock', 'Mung', 1], ['Ozai', 'Mung', 1], ['Sokka', 'Mung', 1], ['Katara', 'Mung', 1], ['Toph', 'Mung', 1], ['Katara', 'Poon', 3], ['Katara', 'Fat', 1], ['Katara', 'Piandao', 3], ['Aang', 'Poon', 3], ['Aang', 'Fat', 1], ['Aang', 'Piandao', 3], ['Appa', 'Poon', 3], ['Appa', 'Fat', 1], ['Appa', 'Piandao', 3], ['Sokka', 'Poon', 3], ['Sokka', 'Fat', 1], ['Sokka', 'Piandao', 3], ['Toph', 'Poon', 3], ['Toph', 'Fat', 1], ['Toph', 'Piandao', 3], ['Momo', 'Poon', 3], ['Momo', 'Fat', 1], ['Momo', 'Piandao', 3], ['Poon', 'Iroh', 3], ['Poon', 'Fat', 1], ['Poon', 'Piandao', 1], ['Iroh', 'Fat', 1], ['Iroh', 'Piandao', 3], ['Fat', 'Piandao', 1], ['Ty Lee', 'Lo', 2], ['Ty Lee', 'Ruon-Jian', 1], ['Ty Lee', 'Chan', 1], ['Ty Lee', 'Combustion Man', 2], ['Zuko', 'Ruon-Jian', 1], ['Zuko', 'Combustion Man', 3], ['Azula', 'Ruon-Jian', 1], ['Azula', 'Combustion Man', 3], ['Mai', 'Ruon-Jian', 1], ['Mai', 'Combustion Man', 2], ['Li', 'Ruon-Jian', 1], ['Li', 'Ursa', 2], ['Li', 'Combustion Man', 1], ['Lo', 'Ruon-Jian', 1], ['Lo', 'Ursa', 2], ['Lo', 'Combustion Man', 1], ['Sokka', 'Ruon-Jian', 1], ['Sokka', 'Ursa', 2], ['Sokka', 'Combustion Man', 4], ['Aang', 'Ruon-Jian', 1], ['Aang', 'Ursa', 2], ['Aang', 'Combustion Man', 4], ['Momo', 'Ruon-Jian', 1], ['Momo', 'Ursa', 2], ['Momo', 'Combustion Man', 4], ['Toph', 'Ruon-Jian', 1], ['Toph', 'Ursa', 2], ['Toph', 'Combustion Man', 4], ['Katara', 'Ruon-Jian', 1], ['Katara', 'Ursa', 2], ['Katara', 'Combustion Man', 4], ['Ruon-Jian', 'Chan', 1], ['Ruon-Jian', 'Ursa', 1], ['Ruon-Jian', 'Combustion Man', 1], ['Ruon-Jian', 'Appa', 1], ['Chan', 'Ursa', 1], ['Chan', 'Combustion Man', 1], ['Ursa', 'Combustion Man', 1], ['Ursa', 'Appa', 2], ['Combustion Man', 'Appa', 4], ['Aang', 'Fang', 1], ['Aang', 'Ta Min', 1], ['Roku', 'Sozin', 3], ['Roku', 'Fang', 1], ['Roku', 'Ta Min', 1], ['Zuko', 'Fang', 1], ['Zuko', 'Ta Min', 1], ['Appa', 'Fang', 1], ['Appa', 'Ta Min', 1], ['Katara', 'Fang', 1], ['Katara', 'Ta Min', 1], ['Sokka', 'Fang', 1], ['Sokka', 'Ta Min', 1], ['Azula', 'Fang', 1], ['Azula', 'Ta Min', 1], ['Sozin', 'Fang', 1], ['Sozin', 'Gyatso', 1], ['Sozin', 'Ta Min', 1], ['Fang', 'Gyatso', 1], ['Fang', 'Ta Min', 1], ['Fang', 'Iroh', 1], ['Fang', 'Toph', 1], ['Fang', 'Ozai', 1], ['Gyatso', 'Ta Min', 1], ['Ta Min', 'Iroh', 1], ['Ta Min', 'Toph', 1], ['Ta Min', 'Ozai', 1], ['Toph', 'Hawky', 1], ['Ozai', 'Hawky', 1], ['Ozai', 'Combustion Man', 3], 
['Katara', 'Hawky', 1], ['Aang', 'Hawky', 1], ['Sokka', 'Hawky', 1], ['Momo', 'Hawky', 1], ['Hawky', 'Combustion Man', 1], ['Hawky', 'Appa', 1], ['Appa', 'Hama', 1], ['Appa', 'Ding', 1], ['Aang', 'Hama', 1], ['Aang', 'Ding', 1], ['Toph', 'Hama', 1], ['Toph', 'Kanna', 2], ['Toph', 'Ding', 1], ['Sokka', 'Hama', 1], ['Sokka', 'Ding', 1], ['Momo', 'Hama', 1], ['Momo', 'Ding', 1], ['Hama', 'Katara', 1], ['Hama', 'Kanna', 1], ['Hama', 'Ding', 1], ['Katara', 'Ding', 1], ['Kanna', 'Ding', 1], ['Aang', 'Ming', 1], ['Aang', 'Azulon', 1], ['Sokka', 'Ming', 1], ['Sokka', 'Azulon', 1], ['Katara', 'Ming', 1], ['Katara', 'Azulon', 1], ['Appa', 'Ming', 1], ['Appa', 'Azulon', 1], ['Toph', 'Due', 2], ['Toph', 'Tho', 2], ['Toph', 'Hue', 2], ['Toph', 'Haru', 7], ['Toph', 'Tyro', 2], ['Toph', 'The Mechanist', 3], ['Toph', 'Teo', 6], ['Toph', 'Ming', 1], ['Toph', 'Azulon', 1], ['Momo', 'Ming', 1], ['Momo', 'Azulon', 1], ['Azula', 'Due', 2], ['Azula', 'Tho', 2], ['Azula', 'Hue', 2], ['Azula', 'Haru', 5], ['Azula', 'Tyro', 2], ['Azula', 'Hippo', 3], ['Azula', 'The Boulder', 3], ['Azula', 'The Mechanist', 3], ['Azula', 'Teo', 5], ['Azula', 'Poon', 2], ['Azula', 'Ming', 1], ['Hakoda', 'Due', 2], ['Hakoda', 'Tho', 2], ['Hakoda', 'Hue', 2], ['Hakoda', 'Haru', 5], ['Hakoda', 'Tyro', 2], ['Hakoda', 'Hippo', 3], ['Hakoda', 'The Boulder', 3], ['Hakoda', 'The Mechanist', 3], ['Hakoda', 'Teo', 5], ['Hakoda', 'Poon', 2], ['Hakoda', 'Ming', 1], ['Hakoda', 'Azulon', 1], ['Bato', 'Due', 2], ['Bato', 'Tho', 2], ['Bato', 'Hue', 2], ['Bato', 'Haru', 3], ['Bato', 'Tyro', 2], ['Bato', 'Hippo', 3], ['Bato', 'The Boulder', 3], ['Bato', 'The Mechanist', 3], ['Bato', 'Teo', 3], ['Bato', 'Poon', 2], ['Bato', 'Ming', 1], ['Bato', 'Azulon', 1], ['Due', 'Haru', 2], ['Due', 'Tyro', 2], ['Due', 'Hippo', 2], ['Due', 'The Boulder', 2], ['Due', 'The Mechanist', 2], ['Due', 'Teo', 2], ['Due', 'The Duke', 2], ['Due', 'Pipsqueak', 2], ['Due', 'Poon', 2], ['Due', 'Ming', 1], ['Due', 'Ozai', 2], ['Due', 'Kyoshi', 
1], ['Due', 'Azulon', 1], ['Due', 'Mai', 1], ['Tho', 'Haru', 2], ['Tho', 'Tyro', 2], ['Tho', 'Hippo', 2], ['Tho', 'The Boulder', 2], ['Tho', 'The Mechanist', 2], ['Tho', 'Teo', 2], ['Tho', 'The Duke', 2], ['Tho', 'Pipsqueak', 2], ['Tho', 'Poon', 2], ['Tho', 'Ming', 1], ['Tho', 'Ozai', 2], ['Tho', 'Kyoshi', 1], ['Tho', 'Azulon', 1], ['Tho', 'Mai', 1], ['Hue', 'Haru', 2], ['Hue', 'Tyro', 2], ['Hue', 'Hippo', 2], ['Hue', 'The Boulder', 2], ['Hue', 'The Mechanist', 2], ['Hue', 'Teo', 2], ['Hue', 'The Duke', 2], ['Hue', 'Pipsqueak', 2], ['Hue', 'Poon', 2], ['Hue', 'Ming', 1], ['Hue', 'Ozai', 2], ['Hue', 'Kyoshi', 1], ['Hue', 'Azulon', 1], ['Hue', 'Mai', 1], ['Haru', 'Hippo', 3], ['Haru', 'The Boulder', 3], ['Haru', 'The Mechanist', 3], ['Haru', 'Teo', 6], ['Haru', 'The Duke', 7], ['Haru', 'Pipsqueak', 3], ['Haru', 'Poon', 2], ['Haru', 'Iroh', 6], ['Haru', 'Ming', 1], ['Haru', 'Kyoshi', 2], ['Haru', 'Zuko', 7], ['Haru', 'Azulon', 1], ['Haru', 'Mai', 2], ['Tyro', 'Hippo', 2], ['Tyro', 'The Boulder', 2], ['Tyro', 'The Mechanist', 2], ['Tyro', 'Teo', 2], ['Tyro', 'The Duke', 2], ['Tyro', 'Pipsqueak', 2], ['Tyro', 'Poon', 2], ['Tyro', 'Iroh', 2], ['Tyro', 'Ming', 1], ['Tyro', 'Kyoshi', 1], ['Tyro', 'Zuko', 2], ['Tyro', 'Azulon', 1], ['Tyro', 'Mai', 1], ['Hippo', 'The Mechanist', 3], ['Hippo', 'Teo', 3], ['Hippo', 'The Duke', 3], ['Hippo', 'Pipsqueak', 3], ['Hippo', 'Poon', 2], ['Hippo', 'Iroh', 3], ['Hippo', 'Ming', 1], ['Hippo', 'Kyoshi', 2], ['Hippo', 'Zuko', 3], ['Hippo', 'Azulon', 1], ['Hippo', 'Mai', 2], ['The Boulder', 'The Mechanist', 3], ['The Boulder', 'Teo', 3], ['The Boulder', 'The Duke', 3], ['The Boulder', 'Pipsqueak', 3], ['The Boulder', 'Poon', 2], ['The Boulder', 'Iroh', 3], ['The Boulder', 'Ming', 1], ['The Boulder', 'Kyoshi', 2], ['The Boulder', 'Zuko', 3], ['The Boulder', 'Azulon', 1], ['The Boulder', 'Mai', 2], ['The Mechanist', 'The Duke', 3], ['The Mechanist', 'Pipsqueak', 3], ['The Mechanist', 'Poon', 2], ['The Mechanist', 'Iroh', 3], ['The Mechanist', 'Ming', 1], ['The Mechanist', 'Ozai', 3], ['The Mechanist', 'Kyoshi', 2], ['The Mechanist', 'Zuko', 3], ['The Mechanist', 'Azulon', 1], ['The Mechanist', 'Mai', 2], ['Teo', 'The Duke', 6], ['Teo', 'Pipsqueak', 3], ['Teo', 'Poon', 2], ['Teo', 'Iroh', 5], ['Teo', 'Ming', 1], ['Teo', 'Ozai', 4], ['Teo', 'Kyoshi', 2], ['Teo', 'Zuko', 6], ['Teo', 'Azulon', 1], ['Teo', 'Mai', 2], ['The Duke', 'Poon', 2], ['The Duke', 'Ming', 1], ['The Duke', 'Kyoshi', 2], ['The Duke', 'Azulon', 1], ['Pipsqueak', 'Poon', 2], ['Pipsqueak', 'Ming', 1], ['Pipsqueak', 'Kyoshi', 2], ['Pipsqueak', 'Azulon', 1], ['Poon', 'Ming', 1], ['Poon', 'Ozai', 2], ['Poon', 'Kyoshi', 1], ['Poon', 'Zuko', 2], ['Poon', 'Azulon', 1], ['Poon', 'Mai', 1], ['Iroh', 'Ming', 1], ['Ming', 'Ozai', 1], ['Ming', 'Kyoshi', 1], ['Ming', 'Zuko', 1], ['Ming', 'Azulon', 1], ['Ming', 'Mai', 1], ['Kyoshi', 'Azulon', 1], ['Hue', 'Qin', 1], ['Hue', 'Li', 1], ['Hakoda', 'Qin', 1], ['Ozai', 'Qin', 1], ['The Mechanist', 'Qin', 1], ['The Mechanist', 'Li', 1], ['The Boulder', 'Qin', 1], ['The Boulder', 'Li', 1], ['Hippo', 'Qin', 1], ['Hippo', 'Li', 1], ['Bato', 'Qin', 1], ['Qin', 'Li', 1], ['Qin', 'Tyro', 1], ['Qin', 'Poon', 1], ['Qin', 'Due', 1], ['Qin', 'Tho', 1], ['Qin', 'Teo', 1], ['Qin', 'The Duke', 1], ['Qin', 'Pipsqueak', 1], ['Qin', 'Haru', 1], ['Li', 'Tyro', 1], ['Li', 'Poon', 1], ['Li', 'Due', 1], ['Li', 'Tho', 1], ['Li', 'Teo', 1], ['Li', 'Haru', 1], ['Toph', 'Jeong Jeong', 3], ['Toph', 'Zhao', 2], ['Haru', 'Jeong Jeong', 1], ['Haru', 'Combustion Man', 1], ['Haru', 'Zhao', 1], ['Teo', 'Jeong Jeong', 1], ['Teo', 'Combustion Man', 1], ['Teo', 'Zhao', 1], ['The Duke', 'Jeong Jeong', 1], ['The Duke', 'Combustion Man', 1], ['The Duke', 'Zhao', 1], ['Zuko', 'Jeong Jeong', 3], ['Iroh', 'Jeong Jeong', 3], ['Iroh', 'Combustion Man', 2], ['Jeong Jeong', 'Azula', 3], ['Jeong Jeong', 'Combustion Man', 1], ['Azula', 'Zhao', 2], ['Combustion Man', 'Zhao', 2], ['Zuko', 'Ham Ghao', 1], ['Aang', 'Ham Ghao', 1], ['Sokka', 'Ham Ghao', 1], ['Appa', 'Ham Ghao', 1], ['Toph', 'Ham Ghao', 1], ['Haru', 'Roku', 2], ['Haru', 'Sozin', 1], ['Haru', 'Ham Ghao', 1], ['Haru', 'Kwan', 1], ['The Duke', 'Sozin', 1], ['The Duke', 'Ham Ghao', 1], ['The Duke', 'Kwan', 1], ['Katara', 'Ham Ghao', 1], ['Roku', 'Ham Ghao', 1], ['Roku', 'Kwan', 1], ['Sozin', 'Ham Ghao', 1], ['Iroh', 'Ham Ghao', 1], ['Ham Ghao', 'Kwan', 1], ['Zuko', 'Chit Sang', 3], ['Katara', 'Chit Sang', 3], ['Aang', 'Chit Sang', 3], ['Toph', 'Chit Sang', 3], ['The Duke', 'Chit Sang', 2], ['The Duke', 'Suki', 3], ['Haru', 'Chit Sang', 2], ['Haru', 'Suki', 3], ['Iroh', 'Chit Sang', 2], ['Teo', 'Chit Sang', 2], ['Teo', 'Suki', 3], ['Sokka', 'Chit Sang', 3], ['Appa', 'Chit Sang', 2], ['Momo', 'Chit Sang', 2], ['Chit Sang', 'Suki', 3], ['Chit Sang', 'Hakoda', 3], ['Chit Sang', 'Mai', 1], ['Chit Sang', 'Azula', 2], ['Chit Sang', 'Ty Lee', 1], ['Chit Sang', 'Jet', 1], ['Chit Sang', 'Yon Rha', 1], ['Chit Sang', 'Kya', 1], ['Teo', 'Jet', 1], ['Teo', 'Yon Rha', 1], ['Teo', 'Kya', 1], ['The Duke', 'Yon Rha', 1], ['The Duke', 'Kya', 1], ['Zuko', 'Yon Rha', 1], ['Zuko', 'Kya', 1], ['Aang', 'Yon Rha', 1], ['Aang', 'Kya', 1], ['Appa', 'Yon Rha', 1], ['Appa', 'Kya', 1], ['Katara', 'Yon Rha', 1], ['Katara', 'Kya', 1], ['Haru', 'Jet', 1], ['Haru', 'Yon Rha', 1], ['Haru', 'Kya', 1], ['Toph', 'Yon Rha', 1], ['Toph', 'Kya', 1], ['Sokka', 'Yon Rha', 1], ['Sokka', 'Kya', 1], ['Azula', 'Yon Rha', 1], ['Azula', 'Kya', 1], ['Hakoda', 'Jet', 1], ['Hakoda', 'Yon Rha', 1], ['Hakoda', 'Kya', 1], ['Suki', 'Yon Rha', 1], ['Suki', 'Kya', 1], ['Jet', 'Yon Rha', 1], ['Jet', 'Kya', 1], ['Momo', 'Yon Rha', 1], ['Momo', 'Kya', 1], ['Yon Rha', 'Kya', 1], ['Katara', 'Actress Katara', 1], ['Katara', 'Actor Sokka', 1], ['Katara', 'Actor Zuko', 1], ['Katara', 'Actor Bumi', 1], ['Katara', 'Actor Jet', 1], ['Katara', 'Actress Yue', 1], ['Katara', 'Actor Toph', 2], ['Katara', 'Actress Azula', 1], ['Toph', 'Actress Katara', 1], ['Toph', 'Actor Sokka', 1], ['Toph', 'Actor Zuko', 1], ['Toph', 'Actor Bumi', 1], ['Toph', 'Flopsy', 1], ['Toph', 'Actor Jet', 1], ['Toph', 'Actress Yue', 1], ['Toph', 'Actor Toph', 2], ['Toph', 'Actress Azula', 1], ['Zuko', 'Painted Lady', 1], ['Zuko', 'Actress Katara', 1], ['Zuko', 'Actor Sokka', 1], ['Zuko', 'Actor Zuko', 1], ['Zuko', 'Actor Bumi', 1], ['Zuko', 'Actor Jet', 1], ['Zuko', 'Actress Yue', 1], ['Zuko', 'Actor Toph', 2], ['Zuko', 'Actress Azula', 1], ['Aang', 'Actress Katara', 1], ['Aang', 'Actor Sokka', 1], ['Aang', 'Actor Zuko', 1], ['Aang', 'Actor Bumi', 1], ['Aang', 'Actor Jet', 1], 
['Aang', 'Actress Yue', 1], ['Aang', 'Actor Toph', 2], ['Aang', 'Actress Azula', 1], ['Ozai', 'Suki', 5], ['Ozai', 'Actress Katara', 1], ['Ozai', 'Actor Sokka', 1], ['Ozai', 'Actor Zuko', 1], ['Ozai', 'Actor Bumi', 1], ['Ozai', 'Flopsy', 1], ['Ozai', 'Jet', 1], ['Ozai', 'Actor Jet', 
1], ['Ozai', 'Actress Yue', 1], ['Ozai', 'Actor Toph', 2], ['Ozai', 'Actress Azula', 1], ['Sokka', 'Actress Katara', 1], ['Sokka', 'Actor Sokka', 1], ['Sokka', 'Actor Zuko', 1], ['Sokka', 'Actor Bumi', 1], ['Sokka', 'Actor Jet', 1], ['Sokka', 'Actress Yue', 1], ['Sokka', 'Actor Toph', 2], ['Sokka', 'Actress Azula', 1], ['Suki', 'Painted Lady', 1], ['Suki', 'Actress Katara', 1], ['Suki', 'Actor Sokka', 1], ['Suki', 'Actor Zuko', 1], ['Suki', 'Bumi', 4], ['Suki', 'Actor Bumi', 1], ['Suki', 'Flopsy', 1], ['Suki', 'Actor Jet', 1], ['Suki', 'Yue', 1], ['Suki', 'Actress Yue', 1], ['Suki', 'Zhao', 1], ['Suki', 'Actor Toph', 2], ['Suki', 'Actress Azula', 1], ['Suki', 'Combustion Man', 1], ['Painted Lady', 'Actress Katara', 1], ['Painted Lady', 'Actor Sokka', 1], ['Painted Lady', 'Iroh', 1], ['Painted Lady', 'Actor Zuko', 1], ['Painted Lady', 'Bumi', 1], ['Painted Lady', 'Actor Bumi', 1], ['Painted Lady', 'Flopsy', 1], ['Painted Lady', 'Jet', 1], ['Painted Lady', 'Actor Jet', 1], ['Painted Lady', 'Yue', 1], ['Painted Lady', 'Actress Yue', 1], ['Painted Lady', 'Zhao', 1], ['Painted Lady', 'Actor Toph', 1], ['Painted Lady', 'Actress Azula', 1], ['Painted Lady', 'Azula', 1], ['Painted Lady', 'Mai', 1], ['Painted Lady', 'Kuei', 1], ['Painted Lady', 'Ty Lee', 1], ['Painted Lady', 'Combustion Man', 1], ['Actress Katara', 'Actor Sokka', 1], ['Actress Katara', 'Appa', 1], ['Actress Katara', 'Iroh', 1], ['Actress Katara', 'Actor Zuko', 1], ['Actress Katara', 'Momo', 1], ['Actress Katara', 'Bumi', 1], ['Actress Katara', 'Actor Bumi', 1], ['Actress Katara', 'Flopsy', 1], ['Actress Katara', 'Jet', 1], ['Actress Katara', 'Actor Jet', 1], ['Actress Katara', 'Yue', 1], ['Actress Katara', 'Actress Yue', 1], ['Actress Katara', 'Zhao', 1], ['Actress Katara', 'Actor Toph', 1], ['Actress Katara', 'Actress Azula', 1], ['Actress Katara', 'Azula', 1], ['Actress Katara', 'Mai', 1], ['Actress Katara', 'Kuei', 1], ['Actress Katara', 'Ty Lee', 1], ['Actress Katara', 'Combustion Man', 1], ['Actor Sokka', 'Appa', 1], ['Actor Sokka', 'Iroh', 1], ['Actor Sokka', 'Actor Zuko', 1], ['Actor Sokka', 'Momo', 1], ['Actor Sokka', 'Bumi', 1], ['Actor Sokka', 'Actor Bumi', 1], ['Actor Sokka', 'Flopsy', 1], ['Actor Sokka', 'Jet', 1], ['Actor Sokka', 'Actor Jet', 1], ['Actor Sokka', 'Yue', 1], ['Actor Sokka', 'Actress Yue', 1], ['Actor Sokka', 'Zhao', 1], ['Actor Sokka', 'Actor Toph', 1], ['Actor Sokka', 'Actress Azula', 1], ['Actor Sokka', 'Azula', 1], ['Actor Sokka', 'Mai', 1], ['Actor Sokka', 'Kuei', 1], ['Actor Sokka', 'Ty Lee', 1], ['Actor Sokka', 'Combustion Man', 1], ['Appa', 'Actor Zuko', 1], ['Appa', 'Actor Bumi', 1], ['Appa', 'Actor Jet', 1], ['Appa', 'Actress Yue', 1], ['Appa', 'Actor Toph', 2], ['Appa', 'Actress Azula', 1], ['Iroh', 'Actor Zuko', 1], ['Iroh', 'Actor Bumi', 1], ['Iroh', 'Actor Jet', 1], ['Iroh', 'Actress Yue', 1], ['Iroh', 'Actor Toph', 2], ['Iroh', 'Actress Azula', 1], ['Actor Zuko', 'Momo', 1], ['Actor Zuko', 'Bumi', 1], ['Actor Zuko', 'Actor Bumi', 1], ['Actor Zuko', 'Flopsy', 1], ['Actor Zuko', 'Jet', 1], ['Actor Zuko', 'Actor Jet', 1], ['Actor Zuko', 'Yue', 1], ['Actor Zuko', 'Actress Yue', 1], ['Actor Zuko', 'Zhao', 1], ['Actor Zuko', 'Actor Toph', 1], ['Actor Zuko', 'Actress Azula', 1], ['Actor Zuko', 'Azula', 1], ['Actor Zuko', 'Mai', 1], ['Actor Zuko', 'Kuei', 1], ['Actor Zuko', 'Ty Lee', 1], ['Actor Zuko', 'Combustion Man', 1], ['Momo', 'Actor Bumi', 1], ['Momo', 'Actor Jet', 1], ['Momo', 'Actress Yue', 1], ['Momo', 'Actor Toph', 2], ['Momo', 'Actress Azula', 1], ['Bumi', 'Actor Bumi', 1], ['Bumi', 'Jet', 1], ['Bumi', 'Actor Jet', 1], ['Bumi', 'Actress Yue', 1], ['Bumi', 'Zhao', 1], ['Bumi', 'Actor Toph', 1], ['Bumi', 'Actress Azula', 1], ['Bumi', 'Kuei', 1], ['Bumi', 'Combustion Man', 1], ['Actor Bumi', 'Flopsy', 1], ['Actor Bumi', 'Jet', 1], ['Actor Bumi', 'Actor Jet', 1], ['Actor Bumi', 'Yue', 1], ['Actor Bumi', 'Actress Yue', 1], ['Actor Bumi', 'Zhao', 1], ['Actor Bumi', 'Actor Toph', 1], ['Actor Bumi', 'Actress Azula', 1], ['Actor Bumi', 'Azula', 1], ['Actor Bumi', 'Mai', 1], ['Actor Bumi', 'Kuei', 1], ['Actor Bumi', 'Ty Lee', 1], ['Actor Bumi', 'Combustion Man', 1], ['Flopsy', 'Jet', 1], ['Flopsy', 'Actor Jet', 1], ['Flopsy', 'Yue', 1], ['Flopsy', 'Actress Yue', 1], ['Flopsy', 'Zhao', 1], ['Flopsy', 'Actor Toph', 1], ['Flopsy', 'Actress Azula', 1], ['Flopsy', 'Kuei', 1], ['Flopsy', 'Combustion Man', 1], ['Jet', 'Actor Jet', 1], ['Jet', 'Yue', 1], ['Jet', 'Actress Yue', 1], ['Jet', 'Zhao', 1], ['Jet', 'Actor Toph', 1], ['Jet', 'Actress Azula', 1], ['Actor Toph', 'Mai', 1], ['Actor Toph', 'Kuei', 2], ['Actor Toph', 'Ty Lee', 1], ['Actor Toph', 'Combustion Man', 1], ['Actress Azula', 'Azula', 1], ['Actress Azula', 'Mai', 1], ['Actress Azula', 'Kuei', 1], ['Actress Azula', 'Ty Lee', 1], ['Actress Azula', 'Combustion Man', 1], ['Kuei', 'Combustion Man', 1], ['Suki', 'Bosco', 1], ['Suki', 'Shinu', 1], ['Suki', 'June', 2], ['Toph', 'Shinu', 1], ['Toph', 'June', 2], ['Kuei', 'Shinu', 1], ['Kuei', 'June', 1], ['Bosco', 'Shinu', 1], ['Bosco', 'Actor Toph', 1], ['Bosco', 'June', 1], ['Ozai', 'June', 2], ['Azula', 'Shinu', 1], ['Azula', 'June', 2], ['Shinu', 'Actor Toph', 1], ['Shinu', 'June', 1], ['Actor Toph', 'June', 1], ['June', 'Nyla', 1], ['June', 'Roku', 1], ['June', 'Pakku', 1], ['June', 'Bumi', 1], ['June', 'Sozin', 1], ['June', 'Kanna', 1], ['June', 'Jeong Jeong', 1], ['June', 'Piandao', 1], ['June', 'Kyoshi', 1], ['June', 'Chin', 1], ['June', 'Kuruk', 1], ['June', 'Yangchen', 1], ['June', 'Lion Turtle', 1], ['Sokka', 'Nyla', 1], ['Sokka', 'Kuruk', 1], ['Sokka', 'Yangchen', 1], ['Sokka', 'Lion Turtle', 2], ['Zuko', 'Nyla', 1], ['Zuko', 'Piandao', 2], ['Zuko', 'Kuruk', 1], ['Zuko', 'Yangchen', 1], ['Zuko', 'Lion Turtle', 2], ['Katara', 'Nyla', 1], ['Katara', 'Kuruk', 1], ['Katara', 'Yangchen', 1], ['Katara', 'Lion Turtle', 2], ['Appa', 'Nyla', 1], ['Appa', 'Kuruk', 1], ['Appa', 'Yangchen', 1], ['Appa', 'Lion Turtle', 2], 
['Nyla', 'Toph', 1], ['Nyla', 'Momo', 1], ['Nyla', 'Aang', 1], ['Nyla', 'Suki', 1], ['Nyla', 'Roku', 1], ['Nyla', 'Pakku', 1], ['Nyla', 'Bumi', 1], ['Nyla', 'Sozin', 1], ['Nyla', 'Ozai', 1], ['Nyla', 'Kanna', 1], ['Nyla', 'Jeong Jeong', 1], ['Nyla', 'Piandao', 1], ['Nyla', 'Iroh', 1], ['Nyla', 'Kyoshi', 1], ['Nyla', 'Chin', 1], ['Nyla', 'Kuruk', 1], ['Nyla', 'Yangchen', 1], ['Nyla', 'Azula', 1], ['Nyla', 'Lion Turtle', 1], ['Toph', 'Pakku', 2], ['Toph', 'Chin', 1], ['Toph', 'Kuruk', 1], ['Toph', 'Yangchen', 1], ['Toph', 'Lion Turtle', 2], ['Momo', 'Kuruk', 1], ['Momo', 'Yangchen', 1], ['Momo', 'Lion Turtle', 2], ['Aang', 'Kuruk', 1], ['Aang', 'Yangchen', 1], ['Aang', 'Lion Turtle', 2], ['Suki', 'Pakku', 2], ['Suki', 'Sozin', 1], ['Suki', 'Kanna', 1], ['Suki', 'Jeong Jeong', 2], ['Suki', 'Piandao', 2], ['Suki', 'Kuruk', 1], ['Suki', 'Yangchen', 1], ['Suki', 'Lion Turtle', 2], ['Roku', 'Piandao', 1], ['Roku', 'Kuruk', 1], ['Roku', 'Yangchen', 1], ['Roku', 'Lion Turtle', 2], ['Pakku', 'Bumi', 2], ['Pakku', 'Sozin', 1], ['Pakku', 'Jeong Jeong', 2], ['Pakku', 'Piandao', 2], ['Pakku', 'Kyoshi', 1], ['Pakku', 'Chin', 1], ['Pakku', 'Kuruk', 1], ['Pakku', 'Yangchen', 1], ['Pakku', 'Lion Turtle', 1], ['Bumi', 'Sozin', 1], ['Bumi', 'Kanna', 1], ['Bumi', 'Jeong Jeong', 2], ['Bumi', 'Piandao', 2], ['Bumi', 'Kyoshi', 2], ['Bumi', 'Chin', 1], ['Bumi', 'Kuruk', 1], ['Bumi', 'Yangchen', 1], ['Bumi', 'Lion Turtle', 2], ['Sozin', 'Kanna', 1], ['Sozin', 'Jeong Jeong', 1], ['Sozin', 'Piandao', 1], ['Sozin', 'Kyoshi', 1], ['Sozin', 'Chin', 1], ['Sozin', 'Kuruk', 1], ['Sozin', 'Yangchen', 1], ['Sozin', 'Lion Turtle', 1], ['Ozai', 'Piandao', 2], ['Ozai', 'Chin', 1], ['Ozai', 'Kuruk', 1], ['Ozai', 'Yangchen', 1], ['Ozai', 'Lion Turtle', 2], ['Kanna', 'Jeong Jeong', 1], ['Kanna', 'Piandao', 1], ['Kanna', 'Kyoshi', 1], ['Kanna', 'Chin', 1], ['Kanna', 'Kuruk', 1], ['Kanna', 'Yangchen', 1], ['Kanna', 'Lion Turtle', 1], ['Jeong Jeong', 'Piandao', 2], ['Jeong Jeong', 'Kyoshi', 1], ['Jeong Jeong', 'Chin', 1], ['Jeong Jeong', 'Kuruk', 1], ['Jeong Jeong', 'Yangchen', 1], ['Jeong Jeong', 'Lion Turtle', 1], ['Piandao', 'Kyoshi', 1], ['Piandao', 'Chin', 1], ['Piandao', 'Kuruk', 1], ['Piandao', 'Yangchen', 1], ['Piandao', 'Azula', 2], ['Piandao', 'Lion Turtle', 1], ['Iroh', 'Kuruk', 1], ['Iroh', 'Yangchen', 1], ['Iroh', 'Lion Turtle', 2], ['Kyoshi', 'Kuruk', 1], ['Kyoshi', 'Yangchen', 1], ['Kyoshi', 'Lion Turtle', 2], ['Chin', 'Kuruk', 1], ['Chin', 'Yangchen', 1], ['Chin', 'Azula', 1], ['Chin', 'Lion Turtle', 1], ['Kuruk', 'Yangchen', 1], ['Kuruk', 'Azula', 1], ['Kuruk', 'Lion Turtle', 1], ['Yangchen', 'Azula', 1], ['Yangchen', 'Lion Turtle', 1], ['Azula', 'Lion Turtle', 2], ['Suki', 'Lo', 1], ['Suki', 'Ursa', 1], ['Li', 'Piandao', 1], ['Li', 'Bumi', 1], ['Li', 'Jeong Jeong', 1], ['Long Feng', 'Lo', 1], ['Long Feng', 'Piandao', 1], ['Long Feng', 'Bumi', 1], ['Long Feng', 'Pakku', 1], ['Long Feng', 'Jeong Jeong', 1], ['Long Feng', 'Ursa', 1], ['Lo', 'Piandao', 1], ['Lo', 'Bumi', 1], ['Lo', 'Pakku', 1], ['Lo', 'Iroh', 1], ['Lo', 'Jeong Jeong', 1], ['Mai', 'Piandao', 1], ['Mai', 'Pakku', 1], ['Mai', 'Jeong Jeong', 1], ['Ty Lee', 'Piandao', 1], ['Ty Lee', 'Pakku', 1], ['Ty Lee', 'Jeong Jeong', 1], ['Piandao', 'Ursa', 1], ['Bumi', 'Ursa', 1], ['Pakku', 'Ursa', 1], ['Jeong Jeong', 'Ursa', 1], ['Suki', 'Hippo', 1], ['Suki', 'The Boulder', 1], ['Suki', 'Bato', 1], ['Suki', 'Pipsqueak', 1], ['Suki', 'The Mechanist', 1], ['Roku', 'Hippo', 1], ['Roku', 'The Boulder', 1], ['Roku', 'Ty Lee', 1], ['Roku', 'Teo', 1], ['Roku', 'The Mechanist', 1], ['Bumi', 'The Duke', 1], ['Bumi', 'Haru', 1], ['Bumi', 'Hakoda', 1], ['Bumi', 'Bato', 1], ['Bumi', 'Pipsqueak', 1], ['Bumi', 'Teo', 
1], ['Bumi', 'The Mechanist', 1], ['Lion Turtle', 'Mai', 1], ['Lion Turtle', 'The Duke', 1], ['Lion Turtle', 'Hippo', 1], ['Lion Turtle', 'The Boulder', 1], ['Lion Turtle', 'Haru', 1], ['Lion Turtle', 'Hakoda', 1], ['Lion Turtle', 'Bato', 1], ['Lion Turtle', 'Ty Lee', 1], ['Lion Turtle', 'Pipsqueak', 1], ['Lion Turtle', 'Teo', 1], ['Lion Turtle', 'The Mechanist', 1], ['The Duke', 'Ty Lee', 1], ['Hippo', 'Ty Lee', 1], ['The Boulder', 'Ty Lee', 1], ['Haru', 'Ty Lee', 1], ['Ty Lee', 'Pipsqueak', 1], ['Ty Lee', 'Teo', 1], ['Ty Lee', 'The Mechanist', 1]]
# len(classic_edges_list) is 2276 - 1





if skip_metrics == False:

    # change the edges_list input to analyse new metrics and graphs
    # true_edge_list -> reader method
    # classic_edges_list -> classical method

    el = true_edges_list
    # copy edges to modify them
    mod_edges_list = copy.deepcopy(el)

    # store all the characters present throughout the show
    show_characters = []
    for i in range(len(el)):
        if el[i][0] not in show_characters:
            show_characters.append(el[i][0])
        if el[i][1] not in show_characters:
            show_characters.append(el[i][1])

    # only necessary for simple reader
    ## remove characters from color dictionary if they don't have an interaction    
    #for i in range(len(show_characters)): 
    #    if list(color_dict.keys())[i] not in show_characters:
    #        del color_dict[list(color_dict.keys())[i]]
        

    new_color_list = sorted(color_dict.items())


    # create number:label relationship (alphabetical order); index is the vertex number of the respective label/character_name
    number_label = []
    for i in range(len(new_color_list)):
        number_label.append(new_color_list[i][0])

    print("********************************************************")
    #print(mod_edges_list)
    print("********************************************************")

    # replace names with numbers (vertex indexes) in mod_true_edges_list
    for i in range(len(mod_edges_list)):
        for j in range(len(number_label)):
            if mod_edges_list[i][0] == number_label[j]:
                mod_edges_list[i][0] = j
            if mod_edges_list[i][1] == number_label[j]:
                mod_edges_list[i][1] = j

    # typecast lists to tuples
    for t in range(len(mod_edges_list)):
        mod_edges_list[t] = tuple(mod_edges_list[t])

    print("********************************************************")
    #for i in range(len(mod_edges_list)):
    #    if len(mod_edges_list[i]) != 3:
    #        print(classic_edges_list[i])
    print("********************************************************")

    c_el = classic_edges_list
    # copy edges to modify them
    c_mod_edges_list = copy.deepcopy(c_el)

    # store all the characters present throughout the show
    show_characters = []
    for i in range(len(c_el)):
        if c_el[i][0] not in show_characters:
            show_characters.append(c_el[i][0])
        if c_el[i][1] not in show_characters:
            show_characters.append(c_el[i][1])

    # only necessary for simple reader
    ## remove characters from color dictionary if they don't have an interaction    
    #for i in range(len(show_characters)): 
    #    if list(color_dict.keys())[i] not in show_characters:
    #        del color_dict[list(color_dict.keys())[i]]
        

    new_color_list = sorted(color_dict.items())


    # create number:label relationship (alphabetical order); index is the vertex number of the respective label/character_name
    number_label = []
    for i in range(len(new_color_list)):
        number_label.append(new_color_list[i][0])

    print("********************************************************")
    #print(mod_edges_list)
    print("********************************************************")

    # replace names with numbers (vertex indexes) in mod_true_edges_list
    for i in range(len(c_mod_edges_list)):
        for j in range(len(number_label)):
            if c_mod_edges_list[i][0] == number_label[j]:
                c_mod_edges_list[i][0] = j
            if c_mod_edges_list[i][1] == number_label[j]:
                c_mod_edges_list[i][1] = j

    # typecast lists to tuples
    for t in range(len(c_mod_edges_list)):
        c_mod_edges_list[t] = tuple(c_mod_edges_list[t])

    print("********************************************************")
    #for i in range(len(mod_edges_list)):
    #    if len(mod_edges_list[i]) != 3:
    #        print(classic_edges_list[i])
    print("********************************************************")






    # create graph
    c_G = nx.Graph()
    c_G.add_weighted_edges_from(c_mod_edges_list)

    # labels of the vertices; name of characters
    labels = {}
    for node in list(c_G.nodes()):
        labels.update( {node : number_label[node]} )

    color_map = []
    # colors of the vertices in order of labels
    for key in labels:
        value = labels[key]
        color_map.append(color_dict[value])

    # replace fifth color with something that networkx understands
    for c in range(len(color_map)):
        if color_map[c] == "other":
            color_map[c] = "yellow"#(0.9, 0.9, 0.25)

    print("**********************************************************")

    options = {
            'labels': labels,
            'node_color': color_map,
            'node_size': 600,
            'width': 0.6,
            'font_size': 20,
            'font_color': (0.6, 0.6, 0.6),
            'edge_color': 'k'
    } 
    #####################################################################################
    #pos = nx.spring_layout(c_G)                                                        # don't draw edges' weights for classic
    #edge_weights = nx.get_edge_attributes(c_G, 'weight')                               # too much visual noise
    #####################################################################################
    # draw the graph
    nx.draw_networkx(c_G, with_labels=False, font_weight='bold', label='NetworkX', **options)
    plt.savefig("Avatar_Graph_method-1.svg", format="svg")
    plt.show()
    nx.draw_networkx(c_G, font_weight='bold', label='NetworkX', **options)
    #nx.draw_networkx_edge_labels(c_G, pos, edge_labels=edge_weights, font_size=10)
    plt.savefig("Avatar_Graph_method-1.svg", format="svg")
    plt.show()

    # create graph
    G = nx.Graph()
    G.add_weighted_edges_from(mod_edges_list)

    # labels of the vertices; name of characters
    labels = {}
    for node in list(G.nodes()):
        labels.update( {node : number_label[node]} )

    color_map = []
    # colors of the vertices in order of labels
    for key in labels:
        value = labels[key]
        color_map.append(color_dict[value])

    # replace fifth color with something that networkx understands
    for c in range(len(color_map)):
        if color_map[c] == "other":
            color_map[c] = "yellow"#(0.9, 0.9, 0.25)

    print("**********************************************************")

    options = {
            'labels': labels,
            'node_color': color_map,
            'node_size': 600,
            'width': 0.6,
            'font_size': 20,
            'font_color': (0.6, 0.6, 0.6),
            'edge_color': 'k'
    } 
    ####################################################################################
    pos = nx.spring_layout(G)
    edge_weights = nx.get_edge_attributes(G, 'weight')
    ####################################################################################
    # draw the graph
    nx.draw_networkx(G, with_labels=False, font_weight='bold', label='NetworkX', **options)
    plt.savefig("Avatar_Graph_method-2.svg", format="svg")
    plt.show()
    nx.draw_networkx(G, pos, font_weight='bold', label='NetworkX', **options)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights, font_size=10)
    plt.savefig("Avatar_Graph_method-2.svg", format="svg")
    plt.show()












    # # # # # # # # # #
    # Metrics Section #
    # # # # # # # # # #
    G_metrics = []

    # check if graph is connected
    #connected = nx.is_connected(G)
    #print("G is connected: ", connected)
    #print("G has this many vertices: ",len(G))
    #print("G has this many edges: ", G.number_of_edges())

    d_metric = []
    # getting degree METRIC
    degree = nx.degree_centrality(G)
    c_degree = nx.degree_centrality(c_G)

    #get_metric_dic(d_metric, degree, "Degree Centrality", "Method-A", "Centrality", "Percentage of vertices", number_label)
    #ccdf(degree)
    #G_metrics.append(d_metric)
    #print("degree", degree)
    #print("c_degree", c_degree)
    print("G degree passed.")
    #print(G_metrics)

    c_metric = []
    # getting distance(closeness) METRIC
    closeness = nx.closeness_centrality(G)
    c_closeness = nx.closeness_centrality(c_G)
    #get_metric_dic(c_metric, closeness, "Closeness", "Method-A", "Closeness", "Percentage of vertices", number_label)
    #G_metrics.append(c_metric)
    #print("closeness", closeness)
    #print("c_closeness", c_closeness)
    print("G closeness passed.")
    #print(G_metrics)

    clustering = nx.clustering(G)
    c_clustering = nx.clustering(c_G)


    #print("clustering", clustering)
    #print("c_clustering", c_clustering)

    degrees = G.degree()
    c_degrees = c_G.degree()

    print("degrees", degrees)
    print("c_degrees", c_degrees)

    """ cc_metric = []
    # getting number of connected components
    n_components = nx.number_connected_components(G)
    # getting connected components
    c_components = nx.connected_components(G)
    # getting size of connected components METRIC
    sizes = [len(c) for c in sorted(c_components, key=len, reverse=True)]
    cc_metric.append(min(sizes))
    cc_metric.append(max(sizes))
    cc_metric.append(statistics.mean(sizes))
    cc_metric.append(statistics.median(sizes))
    if(len(sizes) >= 2):
        cc_metric.append(statistics.stdev(sizes))
        # plot a nice drawing
        cdf = ECDF(sizes)
        plt.plot(cdf.x, cdf.y, label="Method-A CC sizes ECDF", marker=".", linestyle='none', markerfacecolor='none')
        plt.xlabel("CC", fontsize=18)
        plt.ylabel("Percentage of vertices", fontsize=16)
        plt.legend()
        plt.show()
    else:
        print("WARNING: No ECDF for Connected Components")
        cc_metric.append(0)
    G_metrics.append(cc_metric)
    print("G connected components passed.")
    #print(G_metrics) """


    b_metric = []
    # getting (shortest path) betweenness METRIC
    betweenness = nx.betweenness_centrality(G)
    c_betweenness = nx.betweenness_centrality(c_G)
    #get_metric_dic(b_metric, betweenness, "Betweenness", "G", "Betweenness", "Percentage of vertices", number_label)
    #G_metrics.append(b_metric)
    #print("betweenness", betweenness)
    #print("c_betweenness", c_betweenness)
    print("G betweenness passed.")
    #print(G_metrics)




    e_metric = []
    # getting edge METRIC
    edge_weights = [x[2]['weight'] for x in list(G.edges.data())]

    # all weights of the edges of the graph sorted in descending order
    weights = [c for c in sorted(edge_weights, reverse=True)]

    total_weight = 0
    for i in weights:
        total_weight += i

    print("NUMBER OF SCENES WITH DIALOGUE INTERACTIONS", total_weight)

    e_metric.append(min(weights))
    e_metric.append(max(weights))
    e_metric.append(statistics.mean(weights))
    e_metric.append(statistics.median(weights))
    if(len(weights) >= 2):
        e_metric.append(statistics.stdev(weights))
        # plot a nice drawing
        """ cdf = ECDF(weights)
        plt.plot(cdf.x, cdf.y, label="Method-A Edge Weights ECDF", marker=".", linestyle='none', markerfacecolor='none')
        plt.xlabel("Weights", fontsize=18)
        plt.ylabel("Percentage of edges", fontsize=16)
        plt.legend()
        plt.show() """
    else:
        print("WARNING: No ECDF for Edge Weights")
        e_metric.append(0)
    G_metrics.append(e_metric)
    top_20_w = weights[0:-1] #20
    top_20 = []
    for i in range(len(top_20_w)):
        for j in range(len(list(G.edges.data()))):
            if top_20_w[i] == list(G.edges.data())[j][2]['weight']:
                top_20.append([list(G.edges.data())[j][0], list(G.edges.data())[j][1], top_20_w[i]])

    for i in range(len(top_20)):
        for j in range(len(number_label)):
            if top_20[i][0] == j:
                top_20[i][0] = number_label[j]
            if top_20[i][1] == j:
                top_20[i][1] = number_label[j]
    print("Category: Edges' Weights")
    print("Top 20: ", top_20)    
    print("G edge weights passed.")
    

    print("\n##########################")
    #print("G metrics: \nfirst:[degree, distance(closeness), connected components' sizes, betweenness] \nsecond:[min, max, mean, median, standard deviation]\n")
    #print("degree centrality: ", G_metrics[0])
    #print("distance(closeness): ", G_metrics[1])
    #print("connected components' sizes: ", G_metrics[2])
    #print("betweenness: ", G_metrics[3])
    #print("edge weights: ", G_metrics[4])
    print("\n##########################")





































# legacy pseudo code below

"""
function detectInteraction(scene_sentence){
    if is dialogue{
        if vocative or similar{
            return [speaker, vocative]
        }else if pronoun{
            check for who was referenced
            return [speaker, referenced]
        }else if alias{
            get character[name]
            return [speaker, name]
        }else{
            return []
        }
    }else{//it's a description/narration
        check for characters //(pronouns, names or alias)
        check for s_verbs //special action verbs
        if characters with s_verbs{
            return [character1, character2]
        }else{
            return []
        }
    }
}


read transcript{
    segment the transcript in scenes using separators
    for each scene{
        //detecting new characters in the scene
        if detectNewCharacter(current_scene).length() > 0 {
            add new characters+color as a node to the graph
        }
        current_interactions = []
        for each scene_sentence{
            interaction = detectInteraction(scene_sentence)
            if interaction.size() > 0 {
                if interaction is not in current_interactions AND interaction.reverse() is not in current_interactions{ //new interaction
                    add an edge (weight 1) between the 2 nodes
                    current_interactions.push(interaction)
                }
            }
        }
        //adding edges and weights
        for i in current_interactions{
            if i in graph{
                i.value++
            }else if i.reverse() in graph{
                i.reverse()++
            }else{
                add i to the graph
            }
            
        }
    }	
}
"""