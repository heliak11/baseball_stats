import pandas as pd
import gspread
import streamlit as st
import io
from datetime import datetime

# ---------------------------------------------------------
# 1. DONNÉES BRUTES (Copiez-collez vos données ici)
# ---------------------------------------------------------
DONNEES_BRUTES = """joueur	Partie	Date		PLU	1B	2B	3B	CC	KE	KD	FO	GO	SAC	DI	E/OPT	BB	FA	BV	PP	RUN	DFO	H	K	PA	AB	PP
R Gagnon	Gatineau, partie matin	10-Jul-26																			0	0	0	0	0	0
C Gohier	Gatineau, partie matin	10-Jul-26				1						1						1	1	1	1	1	0	2	2	1
N Trottier	Gatineau, partie matin	10-Jul-26						1	1										1	1	1	1	1	2	2	1
S Sarazin	Gatineau, partie matin	10-Jul-26							1								1				0	0	1	2	1	0
N Lefebvre	Gatineau, partie matin	10-Jul-26									1					1		1			0	0	0	2	1	0
L-K Comtois	Gatineau, partie matin	10-Jul-26							1	1											0	0	2	2	2	0
C Sirois	Gatineau, partie matin	10-Jul-26									1	1									0	0	0	2	2	0
L Gendron	Gatineau, partie matin	10-Jul-26										1					1				0	0	0	2	1	0
G Roberge	Gatineau, partie matin	10-Jul-26							1							1		1			0	0	1	2	1	0
L-R Lalande	Gatineau, partie matin	10-Jul-26							1			1									0	0	1	2	2	0
L Barbério McDavid	Gatineau, partie matin	10-Jul-26				1			1											1	1	1	1	2	2	0
M Poirier	Gatineau, partie matin	10-Jul-26										2							1		0	0	0	2	2	1
V Soucy	Gatineau, partie matin	10-Jul-26								1		1									0	0	1	2	2	0
R Gagnon	Gatineau, partie soir	10-Jul-26									1	1									0	0	0	2	2	0
C Gohier	Gatineau, partie soir	10-Jul-26			1	1													1	1	2	2	0	2	2	1
N Trottier	Gatineau, partie soir	10-Jul-26							1							1				1	0	0	1	2	1	0
S Sarazin	Gatineau, partie soir	10-Jul-26							1							1		1		1	0	0	1	2	1	0
N Lefebvre	Gatineau, partie soir	10-Jul-26							1							1					0	0	1	2	1	0
L-K Comtois	Gatineau, partie soir	10-Jul-26							1			1									0	0	1	2	2	0
C Sirois	Gatineau, partie soir	10-Jul-26			1											1		1		1	1	1	0	2	1	0
L Gendron	Gatineau, partie soir	10-Jul-26													1		1			1	0	0	0	2	1	0
G Roberge	Gatineau, partie soir	10-Jul-26							1												0	0	1	1	1	0
L-R Lalande	Gatineau, partie soir	10-Jul-26							1	1											0	0	2	2	2	0
L Barbério McDavid	Gatineau, partie soir	10-Jul-26			1							1								1	1	1	0	2	2	0
M Poirier	Gatineau, partie soir	10-Jul-26				1						1							2	1	1	1	0	2	2	2
V Soucy	Gatineau, partie soir	10-Jul-26										2									0	0	0	2	2	0
R Gagnon	Gatineau	11-Jul-26			1				1												1	1	1	2	2	0
C Gohier	Gatineau	11-Jul-26			1	2										1		4	2	2	3	3	0	4	3	2
N Trottier	Gatineau	11-Jul-26							2						1			1		1	0	0	2	3	3	0
S Sarazin	Gatineau	11-Jul-26							1		1	1							1		0	0	1	3	3	1
N Lefebvre	Gatineau	11-Jul-26								1						1					0	0	1	2	1	0
L-K Comtois	Gatineau	11-Jul-26				2														1	2	2	0	2	2	0
C Sirois	Gatineau	11-Jul-26			1					1								1		1	1	1	1	2	2	0
L Gendron	Gatineau	11-Jul-26			2										1						2	2	0	3	3	0
G Roberge	Gatineau	11-Jul-26			1										1					1	1	1	0	2	2	0
L-R Lalande	Gatineau	11-Jul-26			1													1	1	1	1	1	0	1	1	1
L Barbério McDavid	Gatineau	11-Jul-26			2				1												2	2	1	3	3	0
M Poirier	Gatineau	11-Jul-26			1							1				1			3	1	1	1	0	3	2	3
V Soucy	Gatineau	11-Jul-26			1							1								1	1	1	0	2	2	0"""

