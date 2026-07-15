import streamlit as st
import pandas as pd
import gspread
import time
import datetime

st.set_page_config(page_title="Baseball Midget - Stats", page_icon="⚾", layout="centered")
st.title("⚾ Tableau de Bord Midget")

# ---------------------------------------------------------
# Connexion à Google Sheets
# ---------------------------------------------------------
# Se connecte en utilisant les "Secrets" de Streamlit
gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
# Ouvre le fichier via son lien (remplace par ton URL)
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1mDPEcK9zRMKj7YZLqI1Q1Q9AeTjUGlIHl13jnfaIkF4/edit?gid=0#gid=0")

# On garde la référence de l'onglet des présences pour pouvoir y écrire
ws_presences = sh.worksheet("presences")
try:
    ws_defense = sh.worksheet("defense")
except gspread.WorksheetNotFound:
    ws_defense = sh.add_worksheet(title="defense", rows="1000", cols="8")
    ws_defense.append_row(["id", "partie_id", "joueur_id", "manche", "position", "po", "a", "e"])

# ---------------------------------------------------------
# Chargement optimisé des données (Mise en cache)
# ---------------------------------------------------------
# Garde les données en mémoire pendant 10 minutes ou jusqu'à ce qu'on vide le cache manuellement
@st.cache_data(ttl=600)
def charger_donnees():
    # Fonction interne pour charger une feuille de manière robuste, évitant l'erreur sur les en-têtes dupliqués.
    def safe_load_sheet(worksheet):
        all_values = worksheet.get_all_values()
        if not all_values:
            return pd.DataFrame() # Retourne un DataFrame vide si la feuille est vide
        headers = all_values[0]
        data = all_values[1:]
        return pd.DataFrame(data, columns=headers)

    df_j = safe_load_sheet(sh.worksheet("joueurs"))
    df_p = safe_load_sheet(sh.worksheet("parties"))
    df_pres = safe_load_sheet(ws_presences)
    df_def = safe_load_sheet(ws_defense)
    return df_j, df_p, df_pres, df_def

# On appelle la fonction mise en cache (instantané après le 1er chargement !)
joueurs_df, parties_df, presences_df, defense_df = charger_donnees()

# ---------------------------------------------------------
# Normalisation des en-têtes pour éviter les erreurs de frappe
# (enlève les espaces, met en minuscules, retire les accents)
# ---------------------------------------------------------
for df in [joueurs_df, parties_df, presences_df, defense_df]:
    if not df.empty:
        df.columns = df.columns.str.strip().str.lower().str.replace('é', 'e').str.replace('è', 'e')

# Création de dictionnaires pour les menus déroulants
if not joueurs_df.empty:
    noms_joueurs = joueurs_df['prenom'].astype(str) + " " + joueurs_df['nom'].astype(str) + " (#" + joueurs_df['numero_dossard'].astype(str) + ")"
    dict_joueurs = dict(zip(noms_joueurs, joueurs_df['id']))
else:
    dict_joueurs = {}

if not parties_df.empty:
    if 'resultat' not in parties_df.columns:
        parties_df['resultat'] = "À venir"
    if 'pointage' not in parties_df.columns:
        parties_df['pointage'] = ""
        
    def format_nom_partie(row):
        base = f"{row['date_match']} vs {row['equipe_adverse']} ({row['type_match']} à {row['lieu']})"
        res = str(row['resultat'])
        score = str(row['pointage'])
        if res != 'nan' and res != 'À venir' and res != '':
            if score != 'nan' and score != '':
                return f"{base} - {res} [{score}]"
            else:
                return f"{base} - {res}"
        return base
        
    noms_parties = parties_df.apply(format_nom_partie, axis=1)
    dict_parties = dict(zip(noms_parties, parties_df['id']))
else:
    dict_parties = {}

