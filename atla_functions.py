from atla_nonalias import nonalias_list # contains proper nouns that are NOT character names or alias
from atla_alias import alias_dict       # contains all characters of the show and their known alias
from atla_color import color_dict       # contains all characters of the show and their respective colors



def aliasOrName(noun):
    """
    noun -> some string
    checks if noun is either a name or an alias for a character.
    returns a list with the name and a list of aliases [name, [alias1, alias2, ...]]
    """
    character = []
    for name, aliases in alias_dict.items(): # check each character-aliases pair for the noun
        if ((noun == name) or (noun in aliases)): # character introduced by name or alias
            character = [name, aliases]  # character = ["name",["alias1", "alias2", ...]]
            return character

    return character



def detectProperNouns(phrase):
    """
    phrase -> a simple transcrtipt text string
    gets a string of words and returns a list with characters names and composite names (proper nouns)
    """
    # split phrase in words by spaces 
    word_set = phrase.split()
    p_proper_nouns = [] # possible proper nouns
    proper_nouns = []

    for w in range(len(word_set)): # check each word
        if word_set[w][0].isupper(): # check for first capital letter
            temp_noun = ""
            for i in range(5): # arbitrary limit for proper noun word count
                try:
                    if word_set[w+i][0].isupper(): # proper noun
                        if word_set[w+i][-1].isalpha(): # check for last character
                            temp_noun = temp_noun+word_set[w+i]+" "
                        else: # terminates nouns on punctuation marks e.g. "," ";" "!" etc. also assumes punctuation marks the end of noun
                            temp_noun = temp_noun+word_set[w+i]+" "
                            break
                    else:
                        break
                except:
                    #print("Phrase:", phrase)
                    #print("Word Set:", word_set)
                    #print("w:",w)
                    #print("Error. Probably out of index.")
                    pass
            # exclude final space and add proper noun
            temp_noun = temp_noun[0:-1]
            p_proper_nouns.append(temp_noun)

    # check if proper nouns are non alias
    for n in p_proper_nouns:
        if n in p_proper_nouns and n not in nonalias_list:
            proper_nouns.append(n)

    return proper_nouns


###################################
# probably not gonna use this one #
###################################

def detectNewCharacter(current_scene, current_characters):
    """
    current_scene -> something treated from an html request
    reads a scene and determines if there are new characters
    return a list of said characters with their aliases
    """
    p_new_characters = [] # possible new characters
    new_characters = []   # definitely new characters

    # save proper nouns of the current_scene in a list
    scene_proper_nouns = detectProperNouns(current_scene)

    # remove punctuation marks from elements
    for i in range(len(scene_proper_nouns)):
        if not(scene_proper_nouns[i][-1].isalpha()):
            scene_proper_nouns[i] = scene_proper_nouns[i][0:-1]

    # proper_noun are strings with initial capital letters like: 'Katara', 'Aang', 'Avatar Aang', 'Toph', 'The Blind Bandit'
    for proper_noun in scene_proper_nouns:
        if len(aliasOrName(proper_noun)) > 0:
            p_new_characters.append(aliasOrName(proper_noun))
            continue
        else:
            # no corresponding character name nor alias
            print("#############################################")
            print("#############################################")
            print("possible new alias found in: "+current_scene)
            print("alias candidate: "+proper_noun)
            print("#############################################")
            print("#############################################")

    # check if characters mentioned now have already been mentioned before
    for n in p_new_characters:
        if n in p_new_characters and n not in current_characters:
            new_characters.append(n)

    return new_characters


def nextSpeaker(scene, sentence):
    """
    scene -> a single scene from an episode
    sentence -> current sentence being read
    returns the name of the next character that will speak
    """
    reference_point = scene.index(sentence)
    if reference_point == len(scene)-1:
        return ""
    else:
        # find speaker
        beginning_speaker = scene[reference_point+1].find("<b>") + len("<b>")
        end_speaker = scene[reference_point+1].find("</b>", beginning_speaker)
        speaker = scene[reference_point+1][beginning_speaker:end_speaker]
        # find speaker's character
        speaker_character = aliasOrName(speaker)
        return speaker_character[0]


    

