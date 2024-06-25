# Gestion des Données des Pluviomètres

## Objectifs du Projet

Ce projet vise à automatiser la gestion des données des pluviomètres en utilisant des scripts Python sur un serveur OVH. Les processus incluent la récupération des données brutes depuis un FTP, leur traitement, la calibration des données, la création de matrices creuses, et la mise à jour des données sur le FTP.

## Architecture du Projet

Le projet est structuré pour suivre les bonnes pratiques de programmation, y compris les principes SOLID, afin de garantir la modularité, la maintenabilité et l'efficacité. La structure est la suivante :

```

/src

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

#### Processus 2 (copie données traitées format matrice creuse)

- **Objectif** : Sauvegarde des fichiers traités matrice creuse sur le FTP.

- **Description** : Ce processus est conçu pour être exécuté 1 fois par jour. Il récupère les fichiers de données traités et au format matrice creuse et l'enregistre sur le ftp en supprimant les fichiers précédemment enregistrés.






### Guide d'accès à OVH via SSH, Interaction avec l'environnement Linux, Utilisation de CRON et Activation d'un Environnement Virtuel

---

#### **1. Accéder à OVH via SSH**

**Étape 1: Obtenez les informations de connexion SSH**

- Adresse IP ou nom de domaine du serveur OVH.

- Nom d'utilisateur SSH.

- Mot de passe SSH (ou clé SSH pour une connexion sécurisée).

**Étape 2: Installez un client SSH**

- Sur Windows, utilisez [PuTTY](https://www.putty.org/).

- Sur macOS ou Linux, utilisez le terminal intégré.

**Étape 3: Connectez-vous au serveur**

- Sur macOS ou Linux, ouvrez le Terminal et entrez :

  ```

  ssh username@server_ip

  ```

  Remplacez `username` par votre nom d'utilisateur SSH et `server_ip` par l'adresse IP du serveur OVH.

- Sur Windows, ouvrez PuTTY :

  1. Entrez l'adresse IP du serveur dans le champ "Host Name (or IP address)".

  2. Cliquez sur "Open".

  3. Entrez votre nom d'utilisateur et mot de passe lorsque vous y êtes invité.

---

#### **2. Interactions de base avec l'environnement Linux**

**Commandes de navigation :**

- `pwd` : Afficher le répertoire de travail actuel.

- `ls` : Lister les fichiers dans le répertoire actuel.

- `cd directory_name` : Changer de répertoire.

- `cd ..` : Revenir au répertoire parent.

**Commandes de gestion des fichiers et répertoires :**

- `mkdir directory_name` : Créer un nouveau répertoire.

- `touch file_name` : Créer un nouveau fichier vide.

- `cp source destination` : Copier un fichier ou répertoire.

- `mv source destination` : Déplacer ou renommer un fichier ou répertoire.

- `rm file_name` : Supprimer un fichier.

- `rm -r directory_name` : Supprimer un répertoire et son contenu.

**Commandes de gestion des permissions :**

- `chmod permissions file_name` : Modifier les permissions d'un fichier ou répertoire. Exemple : `chmod 755 script.sh`.

- `chown user:group file_name` : Changer le propriétaire d'un fichier ou répertoire.

**Commandes d'édition de fichiers :**

- `nano file_name` : Ouvrir et éditer un fichier avec l'éditeur Nano.

- `vi file_name` : Ouvrir et éditer un fichier avec l'éditeur Vi.

---

#### **3. Activation d'un Environnement Virtuel et Lancement Manuel d'un Script**

**Étape 1: Créer un environnement virtuel**

- Si vous n'avez pas encore créé un environnement virtuel, utilisez la commande suivante :

  ```

  python3 -m venv myenv

  ```

**Étape 2: Activer l'environnement virtuel**

- Sur macOS ou Linux :

  ```

  source myenv/bin/activate

  ```

- Sur Windows :

  ```

  myenv\Scripts\activate

  ```

**Étape 3: Installer les dépendances nécessaires**

- Assurez-vous que votre environnement virtuel est activé et installez les dépendances nécessaires :

  ```

  pip install -r requirements.txt

  ```

**Étape 4: Lancer manuellement un script**

- Exécutez votre script Python dans l'environnement virtuel activé :

  ```

  python script_name.py

  ```

**Étape 5: Désactiver l'environnement virtuel**

- Pour désactiver l'environnement virtuel, utilisez la commande suivante :

  ```

  deactivate

  ```

---

#### **4. Utilisation de CRON**

**Étape 1: Comprendre CRON**

CRON est un service Linux qui exécute des tâches planifiées à des intervalles spécifiques. Les tâches planifiées sont définies dans le fichier crontab.

**Étape 2: Ouvrir le fichier crontab**

Pour éditer le crontab pour l'utilisateur actuel, exécutez :

```

crontab -e

```

La première fois, vous devrez peut-être choisir un éditeur de texte (Nano est recommandé pour les débutants).

**Étape 3: Syntaxe du fichier crontab**

Chaque ligne dans le crontab représente une tâche planifiée et suit cette syntaxe :

```

* * * * * command_to_run

- - - - -

| | | | |

| | | | ----- Jour de la semaine (0 - 7) (dimanche est 0 ou 7)

| | | ------- Mois (1 - 12)

| | --------- Jour du mois (1 - 31)

| ----------- Heure (0 - 23)

------------- Minute (0 - 59)

```

**Exemple :**

- Exécuter un script chaque jour à minuit :

  ```

  0 0 * * * /usr/bin/python3 /path/to/script.py

  ```

- Exécuter un script toutes les heures :

  ```

  0 * * * * /usr/bin/python3 /path/to/script.py

  ```

- Exécuter un script chaque lundi à 8 heures du matin :

  ```

  0 8 * * 1 /usr/bin/python3 /path/to/script.py

  ```

**Étape 4: Utiliser un environnement virtuel avec CRON**

- Pour utiliser un environnement virtuel avec CRON, spécifiez l'activation de l'environnement virtuel avant d'exécuter le script. Par exemple :

  ```

  0 0 * * * /bin/bash -c 'source /path/to/myenv/bin/activate && /usr/bin/python /path/to/script.py'

  ```

**Étape 5: Sauvegarder et quitter**

Après avoir édité le fichier crontab, sauvegardez les modifications et quittez l'éditeur (par exemple, dans Nano, utilisez `Ctrl+O` pour sauvegarder et `Ctrl+X` pour quitter).

**Étape 6: Vérifier les tâches CRON**

Pour lister les tâches CRON actuelles, utilisez :

```

crontab -l

```

Pour supprimer toutes les tâches CRON de l'utilisateur actuel :

```

crontab -r

```

**Étape 7: Vérifier l'exécution des tâches**

Les tâches CRON envoient par défaut un e-mail à l'utilisateur pour chaque commande exécutée. Vous pouvez rediriger la sortie des commandes vers un fichier pour les vérifier plus tard :

```

0 0 * * * /bin/bash -c 'source /path/to/myenv/bin/activate && /usr/bin/python /path/to/script.py' >> /path/to/logfile 2>&1

```

