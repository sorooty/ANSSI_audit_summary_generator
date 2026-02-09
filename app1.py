"""
app_atelier1.py
Interface Streamlit RiskHunter - Optimisation Audits ANSSI
Lancement : streamlit run app_atelier1.py
"""

import streamlit as st
import json
from pathlib import Path
from typing import List
from dataclasses import dataclass, asdict
from datetime import datetime
import os
import base64
from dotenv import load_dotenv

# charger les variables d'environnement depuis un fichier .env
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
    page_title="RiskHunter - Atelier 1 ANSSI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Chargement CSS personnalisé
def load_css():
    css_file = Path("style.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning("Fichier style.css introuvable - styles par défaut appliqués")

load_css()

# Constantes
NON_COMPLIANT_LEVELS = ["partially", "no"]
CHAPTER_ID_TO_ROMAN = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V",
    "6": "VI", "7": "VII", "8": "VIII", "9": "IX", "10": "X"
}

# Référentiel ANSSI (version compacte pour l'interface)
ANSSI_FRAMEWORK = {
    "I": {"title": "I - Sensibiliser et former", "requirements": {
        "1.1": {"title": "Former les équipes opérationnelles", "description": "Formations continues sur risques, authentification, durcissement..."},
        "1.2": {"title": "Sensibiliser les utilisateurs", "description": "Sensibilisation régulière, charte informatique signée..."},
        "1.3": {"title": "Maîtriser l'infogérance", "description": "Évaluer risques, exigences contractuelles, surveillance prestataire..."}
    }},
    "II": {"title": "II - Connaître le SI", "requirements": {
        "2.1": {"title": "Schéma réseau et actifs sensibles", "description": "Cartographie complète, inventaire exhaustif..."},
        "2.2": {"title": "Inventaire comptes à privilèges", "description": "Inventaire nominatif, revue périodique..."},
        "2.3": {"title": "Gestion cycle de vie utilisateurs", "description": "Procédures arrivées/départs, droits d'accès..."},
        "2.4": {"title": "Équipements maîtrisés uniquement", "description": "Interdire équipements personnels, Wi-Fi isolé..."}
    }},
    "III": {"title": "III - Authentifier et contrôler", "requirements": {
        "3.1": {"title": "Moindre privilège", "description": "Droits strictement nécessaires..."},
        "3.2": {"title": "Restreindre ressources sensibles", "description": "Contrôle d'accès strict..."},
        "3.3": {"title": "Mots de passe robustes", "description": "12+ caractères, complexité..."},
        "3.4": {"title": "Authentification forte MFA", "description": "MFA pour accès distant et privilèges..."},
        "3.5": {"title": "Changer éléments par défaut", "description": "Identifiants/mots de passe par défaut..."},
        "3.6": {"title": "Journaliser comptes privilèges", "description": "Centralisation logs, conservation 6 mois..."}
    }},
    "IV": {"title": "IV - Postes de travail", "requirements": {
        "4.1": {"title": "Niveau sécurité minimal", "description": "Pare-feu, antivirus, chiffrement..."},
        "4.2": {"title": "Protection supports amovibles", "description": "Sensibilisation, blocage USB..."},
        "4.3": {"title": "Gestion centralisée", "description": "GPO, MDM..."},
        "4.4": {"title": "Pare-feu local", "description": "Activé, liste blanche..."},
        "4.5": {"title": "Chiffrement transmissions", "description": "HTTPS, SFTP, S/MIME..."}
    }},
    "V": {"title": "V - Réseau", "requirements": {
        "5.1": {"title": "Segmentation réseau", "description": "VLANs, zones de confiance..."},
        "5.2": {"title": "Contrôle flux", "description": "Matrice de flux, deny all..."},
        "5.3": {"title": "Protocoles sécurisés", "description": "HTTPS, SSH, SFTP..."},
        "5.4": {"title": "Passerelle Internet", "description": "Proxy, filtrage, DMZ..."},
        "5.5": {"title": "Sécuriser Wi-Fi", "description": "WPA3, 802.1X..."},
        "5.6": {"title": "Protéger messagerie", "description": "Anti-spam, TLS, SPF/DKIM/DMARC..."},
        "5.7": {"title": "Interconnexions partenaires", "description": "VPN IPsec, matrice flux..."},
        "5.8": {"title": "Accès physiques salles serveurs", "description": "Badges, biométrie, vidéosurveillance..."}
    }},
    "VI": {"title": "VI - Administration", "requirements": {
        "6.1": {"title": "Interdire Internet admin", "description": "Pas d'accès Internet direct..."},
        "6.2": {"title": "Réseau dédié admin", "description": "VLAN dédié, cloisonné..."},
        "6.3": {"title": "Limiter comptes admin", "description": "Minimum utilisateurs, RBAC..."}
    }},
    "VII": {"title": "VII - Nomadisme", "requirements": {
        "7.1": {"title": "Sensibilisation nomadisme", "description": "Risques vol, perte..."},
        "7.2": {"title": "Chiffrement nomades", "description": "BitLocker, FileVault..."},
        "7.3": {"title": "VPN nomadisme", "description": "VPN IPsec, MFA..."},
        "7.4": {"title": "Messagerie nomade", "description": "IMAPS, MDM, remote wipe..."}
    }},
    "VIII": {"title": "VIII - Mises à jour", "requirements": {
        "8.1": {"title": "Politique mises à jour", "description": "Processus qualification/déploiement..."},
        "8.2": {"title": "Déployer correctifs", "description": "Critiques <1 mois, autres <3 mois..."}
    }},
    "IX": {"title": "IX - Superviser", "requirements": {
        "9.1": {"title": "Journalisation", "description": "Centralisation, protection logs..."},
        "9.2": {"title": "Politique sauvegarde", "description": "Hors ligne, tests restauration..."},
        "9.3": {"title": "Audits réguliers", "description": "Annuels, plan actions..."},
        "9.4": {"title": "Référent SSI", "description": "RSSI désigné, moyens..."},
        "9.5": {"title": "Gestion incidents", "description": "Procédure formalisée, CERT..."}
    }},
    "X": {"title": "X - Plus loin", "requirements": {
        "10.1": {"title": "Analyse de risques", "description": "EBIOS RM, ISO 27005..."},
        "10.2": {"title": "Produits qualifiés ANSSI", "description": "CSPN, PASSI, PRIS, PDIS..."}
    }}
}