# ---------------------------------------------------------
# Fonction pour afficher la légende (Réutilisable)
# ---------------------------------------------------------
def afficher_legende():
    with st.expander("📖 Voir la légende des codes et des statistiques"):
        st.write("**Codes d'action (Baseball Québec)**")
        st.markdown("""
        | Code | Signification | Est un Coup Sûr (H) ? | Est une Présence Officielle (AB) ? |
        | :--- | :--- | :--- | :--- |
        | **1B** | Simple (Single) |  Oui |  Oui |
        | **2B** | Double |  Oui |  Oui |
        | **3B** | Triple |  Oui |  Oui |
        | **CC** | Coup de circuit |  Oui |  Oui |
        | **BB** | But sur balles | ❌ Non | ❌ Non |
        | **FA** | Frappé par l'aligneur (Atteint) | ❌ Non | ❌ Non |
        | **SAC** | Amorti Sacrifice / Ballon Sacrifice | ❌ Non | ❌ Non |
        | **KE** | Retrait sur prises (sans élan / regardé) | ❌ Non |  Oui |
        | **KD** | Retrait sur prises (sur élan) | ❌ Non |  Oui |
        | **E / FC** | Atteint sur Erreur / Choix Défensif | ❌ Non |  Oui |
        | **GO** | Roulant (Ground Out) | ❌ Non |  Oui |
        | **FO** | Ballon (Fly Out) | ❌ Non |  Oui |
        """)
        st.caption("📌 **Rappel des positions :** 1=Lanceur (P), 2=Receveur (C), 3=1er but (1B), 4=2e but (2B), 5=3e but (3B), 6=Arrêt-court (SS), 7=Champ gauche (LF), 8=Champ centre (CF), 9=Champ droit (RF), DH=Frappeur de choix, B=Banc.")
        
        st.markdown("---")
        st.write("**Abréviations des statistiques**")
        st.markdown("""
        | Abréviation | Terme anglais | Signification |
        | :--- | :--- | :--- |
        | **PA** | Plate Appearances | **Présences au marbre** (Total des passages au bâton) |
        | **AB** | At-Bats | **Présences officielles** (Exclut les buts sur balles et atteints) |
        | **R** | Runs | **Points marqués** |
        | **H** | Hits | **Coups sûrs** (Simples, Doubles, Triples, Circuits) |
        | **2B** | Doubles | **Doubles** (Coups sûrs de 2 buts) |
        | **3B** | Triples | **Triples** (Coups sûrs de 3 buts) |
        | **HR** | Home Runs | **Coups de circuit** |
        | **RBI** | Runs Batted In | **Points produits** |
        | **BB** | Base on Balls | **Buts sur balles** |
        | **SB** | Stolen Bases | **Buts volés** |
        | **AVG** | Batting Average | **Moyenne au bâton** (H ÷ AB) |
        | **OBP** | On-Base Percentage | **Présence sur les buts** ((H + BB + FA) ÷ PA) |
        | **SLG** | Slugging Percentage | **Puissance** (Total des buts obtenus ÷ AB) |
        | **OPS** | On-Base Plus Slugging | **OBP + SLG** (Indice global de performance offensive) |
        | **PO** | Putouts | **Retraits** (Défensive : action d'éliminer directement un coureur/frappeur) |
        | **A** | Assists | **Assistances** (Défensive : lancer/relais menant à un retrait) |
        | **E** | Errors | **Erreurs** (Défensive : jeu raté permettant à un joueur d'avancer) |
        """)

# ---------------------------------------------------------
# Interface Utilisateur : Navigation
# ---------------------------------------------------------
st.sidebar.title("Navigation")
choix_menu = st.sidebar.radio("Aller vers :", ["⚾ Grille de Match", "📊 Journal & Stats", "⚙️ Gestion"])

