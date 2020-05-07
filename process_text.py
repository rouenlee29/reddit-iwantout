import spacy  
import re
import en_core_web_sm
import string

from contractions import CONTRACTION_MAP
nlp = en_core_web_sm.load()


def expand_contractions(text, contraction_mapping=CONTRACTION_MAP):
    
    contractions_pattern = re.compile('({})'.format('|'.join(contraction_mapping.keys())), 
                                      flags=re.IGNORECASE|re.DOTALL)
    def expand_match(contraction):
        match = contraction.group(0)
        first_char = match[0]
        expanded_contraction = contraction_mapping.get(match)\
                                if contraction_mapping.get(match)\
                                else contraction_mapping.get(match.lower())                       
        expanded_contraction = first_char+expanded_contraction[1:]
        return expanded_contraction
        
    expanded_text = contractions_pattern.sub(expand_match, text)
    expanded_text = re.sub("'", "", expanded_text)
    return expanded_text

def remove_special_characters(text, remove_digits=True):
    pattern = r'[^a-zA-z0-9]' if not remove_digits else r'[^a-zA-z]'
    text = re.sub(pattern, '', text)
    return text

def my_tokeniser(text):
    cleaned = remove_special_characters(expand_contractions(text))
    
    split = cleaned.split(" ")
    tokenised = []
    for s in split:
        if s.strip() != '':
            tokenised.append(s.strip())
    return tokenised

def spacy_tokeniser(text):
  
    text = text.lower().strip()
    processed_tokens = []
    tokens = nlp(text)
    for token in tokens:
        if (token.is_stop or token.is_punct):
            continue
        else:
            processed_tokens.append(token.lemma_)

    return processed_tokens

# taken from fast.ai
re_tok = re.compile(f'([{string.punctuation}“”¨«»®´·º½¾¿¡§£₤‘’])')
def tokenize(s): return re_tok.sub(r' \1 ', s).split()