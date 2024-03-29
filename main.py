from flask import Flask, request
from neo4j import GraphDatabase
from flask_cors import CORS
import json
import datetime

app = Flask(__name__) #créer une instance de la classe flask et initialise l'application
CORS(app)
#CORS(app, resources={r"/store_data": {"origins": "https://localhost:53000"}})

with open('config.json','r') as json_file:
    config = json.load(json_file)
uri = config['uri']
username = config['username']
password = config['password']

driver = GraphDatabase.driver(uri, auth=(username, password)) #initialise le driver neo4j

proposition = "Proposition Anonyme"
@app.route('/store_data', methods=['POST'])
def store_data():
    data = request.get_json()
    date = data.get('date')
    manager = data.get('manager')
    feedback = data.get('feedback')
    month = data.get('month')
    year = data.get('year')
    time = data.get('time')
    person = data.get('person')
    categorie = data.get('selectedImageTitle')
    champs = data.get('selectedText')

    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        with driver.session() as session:
            # Vérification de l'existence du nœud année
            year_exists = session.run("MATCH (annee:Annee {annee: $year}) RETURN COUNT(annee) AS count", year=year).single()[
                "count"] > 0

            # Vérification de l'existence du nœud mois
            month_exists = session.run("MATCH (mois:Mois {mois: $month}) RETURN COUNT(mois) AS count", month=month).single()[
                "count"] > 0

            # Vérification de l'existence du nœud personne
            person_exists = session.run("MATCH (personne:Personne {name: $person}) RETURN COUNT(personne) AS count",
                                        person=person).single()["count"] > 0

            # Création des nœuds si nécessaire
            if not year_exists:
                session.run("CREATE (annee:Annee {annee: $year})", year=year)

            if not month_exists:
                session.run("CREATE (mois:Mois {mois: $month})", month=month)

            if not person_exists:
                session.run("CREATE (personne:Personne {name: $person})", person=person)

            # Création du nœud Status avec les liens vers les nœuds existants ou nouvellement créés
            session.run("CREATE (status:Status {categorie: $categorie, champs: $champs ,date: $date, manager: $manager, time: $time}) "
                        "WITH status "
                        "MATCH (personne:Personne {name: $person}) "
                        "MATCH (annee:Annee {annee: $year}) "
                        "MATCH (mois:Mois {mois: $month}) "
                        "CREATE (status)-[:EST_ASSOCIE_A]->(personne) "
                        "CREATE (status)-[:EST_EN_ANNEE]->(annee) "
                        "CREATE (status)-[:EST_EN_MOIS]->(mois)",

                        categorie=categorie, champs=champs, date=date, manager=manager, time=time, person=person,
                        year=year, month=month)
            if len(feedback) != 0:
                session.run("CREATE (proposition:Proposition {proposition: $proposition, feedback: $feedback})",
                            proposition=proposition, feedback=feedback)
                session.run("MATCH(proposition:Proposition {proposition: $proposition, feedback: $feedback}),"
                            "(annee:Annee {annee: $year}),"
                            "(mois:Mois {mois: $month})"
                            "CREATE (proposition)-[:EST_EN_MOIS]->(mois),"
                            "(proposition)-[:EST_EN_ANNEE]->(annee)", proposition=proposition, feedback=feedback,
                            month=month, year=year)

    print('Champs textes stockés avec succès')
    return 'Champs textes stockés avec succès'


if __name__ == '__main__':
    app.run(debug=True)