@dataclass
class DeficiencySummary:
    requirement_id: str
    requirement_title: str
    compliance_level: str
    summary: str

# Fonctions utilitaires
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
    """
    Génère un résumé structuré d'une défaillance ANSSI via GPT-4o.
    
    Args:
        deficiency: Dictionnaire contenant les détails de la défaillance
        api_key: Clé API OpenAI
        
    Returns:
        Résumé texte (4-5 lignes) ou message d'erreur
    """
    if not OPENAI_AVAILABLE:
        return "Erreur : Module OpenAI non disponible"
    
    client = OpenAI(api_key=api_key)
    
    # Construction du contexte structuré
    requirement_id = deficiency.get('requirement_id', 'N/A')
    requirement_title = deficiency.get('requirement_title', 'N/A')
    compliance_level = deficiency.get('compliance_level', 'N/A')
    justification = deficiency.get('justification', 'Not specified')
    gap_description = deficiency.get('gap_description', 'Not specified')
    induced_risks = deficiency.get('induced_risks', 'Not specified')
    action_plan = deficiency.get('action_plan', 'Not specified')
    
    # System prompt (rôle + contraintes)
    system_prompt = """You are a senior cybersecurity auditor specialized in ANSSI (French National Cybersecurity Agency) compliance frameworks.

Your task is to generate concise, factual summaries of security deficiencies for executive reporting.

Output requirements:
- Write in French
- Maximum 4-5 lines (100 words max)
- Focus on: what is missing, concrete risks, required actions
- Use professional, non-alarmist tone
- Be specific and actionable"""

    # User prompt (données + instructions)
    user_prompt = f"""Analyze this ANSSI compliance deficiency and provide a concise executive summary:

**Requirement**: {requirement_id} - {requirement_title}
**Compliance Level**: {compliance_level}
**Justification**: {justification[:500]}
**Gap Description**: {gap_description[:500]}
**Induced Risks**: {induced_risks[:500]}
**Action Plan**: {action_plan[:500]}

Generate a 4-5 line summary in French covering:
1. What specific control is deficient
2. Main security gap identified
3. Primary risk exposure
4. Recommended remediation priority

Summary:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300,
            top_p=0.95,
            frequency_penalty=0.2,
            presence_penalty=0.1
        )
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Erreur API OpenAI : {str(e)}"


def generate_executive_synthesis(summaries_text: str, api_key: str, total_deficiencies: int = 0) -> str:
    """
    Génère une synthèse exécutive globale via GPT-4o.
    
    Args:
        summaries_text: Agrégation de tous les résumés individuels
        api_key: Clé API OpenAI
        total_deficiencies: Nombre total de défaillances
        
    Returns:
        Synthèse exécutive (25-30 lignes) ou message d'erreur
    """
    if not OPENAI_AVAILABLE:
        return "Erreur : Module OpenAI non disponible"
    
    client = OpenAI(api_key=api_key)
    
    # Limitation de la taille du contexte (éviter dépassement tokens)
    summaries_truncated = summaries_text[:8000]
    
    # System prompt
    system_prompt = """You are a Chief Information Security Officer (CISO) preparing an executive summary for the board of directors.

