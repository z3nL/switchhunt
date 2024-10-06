from pymongo import MongoClient

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import pandas as pd

import os
database_url = os.getenv('DATABASE_URL')
client = MongoClient(database_url)
db = client['Learning']
collection = db['Learning_Collection']
documents = collection.find()  # Fetch all documents
data_list = []  # List to store the data
for document in documents:
    data_list.append(document)  # Append each document to the list
df = pd.DataFrame(data_list)



print(df.head())


# Drop the '_id' column if it's not needed


print(df.head())



from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(max_features=500)  # Limit the number of features to avoid overfitting
description_vectors = vectorizer.fit_transform(df['description'])

from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
df['amount_normalized'] = scaler.fit_transform(df[['amount']])


from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()
df['transaction_type_encoded'] = label_encoder.fit_transform(df['transaction_type'])


import pandas as pd

# One-hot encode the 'transaction_type' column
df_one_hot_encoded = pd.get_dummies(df, columns=['transaction_type'])

# This will create separate binary columns for each unique value in 'transaction_type'
print(df_one_hot_encoded.head())
