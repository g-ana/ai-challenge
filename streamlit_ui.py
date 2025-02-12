import streamlit as st
from fuzzywuzzy import fuzz
import datetime
import pandas as pd
from streamlit_option_menu import option_menu

# Initialize session state
if 'admin_skills' not in st.session_state:
    st.session_state.admin_skills = ["Python Programming", "Data Analysis", "Machine Learning", "Web Development"]

if 'request_history' not in st.session_state:
    st.session_state.request_history = []

# Configure page
st.set_page_config(page_title="Skill Matcher", layout="wide")

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

# Comparison functions
def exact_match(a, b):
    return 100 if a == b else 0

def partial_ratio(a, b):
    return fuzz.partial_ratio(a, b)

def token_sort_ratio(a, b):
    return fuzz.token_sort_ratio(a, b)

def levenshtein_similarity(a, b):
    return fuzz.ratio(a, b)

# Initialize comparator
comparator = SkillComparator(st.session_state.admin_skills)
comparator.add_method('exact_match', exact_match, case_sensitive=False, threshold=100)
comparator.add_method('levenshtein', levenshtein_similarity, case_sensitive=False, threshold=85)
comparator.add_method('token_sort', token_sort_ratio, case_sensitive=False, threshold=80)
comparator.add_method('partial_ratio', partial_ratio, case_sensitive=False, threshold=80)

# Sidebar navigation
#st.sidebar.title("Navigation")
#page = st.sidebar.radio("Go to", ["Skill Matching", "Skill Management", "Request History"])

with st.sidebar:
    page=option_menu(
        menu_title = "Menu",
        menu_icon = "herat-eyes-fill",
        options = ["Skill Matching", "Skill Management", "Request History"],
        icons = ["envelope-heart-fill", "house-heart-fill", "calendar2-heart-fill"],
        default_index = 0
    )

# Current skills display
#st.sidebar.markdown("---")
#st.sidebar.subheader("Current Skills")
#st.sidebar.write(st.session_state.admin_skills)

# Skill Matching Page
if page == "Skill Matching":
    st.title("Skill Matching")
    
    with st.form("compare_form"):
        user_skill = st.text_input("Enter skill to compare", key="skill_input")
        submitted = st.form_submit_button("Compare")
        
        if submitted and user_skill:
            results = comparator.compare(user_skill)
            record = {
                'timestamp': datetime.datetime.now(),
                'user_skill': user_skill,
                'results': results
            }
            st.session_state.request_history.append(record)
            
            # Create results table
            data = []
            for result in results:
                row = {'Admin Skill': result['admin_skill']}
                for method, scores in result['scores'].items():
                    row[method] = scores['score']
                data.append(row)
            
            df = pd.DataFrame(data).set_index('Admin Skill')
            st.subheader("Matching Results")
            st.dataframe(df.style.highlight_max(axis=0, color='#90EE90'))

# Skill Management Page
elif page == "Skill Management":
    st.title("Skill Management")
    
    # Add new skill section
    with st.container(border=True):
        cols = st.columns([4, 1])
        with cols[0]:
            new_skill = st.text_input("Add new skill", key="new_skill_input")
        with cols[1]:
            st.write("")  # Vertical alignment
            st.write("")
            if st.button("Add", use_container_width=True):
                if new_skill and new_skill not in st.session_state.admin_skills:
                    st.session_state.admin_skills.append(new_skill)
                    st.rerun()
                elif new_skill in st.session_state.admin_skills:
                    st.error("Skill already exists!")
    
    # Current skills table
    st.subheader("Current Skills")
    if not st.session_state.admin_skills:
        st.info("No skills in the list yet")
    else:
        for idx, skill in enumerate(st.session_state.admin_skills):
            cols = st.columns([6, 2, 2])
            with cols[0]:
                if st.session_state.get("editing_index") == idx:
                    edited_skill = st.text_input(
                        "Edit skill", 
                        value=skill,
                        key=f"edit_{idx}"
                    )
                    if st.session_state.admin_skills[idx] != edited_skill:
                        st.session_state.admin_skills[idx] = edited_skill
                        del st.session_state["editing_index"]
                        st.rerun()
                else:
                    st.markdown(f"• {skill}")
            
            with cols[1]:
                if st.session_state.get("editing_index") == idx:
                    if st.button("Save", key=f"save_{idx}", use_container_width=True):
                        st.session_state.admin_skills[idx] = edited_skill
                        del st.session_state["editing_index"]
                        st.rerun()
                else:
                    if st.button("Edit", key=f"edit_btn_{idx}", use_container_width=True):
                        st.session_state["editing_index"] = idx
                        st.rerun()
            
            with cols[2]:
                if st.button("❌", key=f"del_{idx}", help="Delete skill", 
                           use_container_width=True):
                    del st.session_state.admin_skills[idx]
                    if st.session_state.get("editing_index") == idx:
                        del st.session_state["editing_index"]
                    st.rerun()

# Request History Page
elif page == "Request History":
    st.title("Request History")
    
    if st.session_state.request_history:
        selected = st.selectbox("Select request", 
                             options=range(len(st.session_state.request_history)),
                             format_func=lambda x: f"{st.session_state.request_history[x]['user_skill']} - {st.session_state.request_history[x]['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        
        record = st.session_state.request_history[selected]
        st.subheader(f"Request Details: {record['user_skill']}")
        st.write(f"**Timestamp:** {record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create results table
        data = []
        for result in record['results']:
            row = {'Admin Skill': result['admin_skill']}
            for method, scores in result['scores'].items():
                row[method] = scores['score']
            data.append(row)
        
        df = pd.DataFrame(data).set_index('Admin Skill')
        st.dataframe(df.style.highlight_max(axis=0, color='#90EE90'))
    else:
        st.info("No comparison requests recorded yet")
        