import sqlite3

def creer_base_de_donnees():
    # Connexion à la base de données (le fichier sera créé s'il n'existe pas)
    conn = sqlite3.connect('statistiques_midget.db')
    cursor = conn.cursor()

    # 1. Table des Joueurs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS joueurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prenom TEXT NOT NULL,
        nom TEXT NOT NULL,
        numero_dossard INTEGER
    )
    ''')

    # 2. Table des Parties
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_match DATE NOT NULL,
        equipe_adverse TEXT NOT NULL,
        lieu TEXT,
        type_match TEXT -- ex: Saison régulière, Tournoi, Séries
    )
    ''')

    # 3. Table des Présences au bâton (La grille de pointage)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS presences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partie_id INTEGER,
        joueur_id INTEGER,
        manche INTEGER NOT NULL,
        
        -- Le code officiel de Baseball Québec (ex: S, D, BB, K, 6-3, F7)
        code_resultat TEXT NOT NULL, 
        
        -- Statistiques découlant de la présence
        point_marque BOOLEAN DEFAULT 0,  -- 1 si le losange est colorié
        points_produits INTEGER DEFAULT 0, -- RBI
        buts_voles INTEGER DEFAULT 0,
        
        FOREIGN KEY (partie_id) REFERENCES parties (id),
        FOREIGN KEY (joueur_id) REFERENCES joueurs (id)
    )
    ''')

    # Sauvegarder et fermer
    conn.commit()
    conn.close()
    print("La base de données SQLite 'statistiques_midget.db' a été créée avec succès !")

# Exécuter la fonction
creer_base_de_donnees()