Your task is to synthesize multiple cybersecurity audit findings into a high-level strategic assessment.

Output requirements:
- Write in French
- 25-30 lines maximum (500 words)
- Structure: Current posture → Critical domains → Priority risks → Strategic recommendations
- Use executive language (avoid technical jargon)
- Provide actionable insights with business impact context
- Maintain neutral, objective tone"""

    # User prompt
    user_prompt = f"""Based on the following {total_deficiencies} ANSSI compliance deficiencies, create a strategic executive summary:

---
{summaries_truncated}
---

Generate a 15-20 line executive summary in French structured as follows:

1. **Overall Security Posture** (2-3 lines): Current compliance maturity level, general assessment

2. **Critical Domains** (4-5 lines): Top 3 security domains with most significant gaps (e.g., access control, network security, training)

3. **Priority Risks** (4-5 lines): Most severe risks to business operations, data confidentiality, regulatory compliance

4. **Strategic Recommendations** (4-5 lines): Top 3 remediation priorities with estimated effort/impact ratio

Focus on business impact and strategic decision-making, not technical details.

Executive Summary:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=800,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.2
        )
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Erreur API OpenAI : {str(e)}"


# ========== INTERFACE ==========

# Header avec logo
col_logo, col_title = st.columns([1, 4])
with col_logo:
    logo_path = Path("assets/RiskHunterLogo.jpg")
    if logo_path.exists():
        st.image(str(logo_path), width=120)
with col_title:
    st.title("🛡️ RiskHunter - Atelier 1 ANSSI")
    st.markdown("**Optimisation d'audits cybersécurité avec IA**")

st.markdown("---")