# --- ONGLET 1 : GRILLE DE MATCH (MATRICE) ---
if choix_menu == "⚾ Grille de Match":
    st.header("Feuille de match interactive")
    
    afficher_legende()
    
    if not dict_joueurs or not dict_parties:
        st.warning("Vos onglets Google Sheets sont vides.")
    else:
        partie_grille = st.selectbox("Sélectionnez le match", list(dict_parties.keys()), key="select_match_grille")
        
        partie_id_selectionnee = dict_parties[partie_grille]
        
        onglet_off, onglet_def = st.tabs(["🏏 Offensive", "🧤 Défensive"])
        
        with onglet_off:
            st.write("Remplissez les cases avec les résultats offensifs. Laissez vide si le joueur n'a pas frappé.")
            
            # 1. Préparer le tableau vide (Lignes = Joueurs, Colonnes = Manches 1 à 9)
            noms = list(dict_joueurs.keys())
            df_grille = pd.DataFrame({"Joueur": noms})
            for i in range(1, 10):
                df_grille[f"M{i}"] = ""
                
            # Ajout des colonnes pour les statistiques globales du match
            df_grille["Points"] = 0
            df_grille["RBI"] = 0
            df_grille["Vols"] = 0

            mapping_lignes_gs = {}
            # 2. Pré-remplir avec les données existantes pour ce match
            if not presences_df.empty:
                # On convertit les identifiants en texte pour éviter les erreurs de comparaison (ex: 1 vs "1")
                presences_match = presences_df[presences_df['partie_id'].astype(str) == str(partie_id_selectionnee)]
                for idx_df, row_pres in presences_match.iterrows():
                    joueur_nom = next((nom for nom, j_id in dict_joueurs.items() if str(j_id) == str(row_pres['joueur_id'])), None)
                    if joueur_nom and pd.notna(row_pres['manche']):
                        # Pandas transforme parfois les chiffres en décimales (1.0 au lieu de 1). On sécurise avec un `int` pur.
                        try:
                            manche_int = int(float(row_pres['manche']))
                            if 1 <= manche_int <= 9:
                                idx = df_grille.index[df_grille['Joueur'] == joueur_nom].tolist()
                                if idx:
                                    df_grille.at[idx[0], f"M{manche_int}"] = str(row_pres['code_resultat'])
                                    mapping_lignes_gs[(str(dict_joueurs[joueur_nom]), manche_int)] = {
                                        "ligne": idx_df + 2,
                                        "code": str(row_pres['code_resultat']),
                                        "points": int(row_pres.get('point_marque', 0) or 0),
                                        "rbi": int(row_pres.get('points_produits', 0) or 0),
                                        "vols": int(row_pres.get('buts_voles', 0) or 0)
                                    }
                                    # Accumuler les stats pour l'affichage
                                    df_grille.at[idx[0], "Points"] += int(row_pres.get('point_marque', 0) or 0)
                                    df_grille.at[idx[0], "RBI"] += int(row_pres.get('points_produits', 0) or 0)
                                    df_grille.at[idx[0], "Vols"] += int(row_pres.get('buts_voles', 0) or 0)
                        except ValueError:
                            pass
                
            # 3. Configurer les colonnes pour avoir des menus déroulants
            # Options offensives avec KE (Regardé), KD (Élan), GO (Roulant) et FO (Ballon)
            options_codes = ["", "1B", "2B", "3B", "CC", "BB", "FA", "SAC", "KE", "KD", "E", "FC", "GO", "FO"]
            col_config = {"Joueur": st.column_config.Column(disabled=True)}
            for i in range(1, 10):
                col_config[f"M{i}"] = st.column_config.SelectboxColumn(label=str(i), options=options_codes, width="small")
                
            # Configuration des nouvelles colonnes
            col_config["Points"] = st.column_config.NumberColumn(label="RUN (Points)", min_value=0, step=1, width="small")
            col_config["RBI"] = st.column_config.NumberColumn(label="PP (RBI)", min_value=0, step=1, width="small")
            col_config["Vols"] = st.column_config.NumberColumn(label="BV (Vols)", min_value=0, step=1, width="small")

            # 4. Afficher la grille éditable
            grille_editee = st.data_editor(df_grille, column_config=col_config, hide_index=True, use_container_width=True, key="grille_off")
            
            # 5. Bouton de sauvegarde de masse
            if st.button("💾 Enregistrer l'offensive", type="primary", use_container_width=True):
                with st.spinner("💾 Synchronisation de l'offensive..."):
                    prochain_id = len(ws_presences.get_all_values())
                    lignes_a_ajouter = []
                    mises_a_jour = 0
                    
                    for index, row in grille_editee.iterrows():
                        joueur_id_original = dict_joueurs[row["Joueur"]]
                        joueur_id_str = str(joueur_id_original)
                        
                        # Récupération des totaux pour ce joueur
                        pts_total = int(row["Points"])
                        rbi_total = int(row["RBI"])
                        vols_total = int(row["Vols"])
                        
                        # Déterminer la manche cible pour enregistrer ces totaux (la 1ère manche jouée)
                        manche_cible = None
                        for m in range(1, 10):
                            if not pd.isna(row[f"M{m}"]) and str(row[f"M{m}"]).strip() != "":
                                manche_cible = m
                                break
                        
                        # S'il a des stats mais aucune présence au bâton, on force la manche 1 (ex: coureur suppléant)
                        if manche_cible is None and (pts_total > 0 or rbi_total > 0 or vols_total > 0):
                            manche_cible = 1

                        for manche in range(1, 10):
                            valeur_nouvelle = "" if pd.isna(row[f"M{manche}"]) else str(row[f"M{manche}"]).strip()
                            info_gs = mapping_lignes_gs.get((joueur_id_str, manche))
                            
                            valeur_originale = info_gs["code"] if info_gs else ""
                            pts_original = info_gs["points"] if info_gs else 0
                            rbi_original = info_gs["rbi"] if info_gs else 0
                            vols_original = info_gs["vols"] if info_gs else 0
                            
                            # On assigne toutes les stats à la manche cible, 0 pour les autres
                            est_cible = (manche == manche_cible)
                            pts_assigne = pts_total if est_cible else 0
                            rbi_assigne = rbi_total if est_cible else 0
                            vols_assigne = vols_total if est_cible else 0
                            
                            if not info_gs:
                                # Ce n'était pas dans la base de données
                                if valeur_nouvelle != "" or (est_cible and (pts_assigne > 0 or rbi_assigne > 0 or vols_assigne > 0)):
                                    # C'est une nouvelle présence
                                    lignes_a_ajouter.append([
                                        prochain_id,
                                        partie_id_selectionnee,
                                        joueur_id_original,
                                        manche,
                                        valeur_nouvelle,
                                        pts_assigne, 
                                        rbi_assigne, 
                                        vols_assigne
                                    ])
                                    prochain_id += 1
                            else:
                                # Présence existante : vérifier quels champs ont changé
                                ligne_idx = info_gs["ligne"]
                                modifie = False
                                
                                if valeur_originale != valeur_nouvelle:
                                    ws_presences.update_cell(ligne_idx, 5, valeur_nouvelle)
                                    modifie = True
                                if pts_original != pts_assigne:
                                    ws_presences.update_cell(ligne_idx, 6, pts_assigne)
                                    modifie = True
                                if rbi_original != rbi_assigne:
                                    ws_presences.update_cell(ligne_idx, 7, rbi_assigne)
                                    modifie = True
                                if vols_original != vols_assigne:
                                    ws_presences.update_cell(ligne_idx, 8, vols_assigne)
                                    modifie = True
                                    
                                if modifie:
                                    mises_a_jour += 1
                                
                    if lignes_a_ajouter:
                        ws_presences.append_rows(lignes_a_ajouter)
                
                if lignes_a_ajouter or mises_a_jour > 0:
                    # Rafraichir le cache
                    charger_donnees.clear()
                    messages = []
                    if lignes_a_ajouter: messages.append(f"{len(lignes_a_ajouter)} ajout(s)")
                    if mises_a_jour > 0: messages.append(f"{mises_a_jour} modification(s)")
                    st.success(f"✅ Offensive enregistrée avec succès : {' et '.join(messages)} !")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("ℹ️ Aucune modification détectée pour l'offensive.")

        with onglet_def:
            st.write("Remplissez les positions défensives par manche (1=P, 2=C, 3=1B, etc.). Entrez les Retraits (PO), Assistances (A) et Erreurs (E) globalement.")
            
            noms_def = list(dict_joueurs.keys())
            df_grille_def = pd.DataFrame({"Joueur": noms_def})
            for i in range(1, 10):
                df_grille_def[f"M{i}"] = ""
                
            df_grille_def["PO"] = 0
            df_grille_def["A"] = 0
            df_grille_def["E"] = 0

            mapping_lignes_gs_def = {}
            if not defense_df.empty:
                defense_match = defense_df[defense_df['partie_id'].astype(str) == str(partie_id_selectionnee)]
                for idx_df, row_def in defense_match.iterrows():
                    joueur_nom = next((nom for nom, j_id in dict_joueurs.items() if str(j_id) == str(row_def['joueur_id'])), None)
                    if joueur_nom and pd.notna(row_def['manche']):
                        try:
                            manche_int = int(float(row_def['manche']))
                            if 1 <= manche_int <= 9:
                                idx = df_grille_def.index[df_grille_def['Joueur'] == joueur_nom].tolist()
                                if idx:
                                    df_grille_def.at[idx[0], f"M{manche_int}"] = str(row_def.get('position', ''))
                                    mapping_lignes_gs_def[(str(dict_joueurs[joueur_nom]), manche_int)] = {
                                        "ligne": idx_df + 2,
                                        "position": str(row_def.get('position', '')),
                                        "po": int(row_def.get('po', 0) or 0),
                                        "a": int(row_def.get('a', 0) or 0),
                                        "e": int(row_def.get('e', 0) or 0)
                                    }
                                    df_grille_def.at[idx[0], "PO"] += int(row_def.get('po', 0) or 0)
                                    df_grille_def.at[idx[0], "A"] += int(row_def.get('a', 0) or 0)
                                    df_grille_def.at[idx[0], "E"] += int(row_def.get('e', 0) or 0)
                        except ValueError:
                            pass
                            
            options_pos = ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "DH", "B"]
            col_config_def = {"Joueur": st.column_config.Column(disabled=True)}
            for i in range(1, 10):
                col_config_def[f"M{i}"] = st.column_config.SelectboxColumn(label=str(i), options=options_pos, width="small")
                
            col_config_def["PO"] = st.column_config.NumberColumn(label="Retraits (PO)", min_value=0, step=1, width="small")
            col_config_def["A"] = st.column_config.NumberColumn(label="Assistances (A)", min_value=0, step=1, width="small")
            col_config_def["E"] = st.column_config.NumberColumn(label="Erreurs (E)", min_value=0, step=1, width="small")
            
            grille_editee_def = st.data_editor(df_grille_def, column_config=col_config_def, hide_index=True, use_container_width=True, key="grille_def")
            
            if st.button("💾 Enregistrer la défensive", type="primary", use_container_width=True):
                with st.spinner("💾 Synchronisation de la grille défensive..."):
                    prochain_id_def = len(ws_defense.get_all_values())
                    lignes_a_ajouter_def = []
                    mises_a_jour_def = 0
                    
                    for index, row in grille_editee_def.iterrows():
                        joueur_id_original = dict_joueurs[row["Joueur"]]
                        joueur_id_str = str(joueur_id_original)
                        
                        po_total = int(row["PO"])
                        a_total = int(row["A"])
                        e_total = int(row["E"])
                        
                        manche_cible = None
                        for m in range(1, 10):
                            if not pd.isna(row[f"M{m}"]) and str(row[f"M{m}"]).strip() != "":
                                manche_cible = m
                                break
                                
                        if manche_cible is None and (po_total > 0 or a_total > 0 or e_total > 0):
                            manche_cible = 1
                            
                        for manche in range(1, 10):
                            valeur_nouvelle = "" if pd.isna(row[f"M{manche}"]) else str(row[f"M{manche}"]).strip()
                            info_gs = mapping_lignes_gs_def.get((joueur_id_str, manche))
                            
                            valeur_originale = info_gs["position"] if info_gs else ""
                            po_original = info_gs["po"] if info_gs else 0
                            a_original = info_gs["a"] if info_gs else 0
                            e_original = info_gs["e"] if info_gs else 0
                            
                            est_cible = (manche == manche_cible)
                            po_assigne = po_total if est_cible else 0
                            a_assigne = a_total if est_cible else 0
                            e_assigne = e_total if est_cible else 0
                            
                            if not info_gs:
                                if valeur_nouvelle != "" or (est_cible and (po_assigne > 0 or a_assigne > 0 or e_assigne > 0)):
                                    lignes_a_ajouter_def.append([
                                        prochain_id_def,
                                        partie_id_selectionnee,
                                        joueur_id_original,
                                        manche,
                                        valeur_nouvelle,
                                        po_assigne,
                                        a_assigne,
                                        e_assigne
                                    ])
                                    prochain_id_def += 1
                            else:
                                ligne_idx = info_gs["ligne"]
                                modifie = False
                                
                                if valeur_originale != valeur_nouvelle:
                                    ws_defense.update_cell(ligne_idx, 5, valeur_nouvelle)
                                    modifie = True
                                if po_original != po_assigne:
                                    ws_defense.update_cell(ligne_idx, 6, po_assigne)
                                    modifie = True
                                if a_original != a_assigne:
                                    ws_defense.update_cell(ligne_idx, 7, a_assigne)
                                    modifie = True
                                if e_original != e_assigne:
                                    ws_defense.update_cell(ligne_idx, 8, e_assigne)
                                    modifie = True
                                    
                                if modifie:
                                    mises_a_jour_def += 1
                                    
                    if lignes_a_ajouter_def:
                        ws_defense.append_rows(lignes_a_ajouter_def)
                        
                if lignes_a_ajouter_def or mises_a_jour_def > 0:
                    charger_donnees.clear()
                    messages = []
                    if lignes_a_ajouter_def: messages.append(f"{len(lignes_a_ajouter_def)} ajout(s)")
                    if mises_a_jour_def > 0: messages.append(f"{mises_a_jour_def} modification(s)")
                    st.success(f"✅ Défensive enregistrée avec succès : {' et '.join(messages)} !")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("ℹ️ Aucune modification détectée pour la défensive.")

