import pandas as pd
import pickle

from sentence_transformers import SentenceTransformer


DATASET = "dataset.csv"


model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)



def create_embeddings():

    df = pd.read_csv(DATASET)


    documents = []


    for _, row in df.iterrows():

        text = f"""
        Disease:
        {row['Disease']}

        Symptoms:
        {row['Symptoms']}

        Causes:
        {row['Causes']}

        Prevention:
        {row['Prevention']}

        Treatment:
        {row['Treatment']}
        """

        documents.append(text)



    embeddings = model.encode(
        documents
    )


    with open(
        "medical_embeddings.pkl",
        "wb"
    ) as file:

        pickle.dump(
            {
                "documents":documents,
                "embeddings":embeddings
            },
            file
        )


    print(
        "Medical embeddings created successfully"
    )



if __name__=="__main__":

    create_embeddings()