def detectNameVocative(phrase, previous_speaker, next_speaker):
    """
    phrase -> a simple transcrtipt text string
    gets a string of words and returns a list of "name vocatives" used by a speaker.
    "name vocatives" are references used by a speaker (A) to refer to someone spoken to (B) by using their (B) name
    """
    # split phrase in words by spaces 
    word_set = phrase.split()
    name_vocatives = []
    p_name_vocatives = [] # possible name vocatives
    punctuation_marks = ['!', '?', '.', ',']
    direct_pronouns = ["you", "yourself", "you guys", "yourselves"]
    proper_nouns = detectProperNouns(phrase)
    

    # check for proper nouns vocatives that are names or alias and save those characters
    # assumes that "Katara, [...]" "[...] Katara!" "[...] Katara?" "[...], Katara." are all vocatives
    for v in proper_nouns:
        if v[-1] in punctuation_marks: # likely a vocative
            if len(aliasOrName(v[0:-1])) > 0:
                p_name_vocatives.append(aliasOrName(v[0:-1])[0])


    if len(word_set) == 1: # isolate word
        # check if isolate is a name or alias; excludes full stop
        if len(aliasOrName(word_set[0][0:-1])) > 0:
            name_vocatives.append(aliasOrName(word_set[0][0:-1])[0])
        """ 
        for character in p_name_vocatives: # characters
            for alias in character[1]: # aliases
                if (word_set[0][0:-1] == character[0]) or (word_set[0][0:-1] == alias):
                    name_vocatives.append(word_set[0][0:-1]) """
    else: 
        for i in range(len(word_set)):
            """ # search for names separated by an "and" word. assumes those characters are being spoken to
            if word_set[i] == 'and':
                try:# Name1 and Name2
                    if word_set[i-1][-1].isalpha() and word_set[i+1][-1].isalpha():
                        if aliasOrName(word_set[i-1]) > 0 and aliasOrName(word_set[i+1]) > 0:
                            name_vocatives.append(aliasOrName(word_set[i-1])[0])
                            name_vocatives.append(aliasOrName(word_set[i+1])[0])
                    elif word_set[i-1][-1].isalpha() and word_set[i+1][-1] in punctuation_marks:
                        if aliasOrName(word_set[i-1]) > 0 and aliasOrName(word_set[i+1][0:-1]) > 0:
                            name_vocatives.append(aliasOrName(word_set[i-1])[0])
                            name_vocatives.append(aliasOrName(word_set[i+1][0:-1])[0])
                except:
                    print("Error. Probably out of index.") """

            # search for direct pronouns. assumes they reference the immediate last character of the scene
            if word_set[i] in direct_pronouns:
                # check if there is a next_character; assume it was referenced by direct_pronouns
                if next_speaker != "":
                    name_vocatives.append(next_speaker)
                # otherwise check if there was a previous character; assume it was referenced by direct_pronouns
                elif previous_speaker != "":
                    name_vocatives.append(next_speaker)

    return (p_name_vocatives)




def sceneSentenceSeparator(scene):
    """
    scene -> a subdivision of the original transcript
    gets a scene as string and returns its Scene Sentences.
    a Scene Sentence is defined by any characters inbetween two '<br>'
    """
    marker = "<br/>" # originally '<br>'. BeautifulSoup transforms it in '<br/>'
    scene_sentences = []

    # first clean up
    # check for <i>, if it exists, the parser has failed and this section must be invalidated
    i = 0
    while(i < 100):
        i_beginning_check = scene.find("<i>")
        i_end_check = scene.find("</i>") + len("</i>")
        if i_beginning_check == -1 and i_end_check == -1: # clean up done
            break
        else: # clean up
            scene = scene.replace(scene[i_beginning_check - len("<i>"):i_end_check + len("</i>")], "", 1)
        i += 1
    # second clean up
    # check for (), leftover from sceneSeparator
    scene = scene.replace("()", "")

    i = 0
    beginning = 0
    while(i < 100):
        # find the next marker
        end = scene.find(marker,beginning)
        # add the string inbetween markers if it's not empty; at least contains <b></b> garanteeing a speaker
        if(len(scene[beginning:end]) >= 7):
            scene_sentences.append(scene[beginning:end])
        
        scene = scene[end+len(marker):]
        # find the first marker, go past it
        #beginning = scene.find(marker) + len(marker)
        i += 1

    scene_sentences = [s for s in scene_sentences if s[0:3] == "<b>"]
    
    return scene_sentences


