from fuzzywuzzy import fuzz
from flask import Flask, request, jsonify
import datetime

class SkillComparator:
    def __init__(self, admin_skills):
        self.admin_skills = admin_skills
        self.methods = []

    def add_method(self, name, func, case_sensitive=False, threshold=0):
        self.methods.append({
            'name': name,
            'func': func,
            'case_sensitive': case_sensitive,
            'threshold': threshold
        })

    def compare(self, user_skill):
        results = []
        for admin_skill in self.admin_skills:
            scores = {}
            for method in self.methods:
                a = admin_skill if method['case_sensitive'] else admin_skill.lower()
                u = user_skill if method['case_sensitive'] else user_skill.lower()
                score = method['func'](a, u)
                scores[method['name']] = {
                    'score': score,
                    'is_match': score >= method['threshold']
                }
            results.append({
                'admin_skill': admin_skill,
                'scores': scores
            })
        results.sort(key=lambda x: max(s['score'] for s in x['scores'].values()), reverse=True)
        return results

# Define comparison functions
def exact_match(a, b):
    return 100 if a == b else 0

def partial_ratio(a, b):
    return fuzz.partial_ratio(a, b)

def token_sort_ratio(a, b):
    return fuzz.token_sort_ratio(a, b)

def levenshtein_similarity(a, b):
    return fuzz.ratio(a, b)

# Flask application setup
app = Flask(__name__)

# Initialize data stores
admin_skills = ["Python Programming", "Data Analysis", "Machine Learning", "Web Development"]
request_history = []

# Initialize comparator
comparator = SkillComparator(admin_skills)
comparator.add_method('exact_match', exact_match, case_sensitive=False, threshold=100)
comparator.add_method('levenshtein', levenshtein_similarity, case_sensitive=False, threshold=85)
comparator.add_method('token_sort', token_sort_ratio, case_sensitive=False, threshold=80)
comparator.add_method('partial_ratio', partial_ratio, case_sensitive=False, threshold=80)

@app.route('/compare', methods=['POST'])
def compare_skill():
    data = request.get_json()
    user_skill = data.get('skill', '').strip()
    
    if not user_skill:
        return jsonify({'error': 'Skill parameter is required'}), 400
    
    try:
        results = comparator.compare(user_skill)
        # Store request history
        request_history.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'user_skill': user_skill,
            'results': results
        })
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/manage', methods=['POST'])
def manage_skills():
    data = request.get_json()
    action = data.get('action')

    if action == 'add':
        skill = data.get('skill')
        if not skill:
            return jsonify({'error': 'Skill parameter is required for add action'}), 400
        if skill in admin_skills:
            return jsonify({'error': f'Skill {skill} already exists'}), 400
        admin_skills.append(skill)
        return jsonify({'message': f'Skill {skill} added successfully'}), 200

    elif action == 'update':
        old_skill = data.get('old_skill')
        new_skill = data.get('new_skill')
        if not old_skill or not new_skill:
            return jsonify({'error': 'Both old_skill and new_skill are required for update'}), 400
        try:
            index = admin_skills.index(old_skill)
            admin_skills[index] = new_skill
            return jsonify({'message': f'Skill updated from {old_skill} to {new_skill}'}), 200
        except ValueError:
            return jsonify({'error': f'Skill {old_skill} not found'}), 404

    elif action == 'delete':
        skill = data.get('skill')
        if not skill:
            return jsonify({'error': 'Skill parameter is required for delete action'}), 400
        try:
            admin_skills.remove(skill)
            return jsonify({'message': f'Skill {skill} deleted successfully'}), 200
        except ValueError:
            return jsonify({'error': f'Skill {skill} not found'}), 404

    elif action == 'list':
        return jsonify({'skills':admin_skills})
    
    else:
        return jsonify({'error': 'Invalid action. Valid actions: add, update, delete'}), 400

@app.route('/list', methods=['GET'])
def list_requests():
    return jsonify({'requests': request_history})

if __name__ == '__main__':
    app.run(debug=True)
    
###
    
'''
curl -X POST http://localhost:5000/manage \
-H "Content-Type: application/json" \
-d '{"action": "add", "skill": "Cloud Computing"}'

curl -X POST http://localhost:5000/compare \
-H "Content-Type: application/json" \
-d '{"skill": "pyton programming"}'

curl http://localhost:5000/list


'''