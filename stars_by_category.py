import os
import requests
from collections import defaultdict
import re

# ——— CONFIGURATION ———
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # mettre votre token GitHub ici ou en variable d'env.

USERNAME = "spawnrider"  # votre login GitHub
CATEGORIES = {
    "Frontend": ["javascript", "typescript", "react", "vue", "angular", "css", "html"],
    "Backend": ["python", "java", "ruby", "go", "php", "node"],
    "IA": ["machine-learning", "deep-learning", "tensorflow", "pytorch", "keras", "nlp"],
    "Automation": ["automation", "devops", "ci", "cd", "docker", "ansible", "jenkins"],
    # Ajoutez autant de catégories que souhaité
}
MAX_PER_USR = 100  # nombre max de repos récupérés par page (API GitHub)
TOP_N = 10  # nombre à afficher par catégorie

# ——— FONCTIONS ———
def inject_into_readme(content, readme_path="README.md"):
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()

    new_section = f"<!-- START_STARS -->\n{content}\n<!-- END_STARS -->"
    updated_readme = re.sub(
        r"<!-- START_STARS -->.*?<!-- END_STARS -->",
        new_section,
        readme,
        flags=re.DOTALL
    )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_readme)
        
def get_starred(username, token):
    url = f"https://api.github.com/users/{username}/starred"
    headers = {"Authorization": f"token {token}"} if token else {}
    params = {"per_page": MAX_PER_USR, "page": 1}
    all_stars = []
    while True:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        all_stars.extend(data)
        params["page"] += 1
    return all_stars

def categorize(repo):
    topics = repo.get("topics", []) or []
    lang = repo.get("language") or ""
    langs = [lang.lower()]
    tags = topics + langs
    for category, keywords in CATEGORIES.items():
        if any(k.lower() in tags for k in keywords):
            return category
    return "Autres"

def build_tables(starred_list):
    groups = defaultdict(list)
    for r in starred_list:
        cat = categorize(r)
        groups[cat].append(r)
    tables = {}
    for cat, repos in groups.items():
        repos_sorted = sorted(repos, key=lambda r: r["stargazers_count"], reverse=True)[:TOP_N]
        md = ["| Nom | ⭐ Stars | Langage | Description |",
              "| --- | ---: | --- | --- |"]
        for r in repos_sorted:
            name = f"[{r['full_name']}]({r['html_url']})"
            stars = r["stargazers_count"]
            lang = r.get("language") or ""
            desc = (r.get("description") or "").replace("\n", " ")
            md.append(f"| {name} | {stars} | {lang} | {desc} |")
        tables[cat] = "\n".join(md)
    return tables

# ——— EXÉCUTION ———
if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("Veillez à définir la variable d'environnement GITHUB_TOKEN.")
        exit(1)

    starred = get_starred(USERNAME, GITHUB_TOKEN)
    tables = build_tables(starred)
    markdown = ""
    for cat, table in tables.items():
        markdown += f"\n### {cat}\n\n{table}\n"
    inject_into_readme(markdown)