def containsSceneMarkers(narration, narration_markers):
    """
    narration -> a string starting with <i> and ending with </i>
    narration_markers -> list of strings
    returns True if the narration contains at least one element from narration_markers
    """

    if any(word in narration for word in narration_markers):
        return True
    else:
        return False



def sceneSeparator(episode):
    """
    episode -> the entire string transcript of an episode
    gets an episode as a "soup" string and returns its Scenes.
    a Scene is defined by any characters inbetween the pre-defined markers:
    { Act I, Act II, Act III, Cut, cuts, (Cut, Scene cuts, Scene cuts, fade to, fades to, Fade to, cut back, [End Credits] }
    """
    #i_begin_marker = "<i>"
    #i_end_marker = "</i>"
    # markers inbetween <i> and </i>
    # it's assumed that these markers only occur inbetween <i> and </i> outside of dialogue
    i_narration_markers = [
                    "Cut", "Cuts", 
                    "cut", "cuts",
                    "cut to", "cuts to",
                    "Scene cuts", "Scene cut", 
                    "Fade back", "Fades back",
                    "fade back", "fades back",
                    "fade to", "fades to", 
                    "Fade to", "Fades to", 
                    "cut back", "cuts back",
                    "Shot cut", "Shot cuts",
                    "shot cut", "shot cuts",
                    "Switch to", "Switches to",
                    "switch to", "switches to",
                    "Commercial break", "commercial break",
                    "Show returns", "Show return",
                    "show returns", "show return",
                    "Flashback ends",
                    "Scene opens", "scene opens",
                    "Scene ends", "scene ends",
                    "Scene changes", "scene changes",
                    "Camera switches", "camera switches",
                    "POV changes",
                    "Scene shifts", "scene shifts"
                ]
    # markers inbetween <u><b> and </b></u>; all episodes must begin with the Act I marker
    ub_markers = ["<u><b>Act I</b></u>", "<u><b>Act II</b></u>", "<u><b>Act III</b></u>"]
    # all episodes must end with this marker
    final_marker = "[End Credits]"

    # all episodes contain these four markers
    Act_I = episode.find(ub_markers[0]) + len(ub_markers[0])
    Act_II = episode.find(ub_markers[1]) + len(ub_markers[1])
    Act_III = episode.find(ub_markers[2]) + len(ub_markers[2])
    Credits = episode.find(final_marker)

    # generate 3 subsets of scenes Act I scenes, Act II scenes and Act III scenes
    episode_part_I = episode[Act_I:Act_II]
    episode_part_II = episode[Act_II:Act_III]
    episode_part_III = episode[Act_III:Credits]
  
    # replace scenes with markers, and delete scenes without markers

    # loop through act I
    i_beginning = 0
    i_end = 0
    i = 0 
    while(i < 200):
        contains = False
        # find the first marker, go past it
        i_beginning = episode_part_I.find("<i>", i_end) + len("<i>")
        # find the next marker
        i_end = episode_part_I.find("</i>", i_beginning)
        # check if narration part has i_narration_marker
        if(len(episode_part_I[i_beginning:i_end]) != 0):
            contains = containsSceneMarkers(episode_part_I[i_beginning:i_end], i_narration_markers)

        # new scene has begun, replace it with general marker
        if contains == True:
            #episode_part_I = episode_part_I[0:i_beginning - len("<i>")] + "<scene_marker>" + episode_part_I[i_end + len("</i>"):]       
            episode_part_I = episode_part_I.replace(episode_part_I[i_beginning - len("<i>"):i_end + len("</i>")], "<scene_marker>", 1) 
        # narration with no markers, 'delete' it
        else:
            #episode_part_I = episode_part_I[0:i_beginning - len("<i>")] + episode_part_I[i_end + len("</i>"):]
            episode_part_I = episode_part_I.replace(episode_part_I[i_beginning - len("<i>"):i_end + len("</i>")], "", 1)
        
        i += 1

    
    # loop through act II
    i_beginning = 0
    i_end = 0
    i = 0 
    while(i < 200):
        contains = False
        # find the first marker, go past it
        i_beginning = episode_part_II.find("<i>", i_end) + len("<i>")
        # find the next marker
        i_end = episode_part_II.find("</i>", i_beginning)
        # check if narration part has i_narration_marker
        if(len(episode_part_II[i_beginning:i_end]) != 0):
            contains = containsSceneMarkers(episode_part_II[i_beginning:i_end], i_narration_markers)

        # new scene has begun, replace it with general marker
        if contains == True:
            #episode_part_I = episode_part_I[0:i_beginning - len("<i>")] + "<scene_marker>" + episode_part_I[i_end + len("</i>"):]       
            episode_part_II = episode_part_II.replace(episode_part_II[i_beginning - len("<i>"):i_end + len("</i>")], "<scene_marker>", 1) 
        # narration with no markers, 'delete' it
        else:
            #episode_part_I = episode_part_I[0:i_beginning - len("<i>")] + episode_part_I[i_end + len("</i>"):]
            episode_part_II = episode_part_II.replace(episode_part_II[i_beginning - len("<i>"):i_end + len("</i>")], "", 1)
        
        i += 1

    # loop through act III
    i_beginning = 0
    i_end = 0
    i = 0 
    while(i < 200):
        contains = False
        # find the first marker, go past it
        i_beginning = episode_part_III.find("<i>", i_end) + len("<i>")
        # find the next marker
        i_end = episode_part_III.find("</i>", i_beginning)
        # check if narration part has i_narration_marker
        if(len(episode_part_III[i_beginning:i_end]) != 0):
            contains = containsSceneMarkers(episode_part_III[i_beginning:i_end], i_narration_markers)

        # new scene has begun, replace it with general marker
        if contains == True:
            #episode_part_I = episode_part_I[0:i_beginning - len("<i>")] + "<scene_marker>" + episode_part_I[i_end + len("</i>"):]       
            episode_part_III = episode_part_III.replace(episode_part_III[i_beginning - len("<i>"):i_end + len("</i>")], "<scene_marker>", 1) 
        # narration with no markers, 'delete' it
        else:
            #episode_part_I = episode_part_I[0:i_beginning - len("<i>")] + episode_part_I[i_end + len("</i>"):]
            episode_part_III = episode_part_III.replace(episode_part_III[i_beginning - len("<i>"):i_end + len("</i>")], "", 1)
        
        i += 1
            

    # get the scenes
    episode_scenes = []
    parts = [episode_part_I, episode_part_II, episode_part_III]
    for part in parts:
        i = 0
        while(i < 500):
            # find the first marker, go past it
            beginning = part.find("<scene_marker>") + len("<scene_marker>")
            # find the next marker
            end = part.find("<scene_marker>", beginning)
            # add the string inbetween markers if it's not empty
            if(len(part[beginning:end]) != 0):
                episode_scenes.append(part[beginning:end])

            part = part[end:]
            i+=1


    return episode_scenes





