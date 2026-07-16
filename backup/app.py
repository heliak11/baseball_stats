import streamlit as st
import pandas as pd
import gspread

st.set_page_config(page_title="Baseball Midget - Stats", page_icon="⚾", layout="centered")
st.title("⚾ Tableau de Bord Midget")

# ---------------------------------------------------------
# Connexion à Google Sheets
# ---------------------------------------------------------
# Se connecte en utilisant les "Secrets" de Streamlit
gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
# Ouvre le fichier via son lien (remplace par ton URL)
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1mDPEcK9zRMKj7YZLqI1Q1Q9AeTjUGlIHl13jnfaIkF4/edit?gid=0#gid=0")

# Chargement des onglets
ws_joueurs = sh.worksheet("Joueurs")
ws_parties = sh.worksheet("Parties")
ws_presences = sh.worksheet("Presences")

# Lecture des données vers Pandas
joueurs_df = pd.DataFrame(ws_joueurs.get_all_records())
parties_df = pd.DataFrame(ws_parties.get_all_records())

# Dictionnaires pour les menus déroulants
dict_joueurs = {f"{row['prenom']} {row['nom']} (#{row['numero_dossard']})": row['id'] for _, row in joueurs_df.iterrows()} if not joueurs_df.empty else {}
dict_parties = {f"{row['date_match']} vs {row['equipe_adverse']}": row['id'] for _, row in parties_df.iterrows()} if not parties_df.empty else {}

# ---------------------------------------------------------
# Formulaire de saisie
# ---------------------------------------------------------
st.header("Nouvelle présence au bâton")
with st.form("form_saisie", clear_on_submit=True):
    partie_choisie = st.selectbox("Match", list(dict_parties.keys()))
    manche_choisie = st.number_input("Manche", min_value=1, max_value=9, value=1)
    joueur_choisi = st.selectbox("Joueur au bâton", list(dict_joueurs.keys()))
    
    code_complet = st.selectbox("Action", ["S (Simple)", "D (Double)", "K (Retrait sur prises)", "6-3 (Roulant)"])
    code_final = code_complet.split(" ")[0]
    
    point_marque = st.checkbox("Point marqué ?")
    rbi = st.number_input("Points produits (RBI)", min_value=0, max_value=4, value=0)
    bv = st.number_input("Buts volés", min_value=0, max_value=4, value=0)
    
    soumis = st.form_submit_button("Enregistrer la présence", type="primary")
    
    if soumis:
        # On génère un nouvel ID pour la présence
        nouvel_id = len(ws_presences.get_all_values()) # Compte les lignes existantes
        
        # On ajoute une ligne directement dans le Google Sheets !
        ws_presences.append_row([
            nouvel_id, 
            dict_parties[partie_choisie], 
            dict_joueurs[joueur_choisi], 
            manche_choisie, 
            code_final, 
            int(point_marque), 
            rbi, 
            bv
        ])
        st.success(f"✅ Présence enregistrée dans Google Sheets pour {joueur_choisi.split('(')[0]}!")
# ---------------------------------------------------------
# Configuration de la page (adaptée pour mobile)
# ---------------------------------------------------------
st.set_page_config(page_title="Baseball Midget - Stats", page_icon="⚾", layout="centered")
st.title("⚾ Tableau de Bord Midget")

# ---------------------------------------------------------
# Fonctions de base de données
# ---------------------------------------------------------
def lire_donnees(requete):
    """Exécute une requête SELECT et retourne un DataFrame Pandas"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(requete, conn)
    conn.close()
    return df

def inserer_presence(partie_id, joueur_id, manche, code, point, rbi, bv):
    """Insère une nouvelle présence dans la base de données"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO presences (partie_id, joueur_id, manche, code_resultat, point_marque, points_produits, buts_voles)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (partie_id, joueur_id, manche, code, point, rbi, bv))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# Chargement des données pour l'interface
# ---------------------------------------------------------
joueurs_df = lire_donnees("SELECT id, prenom, nom, numero_dossard FROM joueurs")
parties_df = lire_donnees("SELECT id, equipe_adverse, date_match FROM parties")

