import base64
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Plateforme Scouting Handball U18",
    page_icon="🤾‍♀️",
    layout="wide",
)

EXCEL_FILE = "data_handball.xlsx"


@st.cache_data
def load_data():
  if not os.path.exists(EXCEL_FILE):
    return pd.DataFrame()
  df = pd.read_excel(EXCEL_FILE, sheet_name="DATA_MATCHS").fillna(0)

  # Agrégation par joueuse
  df_grouped = (
      df.groupby(["Nom_Joueuse", "Competition"], as_index=False)
      .agg({
          "Type_Poste": "first",
          "Pays": "first",
          "Min_Jouees": ["count", "sum"],
          "Buts": "sum",
          "Passes_D": "sum",
          "Tirs_Bloques": "sum",
          "Sanctions_2min": "sum",
          "Arrets": "sum",
          "Tirs_Subis": "sum",
      })
  )

  # Aplatir les colonnes
  df_grouped.columns = [
      "Nom_Joueuse",
      "Competition",
      "Type_Poste",
      "Pays",
      "Matchs_Joues",
      "Min_Totales",
      "Buts",
      "Passes_D",
      "Tirs_Bloques",
      "Sanctions_2min",
      "Arrets",
      "Tirs_Subis",
  ]

  # Métriques calculées
  df_grouped["Implication"] = df_grouped["Buts"] + df_grouped["Passes_D"]
  df_grouped["Pct_Arrets"] = np.where(
      df_grouped["Tirs_Subis"] > 0,
      (df_grouped["Arrets"] / df_grouped["Tirs_Subis"]) * 100,
      0,
  )
  df_grouped["Buts_PM"] = (
      df_grouped["Buts"] / df_grouped["Matchs_Joues"]
  ).round(1)
  df_grouped["PassesD_PM"] = (
      df_grouped["Passes_D"] / df_grouped["Matchs_Joues"]
  ).round(1)
  df_grouped["Impl_PM"] = (
      df_grouped["Implication"] / df_grouped["Matchs_Joues"]
  ).round(1)
  df_grouped["Arrets_PM"] = (
      df_grouped["Arrets"] / df_grouped["Matchs_Joues"]
  ).round(1)

  return df_grouped


df = load_data()

st.title("🤾‍♀️ Hub de Détection & Scouting Handball U18")
st.markdown(
    "Filtrez les meilleures joueuses selon vos critères statistiques et accédez"
    " directement à leurs fiches."
)

if df.empty:
  st.warning("Aucune donnée trouvée. Veuillez d'abord exécuter l'extraction.")
  st.stop()

# --- BARRE LATÉRALE : FILTRES ---
st.sidebar.header("🎯 Filtres de Recherche")

poste_filter = st.sidebar.selectbox("Poste", ["Tous", "CHAMP", "GARDIENNE"])
liste_pays = ["Tous"] + sorted([p for p in df["Pays"].unique() if str(p) != "0"])
pays_filter = st.sidebar.selectbox("Pays / Sélection", liste_pays)

min_matchs = st.sidebar.slider(
    "Nombre minimum de matchs joués", 1, int(df["Matchs_Joues"].max()), 3
)

# Application des filtres de base
df_filtered = df[df["Matchs_Joues"] >= min_matchs]
if poste_filter != "Tous":
  df_filtered = df_filtered[df_filtered["Type_Poste"] == poste_filter]
if pays_filter != "Tous":
  df_filtered = df_filtered[df_filtered["Pays"] == pays_filter]

# --- CRITÈRE DE TRI ---
st.sidebar.header("📊 Critère de Classement")
if poste_filter == "GARDIENNE":
  criteres = {
      "% d'Arrêts": "Pct_Arrets",
      "Arrêts Totaux": "Arrets",
      "Arrêts par Match": "Arrets_PM",
      "Passes D / Relances": "Passes_D",
  }
else:
  criteres = {
      "Meilleures Buteuses (Total)": "Buts",
      "Buts par Match": "Buts_PM",
      "Implication Totale (Buts + Passes D)": "Implication",
      "Assists / Passes Décisives": "Passes_D",
      "Tirs Bloqués (Contres)": "Tirs_Bloques",
      "Discipline (Moins de 2min)": "Sanctions_2min",
  }

tri_choisi = st.sidebar.selectbox("Classer par", list(criteres.keys()))
colonne_tri = criteres[tri_choisi]
ordre_asc = True if "Moins" in tri_choisi else False

top_n = st.sidebar.slider("Afficher le Top :", 5, 50, 10)

# Tri final
df_top = df_filtered.sort_values(
    by=colonne_tri, ascending=ordre_asc
).reset_index(drop=True)
df_top.index += 1  # Rang commence à 1

# --- AFFICHAGE DU CLASSEMENT ---
st.subheader(f"🏆 Top {top_n} — {tri_choisi}")

# Sélection des colonnes visibles
colonnes_visibles = [
    "Nom_Joueuse",
    "Pays",
    "Type_Poste",
    "Matchs_Joues",
    "Buts",
    "Buts_PM",
    "Passes_D",
    "Implication",
    "Tirs_Bloques",
    "Sanctions_2min",
]
if poste_filter == "GARDIENNE":
  colonnes_visibles = [
      "Nom_Joueuse",
      "Pays",
      "Matchs_Joues",
      "Arrets",
      "Arrets_PM",
      "Pct_Arrets",
      "Passes_D",
      "Sanctions_2min",
  ]

st.dataframe(df_top[colonnes_visibles].head(top_n), use_container_width=True)

# --- SECTION TÉLÉCHARGEMENT FICHE PDF ---
st.markdown("---")
st.subheader("📄 Consulter le rapport complet d'une joueuse")

col1, col2 = st.columns([2, 1])

with col1:
  joueuse_selectionnee = st.selectbox(
      "Sélectionner une joueuse parmi les résultats :",
      df_top["Nom_Joueuse"].head(top_n).tolist(),
  )

with col2:
  if joueuse_selectionnee:
    comp = df_top[df_top["Nom_Joueuse"] == joueuse_selectionnee][
        "Competition"
    ].iloc[0]
    p_clean = (
        joueuse_selectionnee.replace(" ", "_")
        .encode("ascii", "ignore")
        .decode("utf-8")
    )
    c_clean = comp.replace(" ", "_").encode("ascii", "ignore").decode("utf-8")
    pdf_filename = f"Rapport_{p_clean}_{c_clean}.pdf"

    if os.path.exists(pdf_filename):
      with open(pdf_filename, "rb") as f:
        st.download_button(
            label=f"⬇️ Télécharger la fiche de {joueuse_selectionnee}",
            data=f,
            file_name=pdf_filename,
            mime="application/pdf",
        )
    else:
      st.info(
          "Fiche PDF non trouvée. Lancez `generer_rapport.py` pour la créer."
      )
