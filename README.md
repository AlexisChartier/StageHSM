# Gestion des Données des Pluviomètres

## Objectifs du Projet

Ce projet vise à automatiser la gestion des données des pluviomètres en utilisant des scripts Python sur un serveur OVH. Les processus incluent la récupération des données brutes depuis un FTP, leur traitement, la calibration des données, la création de matrices creuses, et la mise à jour des données sur le FTP.

## Architecture du Projet

Le projet est structuré pour suivre les bonnes pratiques de programmation, y compris les principes SOLID, afin de garantir la modularité, la maintenabilité et l'efficacité. La structure est la suivante :

```

/process

    /modules

        calibration_module.py

        ftp_module.py

        processing_module.py

        utils.py

    main_process0.py

    main_process1_initial.py

    main_process1_light.py

```

### Détails des Modules

- **calibration_module.py** : Gère la calibration des données des pluviomètres.

- **ftp_module.py** : Gère les interactions FTP, y compris le téléchargement, l'upload et la suppression des fichiers.

- **processing_module.py** : Gère la concaténation des données, le traitement des données et la création des matrices creuses.

- **utils.py** : Contient des fonctions utilitaires pour la gestion des fichiers locaux.

### Processus Principaux

#### Processus 0 (copie de travail FTP)

- **Objectif** : Copier les fichiers des pluviomètres spécifiques du FTP de base vers un répertoire de cible sur le FTP sans duplication.

- **Description** : Ce processus se charge de copier les fichiers A0 (données brutes) sur le serveur FTP, en ne copiant que les pluviomètres Hydropolis et Polytech. À terme, les pluviomètres enverront directement les données vers le dossier « A ».

#### Processus 1 Initial (Traitement et concaténation)

- **Objectif** : Télécharger, concaténer, calibrer, traiter les données des pluviomètres puis les transférer vers le FTP.

- **Description** : Ce processus effectue les opérations initiales de traitement des données, y compris la concaténation des fichiers par année, la calibration des données et la création de matrices creuses. Les fichiers traités sont ensuite envoyés sur le FTP et les fichiers bruts sont supprimés après traitement.

#### Processus 1 Léger (Ajout et traitement des nouvelles données)

- **Objectif** : Ajouter les nouvelles données des pluviomètres aux fichiers concaténés et traités, et supprimer les données du FTP une fois traitées.

- **Description** : Ce processus est conçu pour être exécuté régulièrement afin de maintenir les données à jour. Il télécharge les nouvelles données, les ajoute aux fichiers existants, effectue les traitements nécessaires et met à jour les fichiers sur le FTP.