# Sidebar
with st.sidebar:
    # st.image("https://via.placeholder.com/250x80/1a2332/00D4AA?text=RiskHunter", use_container_width=True)
    
    st.header("⚙️ Configuration")
    
    api_key = st.text_input("🔑 Clé API OpenAI", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    
    if not api_key:
        st.warning("⚠️ Clé API requise")
    elif not OPENAI_AVAILABLE:
        st.error("❌ Module openai non installé")
    else:
        st.success("✅ Prêt")
    
    st.markdown("---")
    
    st.markdown("### 📋 Référentiel")
    st.info(f"""
    **Framework** : ANSSI Hygiène v2.0  
    **Exigences** : {sum(len(c['requirements']) for c in ANSSI_FRAMEWORK.values())}  
    **Chapitres** : 10
    """)
    
    st.markdown("---")
    
    st.markdown("### 📖 Guide")
    with st.expander("ℹ️ Comment utiliser"):
        st.markdown("""
        **Étape 1** : Charger JSON audit  
        **Étape 2** : Extraire défaillances  
        **Étape 3** : Générer résumés IA  
        **Étape 4** : Télécharger résultats
        """)

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📤 Import & Extraction", "🤖 Génération Résumés", "📊 Résultats"])

# ========== TAB 1: IMPORT ==========
with tab1:
    st.header("📤 Import du JSON d'audit ANSSI")
    
    uploaded_file = st.file_uploader(
        "📁 Glissez-déposez votre fichier JSON RiskHunter", 
        type=['json', 'txt'],
        help="Format accepté : JSON d'audit RiskHunter"
    )
    
    if uploaded_file:
        try:
            audit_data = json.load(uploaded_file)
            
            if isinstance(audit_data, list):
                audit_data = audit_data[0]
            
            st.success(f"✅ Audit chargé : **{audit_data.get('title', 'Sans titre')}**")
            
            # Métadonnées
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👤 Client", audit_data.get('customerName', 'N/A'))
            with col2:
                st.metric("📅 Début", audit_data.get('startDate', 'N/A'))
            with col3:
                st.metric("📅 Fin", audit_data.get('endDate', 'N/A'))
            with col4:
                st.metric("📋 Type", audit_data.get('type', 'N/A'))
            
            st.markdown("---")
            st.subheader("🔍 Extraction des défaillances")
            
            if st.button("🚀 Lancer l'extraction", type="primary", use_container_width=True):
                with st.spinner("⏳ Analyse en cours..."):
                    deficiencies = extract_deficiencies(audit_data)
                    st.session_state['deficiencies'] = deficiencies
                    st.session_state['audit_data'] = audit_data
                
                st.success(f"✅ **{len(deficiencies)} défaillances** identifiées")
                
                # Statistiques
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Total", len(deficiencies), delta=None)
                with col2:
                    no_count = sum(1 for d in deficiencies if d['compliance_level'] == 'no')
                    st.metric("❌ Non conforme", no_count, delta=f"-{no_count}", delta_color="inverse")
                with col3:
                    partial_count = sum(1 for d in deficiencies if d['compliance_level'] == 'partially')
                    st.metric("⚠️ Partiel", partial_count, delta=f"-{partial_count}", delta_color="inverse")
                
                # Aperçu
                st.markdown("---")
                st.markdown("### 👁️ Aperçu des défaillances")
                
                for i, def_item in enumerate(deficiencies[:5]):
                    severity_emoji = "❌" if def_item['compliance_level'] == 'no' else "⚠️"
                    with st.expander(f"{severity_emoji} **{def_item['requirement_id']}** - {def_item['requirement_title']}"):
                        st.markdown(f"**🎯 Conformité** : `{def_item['compliance_level']}`")
                        st.markdown(f"**📝 Justification** : {def_item['justification'][:300]}...")
                
                if len(deficiencies) > 5:
                    st.info(f"💡 **{len(deficiencies) - 5}** autres défaillances disponibles")
        
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement : `{str(e)}`")

# ========== TAB 2: GÉNÉRATION ==========
with tab2:
    st.header("🤖 Génération des résumés IA")
    
    if 'deficiencies' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord extraire les défaillances dans l'onglet **Import & Extraction**")
    elif not api_key:
        st.warning("⚠️ Veuillez saisir votre clé API OpenAI dans la sidebar")
    elif not OPENAI_AVAILABLE:
        st.error("❌ Module OpenAI non installé. Exécutez : `pip install openai`")
    else:
        deficiencies = st.session_state['deficiencies']
        
        st.info(f"🎯 **{len(deficiencies)} défaillances** prêtes pour traitement IA")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            **Modèle** : GPT-4o  
            **Tokens estimés** : ~{len(deficiencies) * 300}  
            **Durée estimée** : ~{len(deficiencies) * 2}s
            """)
        with col2:
            if st.button("🚀 Générer", type="primary", use_container_width=True):
                summaries = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, deficiency in enumerate(deficiencies):
                    status_text.markdown(f"⏳ **Traitement {i+1}/{len(deficiencies)}** : `{deficiency['requirement_id']}`")
                    progress_bar.progress((i + 1) / len(deficiencies))
                    
                    summary_text = generate_summary_gpt4o(deficiency, api_key)
                    
                    summaries.append(DeficiencySummary(
                        requirement_id=deficiency['requirement_id'],
                        requirement_title=deficiency['requirement_title'],
                        compliance_level=deficiency['compliance_level'],
                        summary=summary_text
                    ))
                
                st.session_state['summaries'] = summaries
                status_text.empty()
                progress_bar.empty()
                
                st.success(f"✅ **{len(summaries)} résumés** générés avec succès")
                
                # Aperçu
                st.markdown("---")
                st.markdown("### 👁️ Aperçu des résumés IA")
                
                for summary in summaries[:3]:
                    severity_emoji = "❌" if summary.compliance_level == 'no' else "⚠️"
                    with st.expander(f"{severity_emoji} **{summary.requirement_id}** - {summary.requirement_title}"):
                        st.markdown(summary.summary)
                
                if len(summaries) > 3:
                    st.info(f"💡 **{len(summaries) - 3}** autres résumés disponibles")

# ========== TAB 3: RÉSULTATS ==========
with tab3:
    st.header("📊 Résultats et Export")
    
    if 'summaries' not in st.session_state:
        st.warning("⚠️ Veuillez d'abord générer les résumés dans l'onglet **Génération Résumés**")
    elif not api_key:
        st.warning("⚠️ Veuillez saisir votre clé API OpenAI")
    else:
        summaries = st.session_state['summaries']
        
        # Synthèse exécutive
        st.subheader("📝 Synthèse exécutive")
        
        if st.button("🧠 Générer la synthèse globale", type="primary", use_container_width=True):
            with st.spinner("⏳ Génération de la synthèse exécutive..."):
                aggregated = "\n\n".join([
                    f"[{s.requirement_id}] {s.requirement_title}\n{s.summary}"
                    for s in summaries
                ])
                
                executive_synthesis = generate_executive_synthesis(aggregated, api_key)
                st.session_state['executive_synthesis'] = executive_synthesis
            
            st.success("✅ Synthèse exécutive générée")
        
        if 'executive_synthesis' in st.session_state:
            st.markdown("---")
            st.markdown("### 📋 Synthèse Exécutive")
            st.info(st.session_state['executive_synthesis'])
            
            # Export
            st.markdown("---")
            st.subheader("💾 Téléchargements")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # JSON optimisé
                cleaned_data = {
                    "schema_version": "1.0",
                    "audit_metadata": {
                        "framework": "ANSSI Hygiène v2.0",
                        "generation_date": datetime.now().isoformat(),
                        "total_deficiencies": len(summaries)
                    },
                    "deficiencies": [
                        {
                            "requirement_id": s.requirement_id,
                            "requirement_title": s.requirement_title,
                            "compliance_level": s.compliance_level,
                            "summary": s.summary
                        }
                        for s in summaries
                    ],
                    "executive_synthesis": st.session_state['executive_synthesis']
                }
                
                st.download_button(
                    label="📥 JSON Optimisé",
                    data=json.dumps(cleaned_data, ensure_ascii=False, indent=2),
                    file_name=f"RH_survey_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                # Résumés TXT
                full_text = "RISKHUNTER - AUDIT ANSSI - SYNTHÈSE DES DÉFAILLANCES\n" + "="*80 + "\n\n"
                for s in summaries:
                    full_text += f"[{s.requirement_id}] {s.requirement_title}\n"
                    full_text += f"{s.summary}\n" + "-"*80 + "\n\n"
                
                st.download_button(
                    label="📥 Résumés TXT",
                    data=full_text,
                    file_name=f"RH_summaries_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col3:
                # Synthèse Markdown
                md_content = f"""# Synthèse Exécutive - Audit ANSSI
**Framework** : ANSSI Hygiène v2.0  
**Date** : {datetime.now().strftime('%Y-%m-%d')}  
**Défaillances** : {len(summaries)}

---

{st.session_state['executive_synthesis']}
"""
                
                st.download_button(
                    label="📥 Synthèse MD",
                    data=md_content,
                    file_name=f"RH_synthesis_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # Métriques
            st.markdown("---")
            st.subheader("📈 Métriques d'optimisation")
            
            if 'audit_data' in st.session_state:
                original_size = len(json.dumps(st.session_state['audit_data']))
                cleaned_size = len(json.dumps(cleaned_data))
                compression = (1 - cleaned_size/original_size) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📦 Original", f"{original_size/1024:.1f} KB")
                with col2:
                    st.metric("✨ Optimisé", f"{cleaned_size/1024:.1f} KB")
                with col3:
                    st.metric("💾 Compression", f"{compression:.1f}%", delta=f"-{compression:.0f}%")
                with col4:
                    st.metric("🎯 Résumés", len(summaries))

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #00D4AA; font-size: 0.9rem;'>
    🛡️ <strong>RiskHunter</strong> | Powered by AI & ANSSI Framework v2.0  
    <em style='color: #f0f4f8;'>Optimisation d'audits cybersécurité</em>
</div>
""", unsafe_allow_html=True)
