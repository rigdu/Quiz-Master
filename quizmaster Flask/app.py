from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import pandas as pd
import os
import json

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
SCORE_FILE = 'score_stats.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

data = pd.DataFrame()
filtered_data = pd.DataFrame()
scores = {}
used_questions = set()
current_file = None

@app.route('/')
def index():
    global data, current_file
    filename = request.args.get('file')
    if filename:
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(path):
            data = pd.read_excel(path)
            current_file = filename
            rounds = sorted(data['Round'].dropna().unique())
            types = sorted(data['Type'].dropna().unique())
            subtypes = sorted(data['Sub Type'].dropna().unique())
            return render_template('index.html', rounds=rounds, types=types, subtypes=subtypes, filename=filename)
    return render_template('index.html', rounds=[], types=[], subtypes=[], filename=None)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return redirect(url_for('index', file=file.filename))
    return redirect(url_for('index'))

@app.route('/filter', methods=['POST'])
def filter_questions():
    global data, filtered_data
    filters = request.json
    filtered_data = data.copy()
    if filters['round']:
        filtered_data = filtered_data[filtered_data['Round'] == filters['round']]
    if filters['type']:
        filtered_data = filtered_data[filtered_data['Type'] == filters['type']]
    if filters['subtype']:
        filtered_data = filtered_data[filtered_data['Sub Type'] == filters['subtype']]
    filtered_data = filtered_data[~filtered_data.index.isin(used_questions)]
    return jsonify({'remaining': len(filtered_data), 'questions': filtered_data[['Question', 'Answer']].to_dict(orient='records')})

@app.route('/score', methods=['POST'])
def update_score():
    global scores, used_questions
    data = request.json
    team = data['team']
    round_name = data['round']
    index = data['index']
    change = data['points']
    if team not in scores:
        scores[team] = {}
    scores[team][round_name] = scores[team].get(round_name, 0) + change
    used_questions.add(index)
    return jsonify({'success': True})

@app.route('/scores')
def get_scores():
    all_rounds = sorted({r for team_scores in scores.values() for r in team_scores})
    result = []
    for team, team_scores in scores.items():
        entry = {'team': team}
        total = 0
        for r in all_rounds:
            entry[r] = team_scores.get(r, 0)
            total += entry[r]
        entry['total'] = total
        result.append(entry)
    top_3 = sorted(result, key=lambda x: x['total'], reverse=True)[:3]
    return jsonify({'scores': result, 'top_3': top_3})

@app.route('/save_scores', methods=['POST'])
def save_scores():
    with open(SCORE_FILE, 'w') as f:
        json.dump(scores, f)
    return jsonify({'success': True})

@app.route('/load_scores')
def load_scores():
    global scores
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, 'r') as f:
            scores = json.load(f)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/export_scores')
def export_scores():
    all_rounds = sorted({r for team_scores in scores.values() for r in team_scores})
    rows = []
    for team, team_scores in scores.items():
        row = {'Team': team}
        total = 0
        for r in all_rounds:
            score = team_scores.get(r, 0)
            row[r] = score
            total += score
        row['Total'] = total
        rows.append(row)
    df = pd.DataFrame(rows)
    path = os.path.join(UPLOAD_FOLDER, 'Exported_Scores.xlsx')
    df.to_excel(path, index=False)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
