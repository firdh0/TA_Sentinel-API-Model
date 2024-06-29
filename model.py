import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import json
import keras
import tensorflow as tf

# from gcs import load as download_models
from preprocess import (preprocess_char_level, preprocess_word_level, msg_preprocess_global, url_preprocess_global)
from tensorflow.keras.preprocessing.text import tokenizer_from_json

# from keras_preprocessing.text import tokenizer_from_json
# from keras._tf_keras.keras.preprocessing.sequence import pad_sequences
# from keras.preprocessing.sequence import pad_sequences

def load_model(path_to_model):
    return keras.models.load_model(path_to_model)

def load_tokenizer(path):
    with open(path, 'r', encoding='utf-8') as f:
        tokenizer_config = json.load(f)
    return tokenizer_from_json(tokenizer_config)

def initialize_models():
    # model_files = [
    #     './model/message_model.h5',
    #     './model/url_model.h5',
    #     './tokenizer/message/msg_tokenizer_char_level.json',
    #     './tokenizer/message/msg_tokenizer_word_level.json',
    #     './tokenizer/url/url_tokenizer_char_level.json',
    #     './tokenizer/url/url_tokenizer_word_level.json'
    # ]

    # Ensure all necessary files are present
    # for file in model_files:
    #     if not os.path.exists(file):
    #         download_models()
    #         break

    msg_model = load_model('./model/message_model.h5')
    url_model = load_model('./model/url_model.h5')

    msg_tokenizer_char_level = load_tokenizer('./tokenizer/message/msg_tokenizer_char_level.json')
    msg_tokenizer_word_level = load_tokenizer('./tokenizer/message/msg_tokenizer_word_level.json')
    url_tokenizer_char_level = load_tokenizer('./tokenizer/url/url_tokenizer_char_level.json')
    url_tokenizer_word_level = load_tokenizer('./tokenizer/url/url_tokenizer_word_level.json')

    return {
        'msg_model': msg_model,
        'url_model': url_model,
        'msg_tokenizer_char_level': msg_tokenizer_char_level,
        'msg_tokenizer_word_level': msg_tokenizer_word_level,
        'url_tokenizer_char_level': url_tokenizer_char_level,
        'url_tokenizer_word_level': url_tokenizer_word_level
    }

models = initialize_models()

def message_prediction(text_phishing):
    msg_model = models['msg_model']
    msg_tokenizer_char_level = models['msg_tokenizer_char_level']
    msg_tokenizer_word_level = models['msg_tokenizer_word_level']

    text_clean = [msg_preprocess_global(text) for text in text_phishing]
    text_char_level = preprocess_char_level(text_clean, msg_tokenizer_char_level)
    text_word_level = preprocess_word_level(text_clean, msg_tokenizer_word_level)

    predictions_prob = msg_model.predict([text_char_level, text_word_level])
    predictions = (predictions_prob > 0.5).astype(int)

    results = []
    for prob, pred in zip(predictions_prob, predictions):
        results.append({
            "smishing_probability": float(prob[0]),
            "is_smishing": bool(pred[0])
        })

    return results

def url_prediction(url_phishing):
    url_model = models['url_model']
    url_tokenizer_char_level = models['url_tokenizer_char_level']
    url_tokenizer_word_level = models['url_tokenizer_word_level']

    url_clean = [url_preprocess_global(url) for url in url_phishing]
    url_char_level = preprocess_char_level(url_clean, url_tokenizer_char_level)
    url_word_level = preprocess_word_level(url_clean, url_tokenizer_word_level)

    predictions_prob = url_model.predict([url_char_level, url_word_level])
    predictions = (predictions_prob > 0.5).astype(int)

    results = []
    for prob, pred in zip(predictions_prob, predictions):
        results.append({
            "phishing_probability": float(prob[0]),
            "is_phishing": bool(pred[0])
        })

    return results