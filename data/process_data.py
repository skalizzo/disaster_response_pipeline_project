import sys
import pandas as pd
from sqlalchemy import create_engine

def load_data(messages_filepath:str, categories_filepath:str)->pd.DataFrame:
    """
    function to load data from csv files
    :param messages_filepath: filepath to the messages.csv file as a string
    :param categories_filepath: filepath to the categories.csv file as a string
    :return: pd.DataFrame (merged Dataframe of both CSV-Files)
    """
    messages = pd.read_csv(messages_filepath)
    categories = pd.read_csv(categories_filepath)
    return pd.merge(left=messages, right=categories, on='id')



def clean_data(df:pd.DataFrame)->pd.DataFrame:
    """
    data wrangling: splits categories into usable columns, drops duplicates
    :param df: pd.DataFrame with messages and categories combined
    :return: pd.DataFrame (cleaned)
    """
    categories = df['categories'].str.split(';', expand=True)
    row = categories.iloc[0]
    category_colnames = row.apply(lambda x: x[:-2]).tolist()
    categories.columns = category_colnames
    for column in categories:
        categories[column] = categories[column].str[-1:]
        categories[column] = pd.to_numeric(categories[column])
    df.drop('categories', axis=1, inplace=True)
    df = pd.concat([df, categories], axis=1)
    df.drop_duplicates(keep='first', inplace=True)
    return df

def save_data(df:pd.DataFrame, database_filename:str):
    """
    saves data to an sqlite database
    :param df: data as pd.DataFrame
    :param database_filename: filename for the database (string)
    :return:
    """
    engine = create_engine(f'sqlite:///{database_filename}')
    df.to_sql('messages', engine, index=False)


def main():
    if len(sys.argv) == 4:

        messages_filepath, categories_filepath, database_filepath = sys.argv[1:]

        print('Loading data...\n    MESSAGES: {}\n    CATEGORIES: {}'
              .format(messages_filepath, categories_filepath))
        df = load_data(messages_filepath, categories_filepath)

        print('Cleaning data...')
        df = clean_data(df)
        
        print('Saving data...\n    DATABASE: {}'.format(database_filepath))
        save_data(df, database_filepath)
        
        print('Cleaned data saved to database!')
    
    else:
        print('Please provide the filepaths of the messages and categories '\
              'datasets as the first and second argument respectively, as '\
              'well as the filepath of the database to save the cleaned data '\
              'to as the third argument. \n\nExample: python process_data.py '\
              'disaster_messages.csv disaster_categories.csv '\
              'DisasterResponse.db')


if __name__ == '__main__':
    main()