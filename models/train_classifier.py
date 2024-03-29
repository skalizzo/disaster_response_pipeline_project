import sys
import nltk
nltk.download(['punkt', 'wordnet', 'averaged_perceptron_tagger'])

import pandas as pd
import re
import numpy as np
import pickle
from sqlalchemy import create_engine

from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from sklearn.metrics import classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion
#from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.multioutput import MultiOutputClassifier


def load_data(database_filepath:str):
    """
    loads the data from the database in the given filepath
    :param database_filepath:
    :return: X (np.array), y (np.array), target category_names (list)
    """
    engine = create_engine(f'sqlite:///{database_filepath}')
    df = pd.read_sql(sql='SELECT * FROM messages;', con=engine)
    X = df['message'].values
    y = df.drop(['id', 'message', 'original', 'genre'], axis=1).values
    category_names = df.drop(['id','message','original','genre'], axis=1).columns
    return X, y, category_names

def tokenize(text)->[]:
    """
    turns a given text into tokens using a word-tokenizer and a lemmatizer;
    replaces URLs with a placeholder
    :param text:
    :return: clean_tokens (list)
    """
    url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    detected_urls = re.findall(url_regex, text)
    for url in detected_urls:
        text = text.replace(url, "urlplaceholder")

    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()

    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)

    return clean_tokens


def build_model():
    """
    building a pipeline for Natural Language Processing with a Multioutputclassifier
    :return: Pipeline
    """
    #RandomForestClassifier limited to max-depth=2 to make the program run faster
    # -->should use a higher parameter in production
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf', MultiOutputClassifier(RandomForestClassifier(max_depth=2)))
    ])
    #only a few parameters active to make GridSearch faster for the review
    parameters = {
        #'vect__ngram_range': ((1, 1), (1, 2)),
        #'vect__max_df': (0.5, 0.75, 1.0),
        # 'vect__max_features': (None, 5000, 10000),
        #'tfidf__use_idf': (True, False),
        'clf__estimator__n_estimators': [10, 50],
    }
    model = GridSearchCV(pipeline, param_grid=parameters, verbose=3)
    return model


def evaluate_model(model, X_test, Y_test, category_names):
    """
    prints a classification report including the precision, recall, F1 Score and accuracy
    for each category of the model
    :param model:
    :param X_test:
    :param Y_test:
    :param category_names:
    :return:
    """
    y_pred = model.predict(X_test)

    for colnr in range(y_pred.shape[1]):
        print('Category: ', category_names[colnr], '(weighted avg)--------------------------------------')
        print('Accuracy: {}'.format(np.mean(Y_test[:, colnr] == y_pred[:, colnr])))
        reportDict = classification_report(Y_test[:, colnr], y_pred[:, colnr], output_dict=True)
        weighted = reportDict['weighted avg']
        for key, value in weighted.items():
            print(f"{key}: {value}")
        print('------------------------------------------------')




def save_model(model, model_filepath):
    """
    saves model as pickle file to given filepath
    :param model: model that should be saved
    :param model_filepath: path where the file should be saved
    :return:
    """
    pickle._dump(model, open(model_filepath, "wb"))


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()