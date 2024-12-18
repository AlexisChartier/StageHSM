# Projet Pluvio Montpellier - Verdanson Pluie

Ce dépôt contient l'ensemble des scripts, applications Shiny et outils de traitement nécessaires à la gestion et à l'analyse des données de pluviométrie sur le bassin versant du Verdanson à Montpellier.

## Contenu du dépôt

- **VerdansonPluie** : Application Shiny permettant de visualiser et d'analyser les cumuls de pluie sur le Verdanson sur les 7 derniers jours.  
  - Affiche une carte avec interpolation spatiale (IDW) des cumuls, des bulles proportionnelles à l'intensité, et un masque pour limiter la zone d'étude.
  - Permet le téléchargement des données journalières, ainsi que la modification du pas de temps (15min, 30min, 1h, 2h, 4h, 12h, 24h, 48h, 72h).
  - Un script `cumul_process.py` génère quotidiennement les fichiers de cumul (Pluvio_Mtp_AAA_YYYYMMDD.csv) à partir des fichiers concaténés de données brutes.

- **gestionPluvio** : Application Shiny dédiée à l'analyse plus générale des cumuls de pluie sur une période à choix par l'utilisateur.  
  - L'utilisateur sélectionne une période avec un pas de 5 minutes.
  - Le script `generate_cumul_total.py` est appelé pour générer un fichier cumul (Pluvio_Cumul_Total_YYYYMMDDHHMM_YYYYMMDDHHMM.csv) contenant le cumul total sur la période sélectionnée.
  - Un seuil de données manquantes est paramétrable, permettant de filtrer les stations affichées.
  - L'application offre la possibilité de générer un graphique de l'intensité et du cumul pour une station choisie, ainsi que de télécharger les données.

- **main_process.py** : Script Python principal pour la récupération et le traitement des données brutes depuis un FTP, leur concaténation, le calibrage, et la génération de matrices creuses (HDF5 et MTX) pour chaque station et chaque année.  
  - Télécharge les données brutes depuis le FTP (Pluvio_Urbain).
  - Concatène les données au format CSV (un fichier par année et par station).
  - Applique une calibration des données.
  - Génère également une matrice creuse en format HDF5 et MTX pour un usage avancé.
  - Met en place un système de backup hebdomadaire des fichiers concaténés.

- **cumul_process.py** : Script Python utilisé par l'application VerdansonPluie pour générer les cumuls quotidiens sur les 7 derniers jours.  
  - Télécharge les fichiers concaténés pour toutes les stations.
  - Pour chaque journée des 7 derniers jours, génère un fichier cumul (Pluvio_Mtp_AAA_YYYYMMDD.csv).
  - Traite les dates et les données manquantes, limite l'intégration aux données de l'année en cours, et s'assure du formatage final.

## Structure du dépôt

- `VerdansonPluie/` : Contient l'application Shiny VerdansonPluie, le script `cumul_process.py` et les fichiers CSV résultants.
- `gestionPluvio/` : Contient l'application Shiny pour l'analyse des pluies sur une période définie par l'utilisateur, ainsi que le script `generate_cumul_total.py`.
- `src/` : Contient les scripts Python `main_process.py`, `calibration_module.py`, `ftp_module.py`, et autres modules nécessaires.
- `temp/` : Répertoires temporaires pour stocker les données brutes, concaténées et traitées.
- `out/` : Répertoire de sortie pour les données calibrées et matrices creuses (HDF5, MTX).
- `backup/` : Répertoire pour les backups hebdomadaires des fichiers concaténés.
- `www/` : Contient les ressources statiques (images, scripts JavaScript) pour les applications Shiny.

## Dépendances et Installation

- **R Packages** :  
  - shiny, leaflet, dplyr, raster, sp, gstat, shinyscreenshot, rgdal, png, tidyr, shinyWidgets, lubridate, ggplot2, shinycssloaders
- **Python Packages** :  
  - pandas, numpy, h5py, scipy, pytz
- **Outils externes** :  
  - Un accès au FTP hydrosciences avec les variables d'environnement `FTP_HOST`, `FTP_USER`, `FTP_PASS`.
  - Python 3.x et R 4.x recommandés.

## Usage

- **Application VerdansonPluie** :  
  Lancer l'application Shiny via `R -e "shiny::runApp('VerdansonPluie')"` ou placer le dossier VerdansonPluie dans un serveur Shiny. Le script `cumul_process.py` doit être exécuté en tâche cron pour générer les données quotidiennes.

- **Application gestionPluvio** :  
  Lancer l'application Shiny via `R -e "shiny::runApp('gestionPluvio')"` ou placer le dossier gestionPluvio dans un serveur Shiny. Le script `generate_cumul_total.py` est appelé par l'application lors du clic sur le bouton "Générer".

- **main_process.py** :  
  Lancé régulièrement en tâche cron pour récupérer et traiter les données brutes, calibrer les données, générer les concaténés annuels mis à jour, les fichiers traités, et les matrices creuses.

