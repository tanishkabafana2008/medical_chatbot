import pandas as pd


class MedicalKnowledge:


    def __init__(self):

        self.diseases = pd.read_csv(
            "data/diseases.csv"
        )

        self.medicines = pd.read_csv(
            "data/medicines.csv"
        )

        self.symptoms = pd.read_csv(
            "data/symptoms.csv"
        )

        self.first_aid = pd.read_csv(
            "data/first_aid.csv"
        )

        self.nutrition = pd.read_csv(
            "data/nutrition.csv"
        )


    def get_all_documents(self):

        documents=[]


        for _,row in self.diseases.iterrows():

            documents.append(
                f"""
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
            )


        for _,row in self.medicines.iterrows():

            documents.append(
                f"""
                Medicine:
                {row['Medicine']}

                Uses:
                {row['Uses']}

                Side Effects:
                {row['Side_Effects']}

                Warnings:
                {row['Warnings']}
                """
            )


        return documents