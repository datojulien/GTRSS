# RSS Feed Generator

This repository contains a Python script to generate three separate RSS feeds from a single source podcast feed:

* **Integrale**: Full episodes prefixed with `L'INTÉGRALE`
* **Best-of (Extras)**: Selected episodes prefixed with `MEILLEUR DE LA SAISON`, `BEST OF`, or `MOMENT CULTE`
* **Remaining Episodes**: All other episodes not included above

Each feed is enriched with custom cover art and channel summaries.

---

## 📦 Repository Structure

```
GTRSS/
├── keep_integrale.py         # Main script to generate RSS feeds
├── only_integrale_feed.xml   # Generated Integrale RSS
├── only_best_feed.xml        # Generated Best-of RSS
├── only_remaining_feed.xml   # Generated Remaining RSS
├── Integrales.jpg            # Cover art for Integrale feed
├── Extras.jpg                # Cover art for Best-of feed
└── README.md                 # This documentation file
```

## ⚙️ Configuration

All settings live at the top of `keep_integrale.py`:

* `feed_url`: Source RSS URL
* `output_integrale`, `output_best`, `output_remaining`: Output filenames
* `integrale_pref`, `best_prefs`: Title prefixes to filter
* `integrale_image_url`, `best_image_url`: Raw GitHub URLs for cover art
* `integrale_summary`, `best_summary`, `remaining_summary`: Channel summaries

Update these values as needed before running the script.

## 🚀 Usage

1. **Install dependencies**:

   ```bash
   pip install requests
   ```
2. **Run the script**:

   ```bash
   python keep_integrale.py
   ```
3. **Output**:

   * Three RSS files will be created/updated in the repository root.
   * If new items are found, the script prints a summary and can optionally commit & push changes.

## 🤖 Continuous Integration

This repo can be integrated into a GitHub Actions workflow:

* On a schedule (e.g. hourly/daily) run `keep_integrale.py`
* Commit and push updated RSS files to `main`

See `.github/workflows/ci.yml` (if present) for an example CI configuration.

## 🤝 Contributing

Feel free to open issues or pull requests to:

* Adjust filtering rules or prefixes
* Change feed formatting or XML namespace handling
* Improve error handling and logging
* Add support for additional custom feeds

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.
