import os

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import json
import re
import string

import nltk
from keras.preprocessing.sequence import pad_sequences

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import \
    StopWordRemoverFactory

# from keras.preprocessing.sequence import pad_sequences

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Load slang words
def load_dataset_slang(path):
    with open(path, 'r') as file:
        slang_words = json.load(file)
    return slang_words

slang_words1 = load_dataset_slang('./slang/json_slang_words1')
slang_words2 = load_dataset_slang('./slang/json_slang_words2')
slang_words3 = load_dataset_slang('./slang/json_slang_words3')

def msg_preprocess_global(text):

    text = text.lower()

    text = re.sub(r'@', '', text)
    text = re.sub(r'#[A-Za-z0-9]+', '', text)
    text = re.sub(r'RT[\s]', '', text)
    text = re.sub(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", '', text)
    text = text.replace('/',' ')
    text = re.sub(r'\.+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text) 
    text = text.replace('\n', ' ')
    text = text.replace("'", "")
    text = text.replace(']','')
    text = text.replace('[','')
    text = text.replace(',',', ')
    text = text.replace('\\', ' ')
    text = text.replace('-',' ')
    text = text.translate(str.maketrans('', '', string.punctuation)) 
    text = text.strip() 

    words = text.split()
    for i, word in enumerate(words):
        if word in slang_words1.keys():
            words[i] = slang_words1[word]
        elif word in slang_words2.keys():
            words[i] = slang_words2[word]
        elif word in slang_words3.keys():
            words[i] = slang_words3[word]
    text = ' '.join(words)

    text = word_tokenize(text)

    factory = StemmerFactory()
    stemmer = factory.create_stemmer()
    stemmed_text = []
    for word in text:
        if word.lower() in ["asian", "basis", "solusi", "sufix"]:
            stemmed_text.append(word)
        elif word.lower() == "ngutang" or word.lower() == "utang":
            stemmed_text.append("hutang")
        elif word.lower() == "menemani":
            stemmed_text.append("teman")
        else:
            stemmed_text.append(stemmer.stem(word))

    stop_factory = StopWordRemoverFactory()
    stopword = stop_factory.get_stop_words()
    filtered = []
    for txt in stemmed_text:
        if txt not in set(stopword) or txt.lower() == 'tidak':
            filtered.append(txt)
    text = filtered

    text = ' '.join(text)
    return text

def url_preprocess_global(url):
    return url

def preprocess_char_level(text, tokenizer):
    X_cl_sequences = tokenizer.texts_to_sequences(text)
    X_cl_padded = pad_sequences(X_cl_sequences, padding='post', truncating='post', maxlen=1000)
    return X_cl_padded

def preprocess_word_level(text, tokenizer):
    X_wl_sequences =  tokenizer.texts_to_sequences(text)
    X_wl_padded = pad_sequences(X_wl_sequences, padding='post', truncating='post', maxlen=1000)
    return X_wl_padded