# Création de dictionnaires pour les menus déroulants
if not joueurs_df.empty:
    noms_joueurs = joueurs_df['prenom'] + " " + joueurs_df['nom'] + " (#" + joueurs_df['numero_dossard'].astype(str) + ")"
    dict_joueurs = dict(zip(noms_joueurs, joueurs_df['id']))
else:
    dict_joueurs = {}

if not parties_df.empty:
    noms_parties = parties_df['date_match'] + " vs " + parties_df['equipe_adverse']
    dict_parties = dict(zip(noms_parties, parties_df['id']))
else:
    dict_parties = {}

# ---------------------------------------------------------
# Interface Utilisateur : Onglets
# ---------------------------------------------------------
onglet_saisie, onglet_stats = st.tabs(["📝 Saisie Rapide", "📊 Journal & Stats"])

# --- ONGLET 1 : SAISIE SUR LE TERRAIN ---
with onglet_saisie:
    st.header("Nouvelle présence au bâton")
    
    if not dict_joueurs or not dict_parties:
        st.warning("La base de données est vide. Assurez-vous que l'initialisation a bien fonctionné.")
    else:
        with st.form("form_saisie", clear_on_submit=True):
            # Sélections principales
            col1, col2 = st.columns(2)
            with col1:
                partie_choisie = st.selectbox("Match", list(dict_parties.keys()))
            with col2:
                manche_choisie = st.number_input("Manche", min_value=1, max_value=9, value=1)
            
            joueur_choisi = st.selectbox("Joueur au bâton", list(dict_joueurs.keys()))
            
            # Codes officiels Baseball Québec
            st.write("**Résultat (Codes Baseball Québec)**")
            codes_offensifs = ["S (Simple)", "D (Double)", "T (Triple)", "CC (Circuit)", "BB (But sur balles)", "FA (Atteint)"]
            codes_retraits = ["K (Retrait sur prises)", "6-3 (Roulant)", "F8 (Ballon)"]
            
            code_complet = st.selectbox("Action", codes_offensifs + codes_retraits)
            code_final = code_complet.split(" ")[0] # Extrait "S", "D", "K", etc.
            
            # Statistiques additionnelles
            st.write("**Actions sur les buts**")
            col_pts, col_rbi, col_bv = st.columns(3)
            with col_pts:
                point_marque = st.checkbox("Point marqué ?")
            with col_rbi:
                rbi = st.number_input("Points produits (RBI)", min_value=0, max_value=4, value=0)
            with col_bv:
                bv = st.number_input("Buts volés", min_value=0, max_value=4, value=0)
                
            # Bouton de soumission
            soumis = st.form_submit_button("Enregistrer la présence", type="primary", use_container_width=True)
            
            if soumis:
                inserer_presence(
                    partie_id=dict_parties[partie_choisie],
                    joueur_id=dict_joueurs[joueur_choisi],
                    manche=manche_choisie,
                    code=code_final,
                    point=int(point_marque),
                    rbi=rbi,
                    bv=bv
                )
                st.success(f"✅ Présence enregistrée pour {joueur_choisi.split('(')[0]}!")

