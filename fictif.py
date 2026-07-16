import sqlite3
from datetime import date

def simuler_premiere_manche():
    # 1. Connexion à la base de données existante
    conn = sqlite3.connect('statistiques_midget.db')
    cursor = conn.cursor()

    # 2. Insertion de l'alignement de départ (9 joueurs fictifs)
    alignement_fictif = [
        ("Julien", "Gravel", 24),    # Frappeur 1
        ("Mathieu", "Lavoie", 11),   # Frappeur 2
        ("Alexandre", "Roy", 44),    # Frappeur 3
        ("Nicolas", "Gagnon", 8),    # Frappeur 4
        ("Gabriel", "Côté", 19),     # Frappeur 5
        ("Samuel", "Bouchard", 27),  # Frappeur 6
        ("Félix", "Tremblay", 2),    # Frappeur 7
        ("William", "Pelletier", 15),# Frappeur 8
        ("Olivier", "Levesque", 5)   # Frappeur 9
    ]

    print("--- 1. Insertion des joueurs dans l'alignement ---")
    joueurs_ids = []
    for prenom, nom, numero in alignement_fictif:
        # On insère le joueur s'il n'existe pas déjà
        cursor.execute('''
            INSERT INTO joueurs (prenom, nom, numero_dossard) 
            VALUES (?, ?, ?)
        ''', (prenom, nom, numero))
        joueurs_ids.append(cursor.lastrowid)
        print(f"Joueur inséré : {prenom} {nom} (#{numero}) - ID: {cursor.lastrowid}")

    # 3. Création d'une nouvelle partie
    print("\n--- 2. Création de la partie ---")
    cursor.execute('''
        INSERT INTO parties (date_match, equipe_adverse, lieu, type_match)
        VALUES (?, ?, ?, ?)
    ''', (date(2026, 7, 13), "Les Voyageurs de Saguenay", "Parc Laviolette", "Saison régulière"))
    partie_id = cursor.lastrowid
    print(f"Match créé contre les Voyageurs - ID de la partie : {partie_id}")

    # 4. Simulation de la 1ère manche au bâton (3 retraits)
    # Déroulement fictif de la manche :
    # - Frappeur 1 (Julien) : Réussit un Simple (S), puis vole le 2e but (BV)
    # - Frappeur 2 (Mathieu) : Obtient un But sur balles (BB). Julien avance au 3e but.
    # - Frappeur 3 (Alexandre) : Frappe un Double (D). Julien marque (point_marque=1). Mathieu avance au 3e. 1 point produit (RBI=1).
    # - Frappeur 4 (Nicolas) : Retrait sur des prises élancé (K). [1er RETRAIT]
    # - Frappeur 5 (Gabriel) : Roulant à l'arrêt-court vers le 1er but (6-3). Mathieu marque sur le jeu (RBI=1). [2e RETRAIT]
    # - Frappeur 6 (Samuel) : Ballon capté au champ centre (F8). [3e RETRAIT - Fin de la demi-manche]

    evenements_manche = [
        # (joueur_id, manche, code, point_marque, rbi, buts_voles)
        (joueurs_ids[0], 1, "S", 1, 0, 1),   # Julien : Simple, marque 1 point, 1 but volé
        (joueurs_ids[1], 1, "BB", 1, 0, 0),  # Mathieu : But sur balles, marque 1 point
        (joueurs_ids[2], 1, "D", 0, 1, 0),   # Alexandre : Double, produit 1 point
        (joueurs_ids[3], 1, "K", 0, 0, 0),   # Nicolas : Retrait K
        (joueurs_ids[4], 1, "6-3", 0, 1, 0), # Gabriel : Retrait 6-3, produit 1 point
        (joueurs_ids[5], 1, "F8", 0, 0, 0)   # Samuel : Retrait F8 (fin de manche)
    ]

    print("\n--- 3. Simulation des présences au bâton (Manche 1) ---")
    for joueur_id, manche, code, point, rbi, bv in evenements_manche:
        cursor.execute('''
            INSERT INTO presences (partie_id, joueur_id, manche, code_resultat, point_marque, points_produits, buts_voles)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (partie_id, joueur_id, manche, code, point, rbi, bv))
        
        # Récupérer le nom du joueur pour l'affichage console
        cursor.execute("SELECT prenom, nom FROM joueurs WHERE id = ?", (joueur_id,))
        nom_joueur = cursor.fetchone()
        print(f"Manche {manche} | {nom_joueur[0]} {nom_joueur[1]} -> Action: '{code}' | Points Marqués: {point} | PP (RBI): {rbi} | Vol(s): {bv}")

    # 5. Sauvegarde des changements et fermeture
    conn.commit()
    conn.close()
    print("\nSimulation terminée avec succès et enregistrée en base de données !")

# Exécuter le script de simulation
if __name__ == "__main__":
    simuler_premiere_manche()