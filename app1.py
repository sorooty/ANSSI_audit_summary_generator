"""
app_atelier1_v2.py
Interface Streamlit RiskHunter - Optimisation Audits ANSSI v2.0
Lancement : streamlit run app_atelier1_v2.py

Nouveautés v2.0:
- Liste dynamique ANSSI avec filtres
- Graphiques Plotly interactifs
- Heatmap de conformité
- Distribution par chapitre
- Affichages améliorés
"""

import streamlit as st
import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

# Charger .env
load_dotenv()

os.environ['STREAMLIT_SERVER_ENABLE_STATIC_SERVING'] = 'true'

# Configuration OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configuration Streamlit
st.set_page_config(
    page_title="RiskHunter - Atelier 1 ANSSI v2.0",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Chargement CSS
def load_css():
    css_file = Path("style.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Constantes
NON_COMPLIANT_LEVELS = ["partially", "no"]
CHAPTER_ID_TO_ROMAN = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V",
    "6": "VI", "7": "VII", "8": "VIII", "9": "IX", "10": "X"
}

# Référentiel ANSSI complet
ANSSI_FRAMEWORK = {
    "I": {
        "title": "I - Sensibiliser et former",
        "requirements": {
            "1.1": {
                "title": "Former les équipes opérationnelles à la sécurité des SI",
                "description": "Formations initiales et continues adaptées aux métiers sur risques, authentification, durcissement, cloisonnement, journalisation."
            },
            "1.2": {
                "title": "Sensibiliser les utilisateurs aux bonnes pratiques",
                "description": "Sensibilisation régulière aux enjeux de sécurité, RGPD, consignes quotidiennes. Charte informatique signée."
            },
            "1.3": {
                "title": "Maîtriser les risques liés à l'infogérance",
                "description": "Évaluer les risques, exigences de sécurité dans les contrats, surveillance du prestataire."
            }
        }
    },
    "II": {
        "title": "II - Connaître le système d'information",
        "requirements": {
            "2.1": {
                "title": "Maintenir un schéma du réseau et identifier les actifs sensibles",
                "description": "Cartographie complète : inventaire actifs, données sensibles, flux réseau, schéma à jour."
            },
            "2.2": {
                "title": "Tenir l'inventaire des comptes à privilèges",
                "description": "Inventaire nominatif et à jour avec revue périodique. Nomenclature claire."
            },
            "2.3": {
                "title": "Gérer les arrivées, départs et changements de fonctions",
                "description": "Procédures formalisées de gestion du cycle de vie : création/suppression comptes, droits d'accès."
            },
            "2.4": {
                "title": "Autoriser la connexion aux seuls équipements maîtrisés",
                "description": "Interdire équipements non autorisés. Wi-Fi invités isolé. Authentification réseau (802.1X)."
            }
        }
    },
    "III": {
        "title": "III - Authentifier et contrôler les accès",
        "requirements": {
            "3.1": {
                "title": "Attribuer les droits selon le moindre privilège",
                "description": "Droits strictement nécessaires. Séparation comptes nominatifs et privilégiés."
            },
            "3.2": {
                "title": "Restreindre l'accès aux ressources sensibles",
                "description": "Lister ressources sensibles, populations autorisées, contrôle d'accès strict."
            },
            "3.3": {
                "title": "Définir des règles de mots de passe robustes",
                "description": "Longueur minimale 12 caractères, complexité, blocage après échecs multiples."
            },
            "3.4": {
                "title": "Privilégier une authentification forte (MFA)",
                "description": "MFA pour accès distant, comptes privilégiés, ressources sensibles."
            },
            "3.5": {
                "title": "Changer les éléments d'authentification par défaut",
                "description": "Changer systématiquement identifiants/mots de passe par défaut."
            },
            "3.6": {
                "title": "Journaliser l'activité des comptes à privilèges",
                "description": "Centraliser journalisation, protéger logs, conserver 6 mois minimum."
            }
        }
    },
    "IV": {
        "title": "IV - Sécuriser les postes de travail",
        "requirements": {
            "4.1": {
                "title": "Établir un niveau de sécurité minimal du parc",
                "description": "Pare-feu, anti-virus, chiffrement partitions, désactiver autorun."
            },
            "4.2": {
                "title": "Protéger le parc des supports amovibles",
                "description": "Sensibilisation, interdiction clés USB inconnues, solutions techniques (AppLocker)."
            },
            "4.3": {
                "title": "Gérer de manière centralisée les politiques de sécurité",
                "description": "GPO Active Directory ou MDM pour homogénéiser configurations."
            },
            "4.4": {
                "title": "Activer le pare-feu local des postes",
                "description": "Bloquer par défaut, logique liste blanche, journalisation."
            },
            "4.5": {
                "title": "Chiffrer les données avant transmission Internet",
                "description": "Chiffrement systématique, protocoles sécurisés (HTTPS, SFTP, S/MIME)."
            }
        }
    },
    "V": {
        "title": "V - Sécuriser le réseau",
        "requirements": {
            "5.1": {
                "title": "Segmenter le réseau en zones de confiance",
                "description": "VLANs, sous-réseaux, pare-feux entre zones."
            },
            "5.2": {
                "title": "Contrôler les flux réseaux",
                "description": "Matrice de flux, moindre privilège, bloquer par défaut."
            },
            "5.3": {
                "title": "Utiliser des protocoles réseau sécurisés",
                "description": "Remplacer HTTP, FTP, TELNET par HTTPS, SFTP, SSH."
            },
            "5.4": {
                "title": "Installer une passerelle sécurisée pour Internet",
                "description": "Proxy, filtrage contenus malveillants, DMZ."
            },
            "5.5": {
                "title": "Sécuriser les accès Wi-Fi",
                "description": "WPA3 ou WPA2-Enterprise avec 802.1X."
            },
            "5.6": {
                "title": "Protéger la messagerie électronique",
                "description": "Anti-spam, anti-virus, TLS, SPF/DKIM/DMARC."
            },
            "5.7": {
                "title": "Sécuriser les interconnexions avec partenaires",
                "description": "Tunnels IPsec conformes ANSSI, matrice de flux."
            },
            "5.8": {
                "title": "Contrôler les accès physiques aux salles serveurs",
                "description": "Badges, biométrie, vidéosurveillance, traçabilité."
            }
        }
    },
    "VI": {
        "title": "VI - Sécuriser l'administration",
        "requirements": {
            "6.1": {
                "title": "Interdire Internet depuis les postes d'administration",
                "description": "Pas d'accès direct Internet, mises à jour via serveurs internes."
            },
            "6.2": {
                "title": "Utiliser un réseau dédié pour l'administration",
                "description": "Réseau physiquement séparé ou VLAN cloisonné."
            },
            "6.3": {
                "title": "Limiter les comptes à privilèges d'administration",
                "description": "Minimum d'utilisateurs, délégation de droits spécifiques."
            }
        }
    },
    "VII": {
        "title": "VII - Gérer le nomadisme",
        "requirements": {
            "7.1": {
                "title": "Sensibiliser aux risques physiques des terminaux nomades",
                "description": "Vol, perte, espionnage visuel, verrouillage systématique."
            },
            "7.2": {
                "title": "Chiffrer les données sur terminaux nomades",
                "description": "Chiffrement complet disque (BitLocker, FileVault, LUKS)."
            },
            "7.3": {
                "title": "Utiliser un VPN pour les connexions nomades",
                "description": "VPN IPsec conforme ANSSI, MFA."
            },
            "7.4": {
                "title": "Sécuriser l'accès messagerie depuis terminaux nomades",
                "description": "Protocoles chiffrés, MFA, effacement à distance (MDM)."
            }
        }
    },
    "VIII": {
        "title": "VIII - Maintenir à jour",
        "requirements": {
            "8.1": {
                "title": "Définir une politique de mises à jour de sécurité",
                "description": "Inventaire composants, veille vulnérabilités, processus qualification/déploiement."
            },
            "8.2": {
                "title": "Mettre à jour régulièrement logiciels et systèmes",
                "description": "Correctifs critiques sous 1 mois, autres sous 3 mois."
            }
        }
    },
    "IX": {
        "title": "IX - Superviser, auditer, réagir",
        "requirements": {
            "9.1": {
                "title": "Journaliser et protéger les journaux",
                "description": "Centralisation logs, protection contre modification, conservation 6 mois."
            },
            "9.2": {
                "title": "Définir une politique de sauvegarde",
                "description": "Identifier données vitales, supports hors ligne, tests restauration."
            },
            "9.3": {
                "title": "Réaliser des audits réguliers",
                "description": "Audits annuels, plan d'actions correctives."
            },
            "9.4": {
                "title": "Désigner un référent SSI",
                "description": "RSSI avec moyens et prérogatives nécessaires."
            },
            "9.5": {
                "title": "Établir une procédure de gestion des incidents",
                "description": "Détection, qualification, traitement, REX formalisés."
            }
        }
    },
    "X": {
        "title": "X - Pour aller plus loin",
        "requirements": {
            "10.1": {
                "title": "Effectuer une analyse de risques formelle",
                "description": "Méthode reconnue (EBIOS RM, ISO 27005), mise à jour régulière."
            },
            "10.2": {
                "title": "Utiliser des produits qualifiés ANSSI",
                "description": "Produits et prestataires qualifiés (CSPN, PASSI, PRIS, PDIS)."
            }
        }
    }
}

@dataclass
class DeficiencySummary:
    requirement_id: str
    requirement_title: str
    compliance_level: str
    summary: str

# ========== FONCTIONS GRAPHIQUES ==========

def create_compliance_heatmap(deficiencies: List[dict]) -> go.Figure:
    """Crée une heatmap de conformité par chapitre."""
    chapter_data = {}
    for d in deficiencies:
        chapter = d['requirement_id'].split('.')[0]
        level = d['compliance_level']
        if chapter not in chapter_data:
            chapter_data[chapter] = {"no": 0, "partially": 0}
        chapter_data[chapter][level] += 1
    
    chapters = sorted(chapter_data.keys(), key=int)
    no_counts = [chapter_data[c]["no"] for c in chapters]
    partial_counts = [chapter_data[c]["partially"] for c in chapters]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Non conforme',
        x=[f"Chapitre {CHAPTER_ID_TO_ROMAN.get(c, c)}" for c in chapters],
        y=no_counts,
        marker_color='#ff6b6b',
        text=no_counts,
        textposition='auto'
    ))
    fig.add_trace(go.Bar(
        name='Partiellement conforme',
        x=[f"Chapitre {CHAPTER_ID_TO_ROMAN.get(c, c)}" for c in chapters],
        y=partial_counts,
        marker_color='#feca57',
        text=partial_counts,
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Distribution des Défaillances par Chapitre ANSSI",
        xaxis_title="Chapitres",
        yaxis_title="Nombre de défaillances",
        barmode='stack',
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f7fafc', size=12),
        height=400
    )
    return fig

def create_severity_pie(deficiencies: List[dict]) -> go.Figure:
    """Crée un pie chart des niveaux de sévérité."""
    severity_counts = Counter([d['compliance_level'] for d in deficiencies])
    
    fig = go.Figure(data=[go.Pie(
        labels=['Non conforme', 'Partiellement conforme'],
        values=[severity_counts.get('no', 0), severity_counts.get('partially', 0)],
        hole=0.4,
        marker_colors=['#ff6b6b', '#feca57'],
        textinfo='label+percent+value',
        textfont_size=14
    )])
    
    fig.update_layout(
        title="Répartition par Niveau de Conformité",
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f7fafc'),
        height=400,
        showlegend=True
    )
    return fig

def create_requirements_table(deficiencies: List[dict]) -> pd.DataFrame:
    """Crée un DataFrame pour affichage tableau."""
    data = []
    for d in deficiencies:
        data.append({
            "ID": d['requirement_id'],
            "Titre": d['requirement_title'],
            "Conformité": "❌ Non conforme" if d['compliance_level'] == 'no' else "⚠️ Partiel",
            "Risques": d['induced_risks'][:50] + "..." if len(d['induced_risks']) > 50 else d['induced_risks']
        })
    return pd.DataFrame(data)

# ========== FONCTIONS LLM ==========

def extract_deficiencies(audit_json: dict) -> List[dict]:
    """Extrait les défaillances du JSON audit."""
    deficiencies = []
    answers = audit_json.get('answers', {})
    
    for chapter_id, chapter_data in answers.items():
        roman_id = CHAPTER_ID_TO_ROMAN.get(chapter_id, chapter_id)
        requirements = chapter_data.get('_', {})
        
        for req_num, req_data in requirements.items():
            compliance = req_data.get('compliance', '')
            if compliance not in NON_COMPLIANT_LEVELS:
                continue
            
            requirement_id = f"{chapter_id}.{req_num}"
            anssi_chapter = ANSSI_FRAMEWORK.get(roman_id, {})
            anssi_req = anssi_chapter.get('requirements', {}).get(requirement_id, {})
            req_title = anssi_req.get('title', 'Exigence non référencée')
            
            justification = req_data.get('justification', '')
            gap_sheet = req_data.get('gapSheet', {})
            gap_obs = gap_sheet.get('gapObservation', {})
            gap_description = gap_obs.get('desc', '') if isinstance(gap_obs, dict) else ''
            
            action_plan_obj = gap_sheet.get('complianceActionPlan', {})
            action_plan = action_plan_obj.get('gapAnalysis', '') if isinstance(action_plan_obj, dict) else ''
            induced_risks = gap_sheet.get('inducedRisks', '')
            
            deficiencies.append({
                'requirement_id': requirement_id,
                'requirement_title': req_title,
                'compliance_level': compliance,
                'justification': justification,
                'gap_description': gap_description,
                'action_plan': action_plan,
                'induced_risks': induced_risks
            })
    
    return deficiencies

def generate_summary_gpt4o(deficiency: dict, api_key: str) -> str:
    """Génère un résumé via GPT-4o."""
    if not OPENAI_AVAILABLE:
        return "Erreur : Module OpenAI non disponible"
    
    client = OpenAI(api_key=api_key)
    
    system_prompt = """You are a senior cybersecurity auditor specialized in ANSSI compliance.

Output requirements:
- Write in French
- Maximum 4-5 lines (100 words)
- Focus on: gap, risk, action
- Professional tone"""

    user_prompt = f"""Analyze this ANSSI deficiency:

**Requirement**: {deficiency.get('requirement_id')} - {deficiency.get('requirement_title')}
**Compliance**: {deficiency.get('compliance_level')}
**Justification**: {deficiency.get('justification', '')[:500]}
**Gap**: {deficiency.get('gap_description', '')[:500]}
**Risks**: {deficiency.get('induced_risks', '')[:500]}
**Actions**: {deficiency.get('action_plan', '')[:500]}

Generate 4-5 line summary in French:
1. What is deficient
2. Main risk
3. Recommended action

Summary:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erreur : {str(e)}"

def generate_executive_synthesis(summaries_text: str, api_key: str, total: int = 0) -> str:
    """Génère synthèse exécutive."""
    if not OPENAI_AVAILABLE:
        return "Erreur : Module OpenAI non disponible"
    
    client = OpenAI(api_key=api_key)
    
    system_prompt = """You are a CISO preparing executive summary.

Output:
- French
- 25-30 lines (300 words)
- Structure: Posture → Domains → Risks → Recommendations
- Executive language"""

    user_prompt = f"""Based on {total} ANSSI deficiencies, create executive summary:

{summaries_text[:8000]}

Generate 15-20 line summary in French:
1. Overall Posture (2-3 lines)
2. Critical Domains (4-5 lines)
3. Priority Risks (4-5 lines)
4. Recommendations (4-5 lines)

Executive Summary:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erreur : {str(e)}"

# ========== INTERFACE ==========

# Header
col_logo, col_title = st.columns([1, 4])
with col_logo:
    logo_path = Path("assets/RiskHunterLogo.jpg")
    if logo_path.exists():
        st.image(str(logo_path), width=120)
with col_title:
    st.title("🛡️ RiskHunter - Atelier 1 ANSSI v2.0")
    st.markdown("**Optimisation d'audits cybersécurité avec IA + Analytics**")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("🔑 Clé API OpenAI", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    
    if not api_key:
        st.warning("⚠️ Clé API requise")
    elif not OPENAI_AVAILABLE:
        st.error("❌ Module openai non installé")
    else:
        st.success("✅ Prêt")
    
    st.markdown("---")
    st.markdown("### 📋 Référentiel ANSSI")
    
    # Liste dynamique des chapitres
    with st.expander("📖 Explorer les 10 Chapitres"):
        for chapter_id, chapter_info in ANSSI_FRAMEWORK.items():
            st.markdown(f"**{chapter_info['title']}**")
            for req_id, req_info in chapter_info['requirements'].items():
                st.markdown(f"- `{req_id}` {req_info['title']}")
                st.caption(req_info['description'])
            st.markdown("---")
    
    st.info(f"""
    **Total Exigences** : {sum(len(c['requirements']) for c in ANSSI_FRAMEWORK.values())}  
    **Chapitres** : 10
    """)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Import", "📊 Analytics", "🤖 Génération IA", "💾 Résultats"])

# ========== TAB 1: IMPORT ==========
with tab1:
    st.header("📤 Import & Extraction")
    uploaded_file = st.file_uploader("📁 Fichier JSON RiskHunter", type=['json', 'txt'])
    
    if uploaded_file:
        try:
            audit_data = json.load(uploaded_file)
            if isinstance(audit_data, list):
                audit_data = audit_data[0]
            
            st.success(f"✅ **{audit_data.get('title', 'Sans titre')}**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Client", audit_data.get('customerName', 'N/A'))
            with col2:
                st.metric("Début", audit_data.get('startDate', 'N/A'))
            with col3:
                st.metric("Fin", audit_data.get('endDate', 'N/A'))
            with col4:
                st.metric("Type", audit_data.get('type', 'N/A'))
            
            st.markdown("---")
            if st.button("🚀 Extraire Défaillances", type="primary", use_container_width=True):
                with st.spinner("Analyse..."):
                    deficiencies = extract_deficiencies(audit_data)
                    st.session_state['deficiencies'] = deficiencies
                    st.session_state['audit_data'] = audit_data
                
                st.success(f"✅ **{len(deficiencies)} défaillances** identifiées")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", len(deficiencies))
                with col2:
                    no_count = sum(1 for d in deficiencies if d['compliance_level'] == 'no')
                    st.metric("Non conforme", no_count, delta=f"-{no_count}", delta_color="inverse")
                with col3:
                    partial = sum(1 for d in deficiencies if d['compliance_level'] == 'partially')
                    st.metric("Partiel", partial, delta=f"-{partial}", delta_color="inverse")
        
        except Exception as e:
            st.error(f"❌ Erreur : `{str(e)}`")

# ========== TAB 2: ANALYTICS ==========
with tab2:
    st.header("📊 Analytics & Visualisations")
    
    if 'deficiencies' not in st.session_state:
        st.warning("⚠️ Extraire les défaillances d'abord")
    else:
        deficiencies = st.session_state['deficiencies']
        
        # Graphiques
        col1, col2 = st.columns(2)
        with col1:
            fig_heatmap = create_compliance_heatmap(deficiencies)
            st.plotly_chart(fig_heatmap, use_container_width=True)
        with col2:
            fig_pie = create_severity_pie(deficiencies)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📋 Liste Détaillée des Défaillances")
        
        # Filtres
        col1, col2 = st.columns(2)
        with col1:
            filter_compliance = st.multiselect(
                "Filtrer par conformité",
                options=["no", "partially"],
                default=["no", "partially"],
                format_func=lambda x: "❌ Non conforme" if x == "no" else "⚠️ Partiel"
            )
        with col2:
            chapters_available = sorted(set([d['requirement_id'].split('.')[0] for d in deficiencies]), key=int)
            filter_chapters = st.multiselect(
                "Filtrer par chapitre",
                options=chapters_available,
                default=chapters_available,
                format_func=lambda x: f"Chapitre {CHAPTER_ID_TO_ROMAN.get(x, x)}"
            )
        
        # Appliquer filtres
        filtered = [
            d for d in deficiencies
            if d['compliance_level'] in filter_compliance
            and d['requirement_id'].split('.')[0] in filter_chapters
        ]
        
        st.info(f"📊 **{len(filtered)}/{len(deficiencies)}** défaillances affichées")
        
        # Table
        df = create_requirements_table(filtered)
        st.dataframe(df, use_container_width=True, height=400)

# ========== TAB 3: GÉNÉRATION ==========
with tab3:
    st.header("🤖 Génération Résumés IA")
    
    if 'deficiencies' not in st.session_state:
        st.warning("⚠️ Extraire les défaillances d'abord")
    elif not api_key or not OPENAI_AVAILABLE:
        st.warning("⚠️ Configurer OpenAI")
    else:
        deficiencies = st.session_state['deficiencies']
        st.info(f"🎯 **{len(deficiencies)} défaillances** prêtes")
        
        if st.button("🚀 Générer Résumés IA", type="primary", use_container_width=True):
            summaries = []
            progress_bar = st.progress(0)
            status = st.empty()
            
            for i, d in enumerate(deficiencies):
                status.markdown(f"⏳ **{i+1}/{len(deficiencies)}** : `{d['requirement_id']}`")
                progress_bar.progress((i + 1) / len(deficiencies))
                
                summary = generate_summary_gpt4o(d, api_key)
                summaries.append(DeficiencySummary(
                    requirement_id=d['requirement_id'],
                    requirement_title=d['requirement_title'],
                    compliance_level=d['compliance_level'],
                    summary=summary
                ))
            
            st.session_state['summaries'] = summaries
            status.empty()
            progress_bar.empty()
            st.success(f"✅ **{len(summaries)} résumés** générés")

# ========== TAB 4: RÉSULTATS ==========
with tab4:
    st.header("💾 Résultats & Export")
    
    if 'summaries' not in st.session_state:
        st.warning("⚠️ Générer les résumés d'abord")
    elif not api_key:
        st.warning("⚠️ Clé API requise")
    else:
        summaries = st.session_state['summaries']
        
        if st.button("🧠 Synthèse Exécutive", type="primary", use_container_width=True):
            with st.spinner("Génération..."):
                text = "\n\n".join([f"[{s.requirement_id}] {s.requirement_title}\n{s.summary}" for s in summaries])
                synthesis = generate_executive_synthesis(text, api_key, len(summaries))
                st.session_state['executive_synthesis'] = synthesis
            st.success("✅ Synthèse générée")
        
        if 'executive_synthesis' in st.session_state:
            st.markdown("---")
            st.info(st.session_state['executive_synthesis'])
            
            st.markdown("---")
            st.subheader("💾 Téléchargements")
            
            col1, col2 = st.columns(2)
            with col1:
                cleaned_data = {
                    "schema_version": "1.0",
                    "audit_metadata": {
                        "framework": "ANSSI Hygiène v2.0",
                        "generation_date": datetime.now().isoformat(),
                        "total_deficiencies": len(summaries)
                    },
                    "deficiencies": [
                        {"requirement_id": s.requirement_id, "requirement_title": s.requirement_title,
                         "compliance_level": s.compliance_level, "summary": s.summary}
                        for s in summaries
                    ],
                    "executive_synthesis": st.session_state['executive_synthesis']
                }
                
                st.download_button(
                    "📥 JSON Optimisé",
                    data=json.dumps(cleaned_data, ensure_ascii=False, indent=2),
                    file_name=f"RH_survey_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                md_content = f"""# Synthèse Exécutive - Audit ANSSI
**Framework** : ANSSI Hygiène v2.0
**Date** : {datetime.now().strftime('%Y-%m-%d')}
**Défaillances** : {len(summaries)}

---

{st.session_state['executive_synthesis']}
"""
                st.download_button(
                    "📥 Synthèse MD",
                    data=md_content,
                    file_name=f"RH_synthesis_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #00D4AA;'>
    🛡️ <strong>RiskHunter v2.0</strong> | Powered by AI & ANSSI Framework  
    <em style='color: #f0f4f8;'>Analytics + Optimisation cybersécurité</em>
</div>
""", unsafe_allow_html=True)