# --- ONGLET 2 : STATISTIQUES ET JOURNAL ---
with onglet_stats:
    st.header("Journal des matchs")
    
    # Légende des codes dans un menu déroulant
    with st.expander("📖 Voir la légende des codes (Baseball Québec)"):
        st.markdown("""
        | Code | Signification | Est un Coup Sûr (H) ? | Est une Présence Officielle (AB) ? |
        | :--- | :--- | :--- | :--- |
        | **S** | Simple |  Oui |  Oui |
        | **D** | Double |  Oui |  Oui |
        | **T** | Triple |  Oui |  Oui |
        | **CC** | Coup de circuit |  Oui |  Oui |
        | **BB** | But sur balles | ❌ Non | ❌ Non |
        | **FA** | Frappé par l'aligneur (Atteint) | ❌ Non | ❌ Non |
        | **K / ꓘ** | Retrait sur des prises | ❌ Non |  Oui |
        | **6-3 / F8 (etc.)** | Retrait défensif | ❌ Non |  Oui |
        """)
        st.caption("📌 **Rappel des positions :** 1=Lanceur, 2=Receveur, 3=1er but, 4=2e but, 5=3e but, 6=Arrêt-court, 7=Champ gauche, 8=Champ centre, 9=Champ droit.")
    
    # Requête SQL pour charger toutes les présences de la base de données
    requete_complete = """
    SELECT 
        j.prenom || ' ' || j.nom AS Joueur,
        p.code_resultat AS Action,
        p.point_marque AS Points,
        p.points_produits AS RBI,
        p.buts_voles AS Vols
    FROM presences p
    JOIN joueurs j ON p.joueur_id = j.id
    """
    
    df_presences = lire_donnees(requete_complete)
    
    if not df_presences.empty:
        # ---------------------------------------------------------
        # Calcul des statistiques avancées avec Pandas
        # ---------------------------------------------------------
        
        # 1. Définir ce qui est un Coup Sûr (H) et une Présence Officielle (AB)
        liste_coups_surs = ['S', 'D', 'T', 'CC']
        # Tout ce qui n'est pas un BB ou FA (Atteint) est une présence officielle (AB)
        exclure_du_ab = ['BB', 'FA'] 
        
        # 2. Créer des colonnes temporaires pour simplifier les calculs
        df_presences['Est_H'] = df_presences['Action'].isin(liste_coups_surs).astype(int)
        df_presences['Est_AB'] = (~df_presences['Action'].isin(exclure_du_ab)).astype(int)
        
        # 3. Grouper par joueur et faire les totaux
        stats_joueurs = df_presences.groupby('Joueur').agg(
            AB=('Est_AB', 'sum'),
            H=('Est_H', 'sum'),
            Points=('Points', 'sum'),
            RBI=('RBI', 'sum'),
            Buts_Voles=('Vols', 'sum')
        ).reset_index()
        
        # 4. CALCUL DE LA MOYENNE AU BÂTON (AVG)
        # On utilise une division sécurisée au cas où un joueur a 0 AB (pour éviter la division par zéro)
        stats_joueurs['AVG'] = stats_joueurs.apply(
            lambda row: row['H'] / row['AB'] if row['AB'] > 0 else 0.0, axis=1
        )
        
        # Formatage de l'affichage de la moyenne (ex: .333 au lieu de 0.33333)
        stats_joueurs['AVG_Format'] = stats_joueurs['AVG'].apply(lambda x: f".{int(x*1000):03d}" if x < 1 else "1.000")
        
        # ---------------------------------------------------------
        # Affichage des tableaux dans Streamlit
        # ---------------------------------------------------------
        
        # Section A : Statistiques cumulatives des joueurs
        st.subheader("📊 Statistiques des Joueurs (Saison)")
        
        # On renomme et ordonne les colonnes pour que ce soit beau
        df_affichage_stats = stats_joueurs[['Joueur', 'AB', 'H', 'AVG_Format', 'Points', 'RBI', 'Buts_Voles']].rename(
            columns={
                'AB': 'AB (Présences)',
                'H': 'H (Coups Sûrs)',
                'AVG_Format': 'AVG (Moyenne)',
                'Points': 'R (Points)',
                'Buts_Voles': 'SB (Buts Volés)'
            }
        )
        
        # Trier par la meilleure moyenne au bâton
        df_affichage_stats = df_affichage_stats.sort_values(by='AVG (Moyenne)', ascending=False)
        st.dataframe(df_affichage_stats, use_container_width=True, hide_index=True)
        
        # Section B : Journal historique des jeux
        st.subheader("📋 Journal historique des jeux")
        st.dataframe(df_presences[['Joueur', 'Action', 'Points', 'RBI', 'Vols']], use_container_width=True, hide_index=True)
        
    else:
        st.info("Aucune donnée enregistrée pour le moment. Allez à l'onglet Saisie pour enregistrer votre premier match !")