# Générateur de flux RSS

Ce dépôt contient un script Python qui génère **trois flux RSS distincts** à partir d’un **unique flux podcast source** :

- **Intégrale** : épisodes complets, préfixés par `L'INTÉGRALE`
- **Best-of (Extras)** : épisodes sélectionnés, préfixés par `MEILLEUR DE LA SAISON`, `BEST OF` ou `MOMENT CULTE`
- **Épisodes restants** : tous les autres épisodes non inclus ci-dessus

Chaque flux est enrichi d’une **jaquette personnalisée** et d’un **résumé de chaîne**.

---

## 📦 Structure du dépôt

```
GTRSS/
├── keep_integrale.py         # Script principal de génération des flux RSS
├── only_integrale_feed.xml   # Flux RSS Intégrale généré
├── only_best_feed.xml        # Flux RSS Best-of généré
├── only_remaining_feed.xml   # Flux RSS Restants généré
├── grosses-tetes-style.xsl   # Affichage navigateur des flux Grosses Têtes
├── Integrales.jpg            # Jaquette du flux Intégrale
├── Extras.jpg                # Jaquette du flux Best-of
└── README.md                 # Cette documentation
```

## ⚙️ Configuration

Tous les réglages se trouvent en tête de `keep_integrale.py` :

- `feed_url` : URL du flux RSS source  
- `output_integrale`, `output_best`, `output_remaining` : noms des fichiers de sortie  
- `integrale_pref`, `best_prefs` : préfixes de titre utilisés pour le filtrage  
- `integrale_image_url`, `best_image_url` : URLs GitHub brutes des jaquettes  
- `integrale_summary`, `best_summary`, `remaining_summary` : résumés des chaînes

Mettez ces valeurs à jour avant d’exécuter le script.

## 🚀 Utilisation

1. **Installer la dépendance** :

   ```bash
   pip install requests
   ```

2. **Lancer le script** :

   ```bash
   python keep_integrale.py
   ```

3. **Résultat** :

   - Trois fichiers RSS sont créés/mis à jour à la racine du dépôt.
   - Les flux Grosses Têtes référencent `grosses-tetes-style.xsl` pour un affichage lisible dans le navigateur.
   - Si de nouveaux éléments sont détectés, le script affiche un récapitulatif et peut, en option, **commit & push** les changements.

## 🤖 Intégration continue

Ce dépôt peut être intégré à **GitHub Actions** :

- Exécuter `keep_integrale.py` à intervalle régulier (ex. horaire/quotidien)
- Committer et pousser les flux RSS mis à jour sur `main`

Consultez `.github/workflows/ci.yml` (si présent) pour un exemple de configuration.

## 🤝 Contributions

Vous pouvez ouvrir des *issues* ou *pull requests* pour :

- Ajuster les règles/préfixes de filtrage  
- Modifier le formatage des flux ou la gestion des espaces de noms XML  
- Améliorer la gestion des erreurs et les logs  
- Ajouter la prise en charge d’autres flux personnalisés

## 📄 Licence

Projet distribué sous licence **MIT**. Voir [LICENSE](LICENSE) pour les détails.