# ---------------------------------------------------------
# 2. LOGIQUE D'IMPORTATION
# ---------------------------------------------------------
def executer_importation():
    print("⏳ Lecture et préparation des données...")
    # Lecture des données avec Pandas (séparateur = tabulation)
    df = pd.read_csv(io.StringIO(DONNEES_BRUTES), sep='\t')
    df.columns = df.columns.str.strip()
    df = df.fillna(0)
    
    # Connexion à Google Sheets
    print("🔌 Connexion à Google Sheets...")
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1mDPEcK9zRMKj7YZLqI1Q1Q9AeTjUGlIHl13jnfaIkF4/edit?gid=0#gid=0")
    
    ws_joueurs = sh.worksheet("joueurs")
    ws_parties = sh.worksheet("parties")
    ws_presences = sh.worksheet("presences")
    
    joueurs_existants = ws_joueurs.get_all_records()
    parties_existantes = ws_parties.get_all_records()
    
    # Dictionnaires pour mapper rapidement noms -> IDs
    dict_joueurs = {f"{j['prenom']} {j['nom']}".strip(): j['id'] for j in joueurs_existants}
    dict_parties = {p['equipe_adverse']: p['id'] for p in parties_existantes}
    
    prochain_id_joueur = len(ws_joueurs.get_all_values())
    prochain_id_partie = len(ws_parties.get_all_values())
    prochain_id_presence = len(ws_presences.get_all_values())
    
    nouvelles_presences = []
    
    colonnes_actions = {
        '1B': '1B', '2B': '2B', '3B': '3B', 'CC': 'CC', 
        'KE': 'KE', 'KD': 'KD', 'FO': 'FO', 'GO': 'GO', 
        'SAC': 'SAC', 'E/OPT': 'E', 'BB': 'BB', 'FA': 'FA'
    }
    
    print("🔄 Traitement des lignes...")
    for index, row in df.iterrows():
        nom_joueur_brut = str(row['joueur']).strip()
        nom_partie_brut = str(row['Partie']).strip()
        
        if not nom_joueur_brut or not nom_partie_brut:
            continue
            
        # 1. Gestion du joueur
        if nom_joueur_brut not in dict_joueurs:
            parts = nom_joueur_brut.split(' ', 1)
            prenom = parts[0]
            nom = parts[1] if len(parts) > 1 else ""
            ws_joueurs.append_row([prochain_id_joueur, prenom, nom, 0])
            dict_joueurs[nom_joueur_brut] = prochain_id_joueur
            print(f"👤 Nouveau joueur créé : {nom_joueur_brut}")
            prochain_id_joueur += 1
            
        joueur_id = dict_joueurs[nom_joueur_brut]
        
        # 2. Gestion de la partie
        if nom_partie_brut not in dict_parties:
            date_str = str(row['Date']).strip()
            try:
                date_formatee = datetime.strptime(date_str, "%d-%b-%y").strftime("%Y-%m-%d")
            except Exception:
                date_formatee = date_str
                
            ws_parties.append_row([prochain_id_partie, date_formatee, nom_partie_brut, "À déterminer", "Tournoi", "À venir", ""])
            dict_parties[nom_partie_brut] = prochain_id_partie
            print(f"🏟️ Nouveau match créé : {nom_partie_brut} ({date_formatee})")
            prochain_id_partie += 1
            
        partie_id = dict_parties[nom_partie_brut]
        
        # 3. Récupération des statistiques globales pour cette ligne
        vols = int(float(row.get('BV', 0)))
        points = int(float(row.get('RUN', 0)))
        rbi = int(float(row.get('PP', 0))) # Pandas prendra la 1ère occurrence de 'PP'
        
        actions_pour_ce_joueur = []
        
        # Parcourt toutes les colonnes d'actions possibles
        for col_csv, code_app in colonnes_actions.items():
            if col_csv in row:
                try:
                    quantite = int(float(row[col_csv]))
                    for _ in range(quantite):
                        actions_pour_ce_joueur.append(code_app)
                except (ValueError, TypeError):
                    pass
                    
        # Si le joueur n'a aucune action mais a des statistiques (ex: 0 AB mais 1 RUN)
        if len(actions_pour_ce_joueur) == 0 and (vols > 0 or points > 0 or rbi > 0):
            actions_pour_ce_joueur.append("")
            
        # 4. Création des lignes de présence (assigne les statistiques à la première action)
        for i, code_action in enumerate(actions_pour_ce_joueur):
            est_premiere_action = (i == 0)
            nouvelles_presences.append([
                prochain_id_presence, partie_id, joueur_id, 1, code_action, 
                points if est_premiere_action else 0, 
                rbi if est_premiere_action else 0, 
                vols if est_premiere_action else 0
            ])
            prochain_id_presence += 1

    if nouvelles_presences:
        print(f"🚀 Injection de {len(nouvelles_presences)} présences dans Google Sheets...")
        ws_presences.append_rows(nouvelles_presences)
        print("✅ Importation terminée avec succès !")
    else:
        print("ℹ️ Aucune donnée valide trouvée pour l'importation.")

if __name__ == "__main__":
    executer_importation()