# --- ONGLET 2 : STATISTIQUES ET JOURNAL ---
elif choix_menu == "📊 Journal & Stats":
    st.header("Journal des matchs")
    
    afficher_legende()
    
    if not presences_df.empty and not joueurs_df.empty and not parties_df.empty:
        st.subheader("🔍 Filtres")
        types_p = parties_df['type_match'].dropna().astype(str).unique()
        types_disponibles = ["Tous les matchs"] + sorted([t for t in types_p if t.strip() != ""])
        filtre_type = st.selectbox("Filtrer par type de match :", types_disponibles)
        
        # Fusion Pandas pour remplacer la requête SQL
        df_merged = pd.merge(presences_df, joueurs_df, left_on='joueur_id', right_on='id')
        
        # Ajout du type de match pour le filtre
        df_merged['partie_id_str'] = df_merged['partie_id'].astype(str)
        parties_df_safe = parties_df.copy()
        parties_df_safe['id_str'] = parties_df_safe['id'].astype(str)
        df_merged = pd.merge(df_merged, parties_df_safe[['id_str', 'type_match']], left_on='partie_id_str', right_on='id_str', how='left')
        
        if filtre_type != "Tous les matchs":
            df_merged = df_merged[df_merged['type_match'] == filtre_type]
            
        if df_merged.empty:
            st.info(f"ℹ️ Aucune donnée enregistrée pour les matchs de type : {filtre_type}.")
            st.stop() # Arrête le traitement de cet onglet pour éviter les erreurs
            
        df_merged['Joueur'] = df_merged['prenom'].astype(str) + " " + df_merged['nom'].astype(str)
        
        df_presences = df_merged[['Joueur', 'code_resultat', 'point_marque', 'points_produits', 'buts_voles']].rename(
            columns={'code_resultat': 'Action', 'point_marque': 'Points', 'points_produits': 'RBI', 'buts_voles': 'Vols'}
        )
        
        # ---------------------------------------------------------
        # Calcul des statistiques avancées avec Pandas
        # ---------------------------------------------------------
        
        # 1. Créer des colonnes temporaires pour catégoriser les actions
        df_presences['Est_1B'] = (df_presences['Action'] == '1B').astype(int)
        df_presences['Est_2B'] = (df_presences['Action'] == '2B').astype(int)
        df_presences['Est_3B'] = (df_presences['Action'] == '3B').astype(int)
        df_presences['Est_CC'] = (df_presences['Action'] == 'CC').astype(int)
        df_presences['Est_BB'] = (df_presences['Action'] == 'BB').astype(int)
        df_presences['Est_FA'] = (df_presences['Action'] == 'FA').astype(int)
        df_presences['Est_KE'] = (df_presences['Action'] == 'KE').astype(int)
        df_presences['Est_KD'] = (df_presences['Action'] == 'KD').astype(int)
        
        df_presences['Est_H'] = df_presences['Est_1B'] + df_presences['Est_2B'] + df_presences['Est_3B'] + df_presences['Est_CC']
        # Assure qu'une présence avec un Action vide (ex: pinch runner avec vols/points) ne compte pas comme un At-Bat officiel (AB)
        df_presences['Est_AB'] = (~df_presences['Action'].isin(['BB', 'FA', ''])).astype(int)
        # Un AB est une présence au marbre qui ne se termine PAS par un BB, FA, ou un sacrifice.
        df_presences['Est_AB'] = (~df_presences['Action'].isin(['BB', 'FA', 'SAC', ''])).astype(int)
        
        # 2. Grouper par joueur et faire les totaux
        stats_joueurs = df_presences.groupby('Joueur').agg(
            PA=('Action', 'count'), # Présences au marbre totales
            AB=('Est_AB', 'sum'),
            H=('Est_H', 'sum'),
            S=('Est_1B', 'sum'), # S pour Single, utilisé dans le calcul de TB
            D=('Est_2B', 'sum'), # D pour Double
            T=('Est_3B', 'sum'), # T pour Triple
            CC=('Est_CC', 'sum'),
            BB=('Est_BB', 'sum'),
            FA=('Est_FA', 'sum'),
            KE=('Est_KE', 'sum'),
            KD=('Est_KD', 'sum'),
            Points=('Points', 'sum'),
            RBI=('RBI', 'sum'),
            Buts_Voles=('Vols', 'sum')
        ).reset_index()
        
        # 3. Calculer les statistiques avancées
        stats_joueurs['K'] = stats_joueurs['KE'] + stats_joueurs['KD']
        
        # TB : Total des buts (Total Bases)
        stats_joueurs['TB'] = stats_joueurs['S'] + (2 * stats_joueurs['D']) + (3 * stats_joueurs['T']) + (4 * stats_joueurs['CC'])
        
        # AVG : Moyenne au bâton (Batting Average) = H / AB
        stats_joueurs['AVG'] = stats_joueurs.apply(lambda row: row['H'] / row['AB'] if row['AB'] > 0 else 0.0, axis=1)
        
        # OBP : Pourcentage de présence sur les buts (On-Base Percentage) = (H + BB + FA) / PA
        stats_joueurs['OBP'] = stats_joueurs.apply(lambda row: (row['H'] + row['BB'] + row['FA']) / row['PA'] if row['PA'] > 0 else 0.0, axis=1)
        
        # SLG : Moyenne de puissance (Slugging Percentage) = TB / AB
        stats_joueurs['SLG'] = stats_joueurs.apply(lambda row: row['TB'] / row['AB'] if row['AB'] > 0 else 0.0, axis=1)
        
        # OPS : Présence sur les buts + Puissance (On-Base Plus Slugging) = OBP + SLG
        stats_joueurs['OPS'] = stats_joueurs['OBP'] + stats_joueurs['SLG']
        
        # 4. Formatage de l'affichage des moyennes (ex: .333 au lieu de 0.33333)
        def formater_moyenne(val):
            val_arrondie = round(val, 3)
            if val_arrondie >= 1.0:
                return f"{val_arrondie:.3f}"
            else:
                return f"{val_arrondie:.3f}".replace('0.', '.')

        for col in ['AVG', 'OBP', 'SLG', 'OPS']:
            stats_joueurs[f'{col}_Format'] = stats_joueurs[col].apply(formater_moyenne)
        
        # ---------------------------------------------------------
        # SECTION PRO : Indicateurs clés (KPI) de l'équipe
        # ---------------------------------------------------------
        st.subheader("🔥 Vue d'ensemble de l'équipe")
        
        total_AB = stats_joueurs['AB'].sum()
        total_H = stats_joueurs['H'].sum()
        moyenne_equipe = total_H / total_AB if total_AB > 0 else 0
        
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        col_kpi1.metric(label="Moyenne globale (AVG)", value=f".{int(moyenne_equipe*1000):03d}" if moyenne_equipe < 1 else "1.000")
        col_kpi2.metric(label="Total des Points", value=stats_joueurs['Points'].sum())
        col_kpi3.metric(label="Coups Sûrs", value=total_H)
        col_kpi4.metric(label="Buts Volés", value=stats_joueurs['Buts_Voles'].sum())
        st.divider() # Ligne de séparation élégante
        
        # ---------------------------------------------------------
        # Affichage des tableaux dans Streamlit
        # ---------------------------------------------------------
        
        st.subheader(" Comparaison et Classement")
        
        metrics_dispo = {
            'Moyenne au bâton (AVG)': 'AVG',
            'Présence sur les buts (OBP)': 'OBP',
            'Puissance (SLG)': 'SLG',
            'OPS (OBP + SLG)': 'OPS',
            'Coups sûrs (H)': 'H',
            'Points produits (RBI)': 'RBI',
            'Points marqués (R)': 'Points',
            'Buts volés (SB)': 'Buts_Voles',
            'Coups de circuit (HR)': 'CC',
            'Retraits sur prises (K)': 'K'
        }
        
        stat_label = st.selectbox("Sélectionnez une statistique pour le graphique et le classement :", list(metrics_dispo.keys()))
        stat_col = metrics_dispo[stat_label]
        
        # 1. Trier les données numériques brutes pour le graphique et le classement
        stats_joueurs = stats_joueurs.sort_values(by=stat_col, ascending=False).reset_index(drop=True)
        
        # 2. Graphique à barres interactif
        st.bar_chart(stats_joueurs.set_index('Joueur')[[stat_col]], use_container_width=True)
        
        # Section A : Tableau de Classement complet
        st.subheader(f"🏆 Classement Complet (trié par {stat_label})")
        
        # On renomme et ordonne les colonnes pour l'affichage final
        df_affichage_stats = stats_joueurs[[
            'Joueur', 'PA', 'AB', 'Points', 'H', 'D', 'T', 'CC', 'RBI', 'BB', 'K', 'KE', 'KD', 'Buts_Voles',
            'AVG_Format', 'OBP_Format', 'SLG_Format', 'OPS_Format'
        ]].rename(
            columns={
                'PA': 'PA',
                'AB': 'AB',
                'Points': 'R',
                'H': 'H',
                'D': '2B',
                'T': '3B',
                'CC': 'HR',
                'RBI': 'RBI',
                'BB': 'BB',
                'K': 'K',
                'KE': 'KE',
                'KD': 'KD',
                'Buts_Voles': 'SB',
                'AVG_Format': 'AVG',
                'OBP_Format': 'OBP',
                'SLG_Format': 'SLG',
                'OPS_Format': 'OPS'
            }
        )
        
        # Ajouter une colonne "Rang" au tout début (1, 2, 3...)
        df_affichage_stats.insert(0, 'Rang', range(1, len(df_affichage_stats) + 1))
        
        st.dataframe(df_affichage_stats, use_container_width=True, hide_index=True)
        
        # Bouton d'exportation CSV pour le classement
        csv_stats = df_affichage_stats.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Télécharger le classement (CSV)",
            data=csv_stats,
            file_name='statistiques_joueurs_midget.csv',
            mime='text/csv',
        )

        # Section B : Journal historique des jeux
        st.subheader("📋 Journal historique des jeux")
        st.dataframe(df_presences[['Joueur', 'Action', 'Points', 'RBI', 'Vols']], use_container_width=True, hide_index=True)
        
        # Bouton d'exportation CSV pour le journal
        csv_journal = df_presences[['Joueur', 'Action', 'Points', 'RBI', 'Vols']].to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Télécharger le journal des présences (CSV)",
            data=csv_journal,
            file_name='journal_presences_midget.csv',
            mime='text/csv',
        )
        
    else:
        st.info("Aucune donnée enregistrée pour le moment. Allez à l'onglet Saisie pour enregistrer votre premier match !")