def detectSpeakerInteraction(scene_sentence, previous_speaker, next_speaker):
    """
    scene_sentence -> string, a single "sentence" of a scene
    previous_speaker -> last character that has spoken
    next_speaker -> next character that will speak
    returns a list of strings containing the speaker of the interaction, and the characters spoken to in this format [speaker_name, [character001_name, character002_name, ...]]
    returns empty if it is an invalid sentence
    """

    """ # check for <i>, if it exists, the parser has failed and this section won't be valid
    i_check = scene_sentence.find("<i>")
    if i_check == -1:
        return [] """

    # find speaker
    beginning_speaker = scene_sentence.find("<b>") + len("<b>")
    end_speaker = scene_sentence.find("</b>")
    speaker = scene_sentence[beginning_speaker:end_speaker]
    # find speaker's character
    speaker_character = aliasOrName(speaker)

    # find vocatives
    vocatives = detectNameVocative(scene_sentence[end_speaker+len("</b>"):], previous_speaker, next_speaker)
    # find vocatives' characters
    """ vocative_characters = []
    for v in vocatives:
        if len(aliasOrName(v)) > 0:
            vocative_characters.append(aliasOrName(v)[0]) """

    """     final_vocatives = []
        for vc in vocative_characters:
            final_vocatives.append(vc)
    """
    # check if there were any vocatives
    result = []
    if len(vocatives) != 0 and len(speaker_character)>0:
        result.append(speaker_character[0])
        result.append(vocatives)
    
    return result