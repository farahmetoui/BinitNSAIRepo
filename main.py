from flask import Flask, request, jsonify
import json
import os
from langchain_community.llms import Ollama 
from jinja2 import Template
from weasyprint import HTML
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Chemin local où sont stockés les rapports JSON
DOSSIER_REPORTS = "C:/Users/binitns/Desktop/backendProject/backendProject/Downloads"

def generer_pdf_depuis_url(url_rapport_json: str) -> str:
    # On extrait le nom du fichier depuis l'URL
    nom_fichier_json = url_rapport_json.split("/reports/")[-1]
    chemin_json = os.path.join(DOSSIER_REPORTS, nom_fichier_json)

    if not os.path.exists(chemin_json):
        raise FileNotFoundError(f"File not found : {chemin_json}")

    # Nom final du PDF
    nom_pdf = nom_fichier_json.replace(".json", "-normalReport.pdf")
    chemin_pdf = os.path.join(DOSSIER_REPORTS, nom_pdf)

    #  Si le PDF existe déjà, on le retourne directement
    if os.path.exists(chemin_pdf):
        return chemin_pdf

    # Charger le fichier JSON
    with open(chemin_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extraire les scores et capture d'écran
    perf = int(data["categories"]["performance"]["score"] * 100)
    access = int(data["categories"]["accessibility"]["score"] * 100)
    seo = int(data["categories"]["seo"]["score"] * 100)
    best = int(data["categories"]["best-practices"]["score"] * 100)
    screenshot_base64 = data["audits"]["final-screenshot"]["details"]["data"]

    # Construire le prompt pour Mistral
    prompt = (
    "Please summarize this Lighthouse report in clear English for a non-technical client. "
    "Add a line break after each metric to improve readability.\n"
    f"1. Performance: {perf}/100\n"
    f"2. Accessibility: {access}/100\n"
    f"3. SEO: {seo}/100\n"
    f"4. Best Practices: {best}/100\n"
)


    # Générer le résumé avec Ollama
    # Générer le résumé avec Ollama
if os.environ.get("CI") == "true":
    resume = "Résumé fictif généré pour les tests CI"
else:
    llm = Ollama(model="mistral")
    resume = llm(prompt)


    # Charger le template HTML
    with open("template.html", "r", encoding="utf-8") as f:
        template = Template(f.read())
    
    texte_html = resume.replace("\n", "<br>")
    # Remplir le template
    html_result = template.render(
        perf=perf,
        access=access,
        seo=seo,
        best=best,
        texte=texte_html,
        screenshot=screenshot_base64
    )

    # Écrire le HTML temporaire
    with open("rapport_temp.html", "w", encoding="utf-8") as f:
        f.write(html_result)

    # Générer le PDF
    HTML("rapport_temp.html").write_pdf(chemin_pdf)

    return chemin_pdf

@app.route("/generer-pdf", methods=["POST"])
def generer_pdf():
    data = request.get_json()
    url_rapport = data.get("url")

    if not url_rapport:
        return jsonify({"error": "URL manquante"}), 400

    try:
        chemin_pdf = generer_pdf_depuis_url(url_rapport)
        public_url = "/reports/" + os.path.basename(chemin_pdf)
        return jsonify({"chemin_pdf": chemin_pdf, "public_url": public_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