# --- ONGLET 3 : GESTION (AJOUT DE JOUEURS ET MATCHS) ---
elif choix_menu == "⚙️ Gestion":
    st.header("Gestion de l'équipe et des matchs")
    
    col_g1, col_g2 = st.columns(2)
    
    # -------------------------------------
    # GESTION DES JOUEURS
    # -------------------------------------
    with col_g1:
        st.subheader("👤 Joueurs")
        tab_ajout_j, tab_modif_j, tab_suppr_j = st.tabs(["Ajouter", "Modifier", "Supprimer"])
        
        with tab_ajout_j:
            with st.form("form_ajout_joueur", clear_on_submit=True):
                prenom = st.text_input("Prénom")
                nom = st.text_input("Nom")
                numero = st.number_input("Numéro de dossard", min_value=0, max_value=99, step=1)
                
                soumis_joueur = st.form_submit_button("Ajouter le joueur", type="primary", use_container_width=True)
                
                if soumis_joueur:
                    if prenom.strip() and nom.strip():
                        with st.spinner("Enregistrement du joueur..."):
                            ws_joueurs = sh.worksheet("joueurs")
                            nouvel_id_j = len(ws_joueurs.get_all_values())
                            ws_joueurs.append_row([nouvel_id_j, prenom.strip(), nom.strip(), numero])
                            
                        charger_donnees.clear()
                        st.success(f"✅ Joueur {prenom} {nom} ajouté !")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("⚠️ Veuillez remplir au moins le prénom et le nom.")
                        
        with tab_modif_j:
            if not dict_joueurs:
                st.info("Aucun joueur à modifier.")
            else:
                joueur_a_modifier = st.selectbox("Sélectionner un joueur à modifier", list(dict_joueurs.keys()), key="select_modif_j")
                j_id = dict_joueurs[joueur_a_modifier]
                j_row = joueurs_df[joueurs_df['id'] == j_id].iloc[0]
                
                with st.form("form_modif_joueur"):
                    nouveau_prenom = st.text_input("Prénom", value=str(j_row['prenom']))
                    nouveau_nom = st.text_input("Nom", value=str(j_row['nom']))
                    nouveau_numero = st.number_input("Numéro de dossard", min_value=0, max_value=99, step=1, value=int(j_row['numero_dossard'] or 0))
                    
                    soumis_modif_j = st.form_submit_button("Enregistrer les modifications", type="primary", use_container_width=True)
                    
                    if soumis_modif_j:
                        if nouveau_prenom.strip() and nouveau_nom.strip():
                            with st.spinner("Mise à jour du joueur..."):
                                ws_joueurs = sh.worksheet("joueurs")
                                # Trouver la ligne exacte (+2 car get_all_records exclut l'entête à la ligne 1)
                                row_idx = joueurs_df.index[joueurs_df['id'] == j_id].tolist()[0] + 2
                                ws_joueurs.update_cell(row_idx, 2, nouveau_prenom.strip())
                                ws_joueurs.update_cell(row_idx, 3, nouveau_nom.strip())
                                ws_joueurs.update_cell(row_idx, 4, nouveau_numero)
                                
                            charger_donnees.clear()
                            st.success(f"✅ Joueur modifié avec succès !")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("⚠️ Veuillez remplir au moins le prénom et le nom.")
                            
        with tab_suppr_j:
            if not dict_joueurs:
                st.info("Aucun joueur à supprimer.")
            else:
                joueur_a_supprimer = st.selectbox("Sélectionner un joueur à supprimer", list(dict_joueurs.keys()), key="select_suppr_j")
                j_id = dict_joueurs[joueur_a_supprimer]
                
                with st.form("form_suppr_joueur"):
                    st.warning("⚠️ Attention, cette suppression est irréversible.")
                    soumis_suppr_j = st.form_submit_button("Supprimer ce joueur")
                    
                    if soumis_suppr_j:
                        with st.spinner("Suppression du joueur..."):
                            ws_joueurs = sh.worksheet("joueurs")
                            row_idx = int(joueurs_df.index[joueurs_df['id'] == j_id].tolist()[0] + 2)
                            ws_joueurs.delete_rows(row_idx)
                            
                        charger_donnees.clear()
                        st.success("✅ Joueur supprimé avec succès !")
                        time.sleep(1)
                        st.rerun()
                    
    # -------------------------------------
    # GESTION DES MATCHS
    # -------------------------------------
    with col_g2:
        st.subheader("🏟️ Matchs")
        tab_ajout_m, tab_modif_m, tab_suppr_m = st.tabs(["Ajouter", "Modifier", "Supprimer"])
        
        with tab_ajout_m:
            with st.form("form_ajout_match", clear_on_submit=True):
                date_match = st.date_input("Date du match")
                equipe_adverse = st.text_input("Équipe adverse")
                lieu = st.text_input("Lieu (ex: Parc Laviolette)")
                type_match = st.selectbox("Type de match", ["Saison régulière", "Séries", "Tournoi", "Hors-concours"])
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    resultat = st.selectbox("Résultat", ["À venir", "Victoire (W)", "Défaite (L)", "Égalité (T)", "Annulée"])
                with col_r2:
                    pointage = st.text_input("Pointage (ex: 5-3)")

                soumis_match = st.form_submit_button("Créer le match", type="primary", use_container_width=True)
                
                if soumis_match:
                    if equipe_adverse.strip():
                        with st.spinner("Création du match..."):
                            ws_parties = sh.worksheet("parties")
                            nouvel_id_p = len(ws_parties.get_all_values())
                            ws_parties.append_row([nouvel_id_p, str(date_match), equipe_adverse.strip(), lieu.strip(), type_match, resultat, pointage.strip()])
                            
                        charger_donnees.clear()
                        st.success(f"✅ Match contre {equipe_adverse} créé !")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("⚠️ Veuillez indiquer l'équipe adverse.")
                        
        with tab_modif_m:
            if not dict_parties:
                st.info("Aucun match à modifier.")
            else:
                match_a_modifier = st.selectbox("Sélectionner un match à modifier", list(dict_parties.keys()), key="select_modif_m")
                m_id = dict_parties[match_a_modifier]
                m_row = parties_df[parties_df['id'] == m_id].iloc[0]
                
                try:
                    current_date = datetime.datetime.strptime(str(m_row['date_match']), "%Y-%m-%d").date()
                except ValueError:
                    current_date = datetime.date.today()
                    
                types_match = ["Saison régulière", "Séries", "Tournoi", "Hors-concours"]
                current_type = str(m_row['type_match'])
                type_index = types_match.index(current_type) if current_type in types_match else 0
                
                resultats_possibles = ["À venir", "Victoire (W)", "Défaite (L)", "Égalité (T)", "Annulée"]
                current_resultat = str(m_row.get('resultat', 'À venir'))
                if current_resultat == 'nan' or current_resultat == '': current_resultat = 'À venir'
                res_index = resultats_possibles.index(current_resultat) if current_resultat in resultats_possibles else 0
                
                current_pointage = str(m_row.get('pointage', ''))
                if current_pointage == 'nan': current_pointage = ''

                with st.form("form_modif_match"):
                    nouvelle_date = st.date_input("Date du match", value=current_date)
                    nouvelle_equipe = st.text_input("Équipe adverse", value=str(m_row['equipe_adverse']))
                    nouveau_lieu = st.text_input("Lieu", value=str(m_row['lieu']))
                    nouveau_type = st.selectbox("Type de match", types_match, index=type_index)
                    
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        nouveau_resultat = st.selectbox("Résultat", resultats_possibles, index=res_index)
                    with col_r2:
                        nouveau_pointage = st.text_input("Pointage (ex: 5-3)", value=current_pointage)

                    soumis_modif_m = st.form_submit_button("Enregistrer les modifications", type="primary", use_container_width=True)
                    
                    if soumis_modif_m:
                        if nouvelle_equipe.strip():
                            with st.spinner("Mise à jour du match..."):
                                ws_parties = sh.worksheet("parties")
                                # Trouver la ligne exacte (+2)
                                row_idx = parties_df.index[parties_df['id'] == m_id].tolist()[0] + 2
                                ws_parties.update_cell(row_idx, 2, str(nouvelle_date))
                                ws_parties.update_cell(row_idx, 3, nouvelle_equipe.strip())
                                ws_parties.update_cell(row_idx, 4, nouveau_lieu.strip())
                                ws_parties.update_cell(row_idx, 5, nouveau_type)
                                ws_parties.update_cell(row_idx, 6, nouveau_resultat)
                                ws_parties.update_cell(row_idx, 7, nouveau_pointage.strip())
                                
                            charger_donnees.clear()
                            st.success(f"✅ Match modifié avec succès !")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("⚠️ Veuillez indiquer l'équipe adverse.") 
                            
        with tab_suppr_m:
            if not dict_parties:
                st.info("Aucun match à supprimer.")
            else:
                match_a_supprimer = st.selectbox("Sélectionner un match à supprimer", list(dict_parties.keys()), key="select_suppr_m")
                m_id = dict_parties[match_a_supprimer]
                
                with st.form("form_suppr_match"):
                    st.warning("⚠️ Attention, cette suppression est irréversible.")
                    soumis_suppr_m = st.form_submit_button("Supprimer ce match")
                    
                    if soumis_suppr_m:
                        with st.spinner("Suppression du match..."):
                            ws_parties = sh.worksheet("parties")
                            row_idx = int(parties_df.index[parties_df['id'] == m_id].tolist()[0] + 2)
                            ws_parties.delete_rows(row_idx)
                            
                        charger_donnees.clear()
                        st.success("✅ Match supprimé avec succès !")
                        time.sleep(1)
                        st.rerun()