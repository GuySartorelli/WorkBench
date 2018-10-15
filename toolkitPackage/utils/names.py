"""
Utilities for handling complex renaming such as adding or removing prefixes/suffixes. Deals directly with strings.

NOTE: Still need to include options for different numbers of affixes for at least keepAffixes.
"""

from toolkitPackage.converter.commands import warning, error

def stripAffix(name='', prefix=True, suffix=True, returnUnderscore=True):
    """
    function for stripping prefixes and suffixes from object names
    
    @param name: str, name of object from which to strip affixes
    @param prefix: bool, determines whether to strip the prefix
    @param suffix: bool, determines whether to strip the suffix
    @param returnUnderscore: bool, determines whether to return affixes with underscores
    @return: list[str], stripped name, prefix, suffix
    """
    # split string by underscores and create empty affixes to return
    strippedName = name.split('_')
    strippedSuffix = ''
    strippedPrefix = ''
    
    # pop off affixes
    if len(strippedName) > 1:
        if prefix == True:
            strippedPrefix = strippedName.pop(0)
    if len(strippedName) > 1:
        if suffix == True:
            strippedSuffix = strippedName.pop(-1)
    
    # add underscores to affixes if appropriate
    if returnUnderscore == True:
        strippedPrefix = strippedPrefix + '_'
        strippedSuffix = '_' + strippedSuffix
    
    # revert affixes to empty strings if only underscore
    if strippedPrefix is '_':
        strippedPrefix = ''
    if strippedSuffix is '_':
        strippedSuffix = ''
    
    # return list of new name and affixes
    nameList = ['_'.join(strippedName), strippedPrefix, strippedSuffix]
    return nameList


def keepAffixes(name, newName, keepPrefix=True, keepSuffix=True, incrementChars=None):
    """
    function for renaming objects but keeping their affixes
    
    @param name: str, name of object to keep its affixes
    @param newName: str, new name for object (without affixes)
    @param keepPrefix: bool, keep or drop prefix
    @param keepSuffix: bool, keep or drop suffix
    @return: str, new name of object with affixes intact
    """
    #strip Affixes (note: might not yet allow for not having an affix)
    prefix, suffix = stripAffix(name)[1:3]
    if keepPrefix == False:
        prefix = ''
    if keepSuffix == False:
        suffix = ''
    #join affixes to new name
    newNameToJoin = [prefix, newName, suffix]
    newNameJoined = ''.join(newNameToJoin)
    return newNameJoined


def generateDelimiters(delimiter):
    '''
    function for generating incremental characters (or 'delimiters') for renaming multiple objects
    
    @param delimiter: str or int, starting incremental character
    @param numObj: number of objects to rename
    @param numChars: minimum number of digits for each increment character (NOT YET SUPPORTED) 
    @return: list[str], incremental characters for all objects to rename  
    '''
    #if using float, convert to int
    if isinstance(delimiter, float):
        delimiter = int(delimiter)
        warning("converting delimiter from float")
    
    #if using integers, just yield that
    if isinstance(delimiter, int):
        while True:
            yield str(delimiter)
            delimiter += 1
    
    elif isinstance(delimiter, str):
        #charsInAlphabet is the remaining number of characters in the alphabet after the original delimiter
        #ordStarter is a lower-case 'a' or upper-case 'A' depending on the case of the original delimiter
        ordValue = ord(delimiter)
        if 64 < ordValue < 91:
            charsInAlphabet = 26 - ordValue + 65
            ordStarter = 65 #uppercase A
        elif 96 < ordValue < 123:
            charsInAlphabet = 26 - ordValue + 97
            ordStarter = 97 #lowercase a
        
        char1 = ''
        char2Iterations = 0
        char1Iterations = 0
        totalIterations = 0
        
        #676 is enough for this to run through AA to ZZ
        while totalIterations < 676:
            #if char2 gets to Z, increase char1
            if char2Iterations > charsInAlphabet:
                char1 = chr(char1Iterations + ordStarter)
                ordValue = ordStarter
                char1Iterations += 1
                char2Iterations = 0
                charsInAlphabet = 26
           
            while char2Iterations < charsInAlphabet:
                char2 = chr(char2Iterations + ordValue)
                char2Iterations += 1
                totalIterations += 1
                yield char1+char2
    #if not str or int
    else:
        raise TypeError( "{0} is not currently supported as a delimiter character type. Please use int or str.".format(type(char)) )