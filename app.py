from flask import Flask, request, render_template
import os
import spacy
import language_tool_python
import fitz 

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

nlp = spacy.load("pt_core_news_sm")
tool = language_tool_python.LanguageTool('pt-BR')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file and file.filename.endswith('.pdf'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return analyze_text(filepath)
    return "No valid file uploaded", 400

def analyze_text(filepath):
    text = extract_text_from_pdf(filepath)
    
    matches = tool.check(text)
    corrected_text = language_tool_python.utils.correct(text, matches)
    
    doc = nlp(text)
    cohesion_score = calculate_cohesion(doc)
    coherence_score = calculate_coherence(doc)

    report = {
        "original_text": text,
        "corrected_text": corrected_text,
        "cohesion_score": cohesion_score,
        "coherence_score": coherence_score
    }
    
    return render_template('report.html', report=report)

def extract_text_from_pdf(filepath):
    text = ""
    with fitz.open(filepath) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def calculate_cohesion(doc):
    connectives = {'e', 'mas', 'porém', 'entretanto', 'ou', 'porque', 'portanto', 'assim', 'também'}
    pronouns = {'ele', 'ela', 'isso', 'aquilo', 'meu', 'minha', 'seu', 'sua', 'nós', 'vocês'}
    
    cohesion_count = sum(1 for token in doc if token.text.lower() in connectives or token.text.lower() in pronouns)
    return cohesion_count / len(doc) if len(doc) > 0 else 0

def calculate_coherence(doc):
    sentences = list(doc.sents)
    topic_count = 0
    for i in range(len(sentences) - 1):
        if sentences[i].root.head == sentences[i + 1].root.head:
            topic_count += 1
    return topic_count / len(sentences) if len(sentences) > 0 else 0

if __name__ == '__main__':
    app.run(debug=True)