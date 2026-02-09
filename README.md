# RiskHunter - Atelier 1 : Optimisation d'Audits ANSSI

Application Streamlit pour la génération automatique de résumés d'audits cybersécurité ANSSI via LLM (ChatGPT 4o).

## Contexte

**Mission** : Transformer un JSON d'audit volumineux (300+ pages) en résumés exploitables pour les ateliers suivants (maturité, risques, conformité).

**Framework** : ANSSI Guide d'hygiène informatique v2.0 (10 chapitres, 42 exigences)

**Stack technique** : Python 3.10+, Streamlit, OpenAI GPT-4o

---

## Installation

### Prérequis

- Python 3.10 ou supérieur
- Clé API OpenAI (GPT-4o)
- 2 Go RAM minimum

### Setup rapide

```bash
# 1. Cloner le projet
git clone <repo-url>
cd riskhunter_atelier1

# 2. Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Installer dépendances
pip install -r requirements.txt

# 4. Configurer clé API
export OPENAI_API_KEY="sk-..."  # Linux/Mac
set OPENAI_API_KEY=sk-...       # Windows
