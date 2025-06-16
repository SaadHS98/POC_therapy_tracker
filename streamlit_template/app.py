import streamlit as st
import json
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import uuid
import copy

# Set page config
st.set_page_config(
    page_title="Therapy Progress Tracking",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #4b6584;
    margin-bottom: 1rem;
    text-align: center;
}
.sub-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #4b6584;
    margin-bottom: 0.5rem;
}
.info-box {
    background-color: #f7f9fb;
    border-radius: 5px;
    padding: 10px;
    margin: 10px 0;
}
.progress-improved {
    color: #20bf6b;
    font-weight: bold;
}
.progress-worsened {
    color: #eb3b5a;
    font-weight: bold;
}
.progress-unchanged {
    color: #778ca3;
    font-weight: bold;
}
.symptom-card {
    background-color: #f7f9fb;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
    border-left: 4px solid #4b6584;
}
.assessment-card {
    background-color: #f7f9fb;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
    border-left: 4px solid #45aaf2;
}
</style>
""", unsafe_allow_html=True)


# Initialize session state variables if they don't exist
if 'uploaded_sessions' not in st.session_state:
    st.session_state.uploaded_sessions = {}
if 'selected_client' not in st.session_state:
    st.session_state.selected_client = None
if 'session_comparisons' not in st.session_state:
    st.session_state.session_comparisons = {}
if 'client_list' not in st.session_state:
    st.session_state.client_list = []

# GAD-7 questions and mapping
gad7_questions = {
    1: "Feeling nervous, anxious, or on edge",
    2: "Not being able to stop or control worrying",
    3: "Worrying too much about different things",
    4: "Trouble relaxing",
    5: "Being so restless that it's hard to sit still",
    6: "Becoming easily annoyed or irritable",
    7: "Feeling afraid, as if something awful might happen"
}

# PHQ-9 questions and mapping
phq9_questions = {
    1: "Little interest or pleasure in doing things",
    2: "Feeling down, depressed, or hopeless",
    3: "Trouble falling/staying asleep, sleeping too much",
    4: "Feeling tired or having little energy",
    5: "Poor appetite or overeating",
    6: "Feeling bad about yourself or that you're a failure or have let yourself or your family down",
    7: "Trouble concentrating on things such as reading the newspaper or watching television",
    8: "Moving or speaking so slowly that other people could have noticed. Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
    9: "Thoughts that you would be better off dead, or thoughts of hurting yourself in some way"
}


# Helper functions
def extract_client_id(json_data):
    """Extract client identifier from session notes"""
    # In a real application, you would have a proper client ID field
    # For demo purposes, we'll extract from the file name or content
    if isinstance(json_data, dict):
        quotes = []
        # Look for quotes in the chief complaint
        if 'Presentation' in json_data and 'Quote (Chief Complaint)' in json_data['Presentation']:
            return f"Client-{hash(json_data['Presentation']['Quote (Chief Complaint)']) % 1000}"
        return f"Client-{hash(str(json_data)) % 1000}"
    return f"Client-{hash(str(json_data)) % 1000}"

def extract_symptoms(json_data):
    """Extract symptoms and their attributes from session notes"""
    symptoms = []
    if isinstance(json_data, dict) and 'Psychological Factors' in json_data:
        psych_factors = json_data['Psychological Factors']
        if 'Symptoms' in psych_factors and isinstance(psych_factors['Symptoms'], dict):
            for symptom_key, symptom_data in psych_factors['Symptoms'].items():
                if isinstance(symptom_data, dict):
                    symptom = {
                        'description': symptom_data.get('Description', 'Unknown'),
                        'intensity': symptom_data.get('Intensity', 'Unknown'),
                        'frequency': symptom_data.get('Frequency', 'Unknown'),
                        'duration': symptom_data.get('Duration', 'Unknown'),
                        'quote': symptom_data.get('Quote (Symptom)', '')
                    }
                    symptoms.append(symptom)
    
    # Also check Mental Status Exam for additional symptoms
    if isinstance(json_data, dict) and 'Mental Status Exam' in json_data:
        mse = json_data['Mental Status Exam']
        if 'Mood and Affect' in mse and mse['Mood and Affect']:
            mood_match = re.search(r'(anxious|depressed|stressed)', mse['Mood and Affect'], re.IGNORECASE)
            if mood_match:
                symptoms.append({
                    'description': f"Mood: {mood_match.group(0)}",
                    'intensity': 'Observed',
                    'frequency': 'During session',
                    'duration': 'Unknown',
                    'quote': mse['Mood and Affect']
                })
    
    # Check Risk Assessment for additional concerns
    if isinstance(json_data, dict) and 'Risk Assessment' in json_data:
        risk = json_data['Risk Assessment']
        if 'Hopelessness' in risk and risk['Hopelessness'] and risk['Hopelessness'] != 'NA':
            symptoms.append({
                'description': 'Hopelessness',
                'intensity': 'Observed',
                'frequency': 'Unknown',
                'duration': 'Unknown',
                'quote': risk.get('Quote (Risk)', risk['Hopelessness'])
            })
    
    return symptoms


def map_to_gad7(symptoms):
    """Map extracted symptoms to GAD-7 assessment"""
    gad7_scores = {q: 0 for q in range(1, 8)}
    
    for symptom in symptoms:
        description = symptom['description'].lower() if isinstance(symptom['description'], str) else ''
        intensity = symptom['intensity'].lower() if isinstance(symptom['intensity'], str) else ''
        quote = symptom['quote'].lower() if isinstance(symptom['quote'], str) else ''
        
        # Question 1: Feeling nervous, anxious, or on edge
        if any(keyword in description or keyword in quote for keyword in ['nervous', 'anxious', 'anxiety', 'on edge', 'stress']):
            if 'high' in intensity or 'severe' in intensity:
                gad7_scores[1] = 3
            elif 'moderate' in intensity:
                gad7_scores[1] = 2
            elif 'mild' in intensity or 'low' in intensity:
                gad7_scores[1] = 1
            else:
                gad7_scores[1] = 1  # Default if intensity not specified
        
        # Question 2: Not being able to stop or control worrying
        if any(keyword in description or keyword in quote for keyword in ['worrying', 'worry', 'can\'t stop', 'uncontrollable']):
            if 'high' in intensity or 'severe' in intensity:
                gad7_scores[2] = 3
            elif 'moderate' in intensity:
                gad7_scores[2] = 2
            elif 'mild' in intensity or 'low' in intensity:
                gad7_scores[2] = 1
            else:
                gad7_scores[2] = 1
        
        # Question 3: Worrying too much about different things
        if any(keyword in description or keyword in quote for keyword in ['worry too much', 'worrying about', 'different things']):
            if 'high' in intensity or 'severe' in intensity:
                gad7_scores[3] = 3
            elif 'moderate' in intensity:
                gad7_scores[3] = 2
            elif 'mild' in intensity or 'low' in intensity:
                gad7_scores[3] = 1
            else:
                gad7_scores[3] = 1
        
        # Question 4: Trouble relaxing
        if any(keyword in description or keyword in quote for keyword in ['relax', 'relaxing', 'tense', 'tension']):
            if 'high' in intensity or 'severe' in intensity:
                gad7_scores[4] = 3
            elif 'moderate' in intensity:
                gad7_scores[4] = 2
            elif 'mild' in intensity or 'low' in intensity:
                gad7_scores[4] = 1
            else:
                gad7_scores[4] = 1
        
        # Question 5: Being so restless that it's hard to sit still
        if any(keyword in description or keyword in quote for keyword in ['restless', 'sit still', 'agitated', 'fidgety']):
            if 'high' in intensity or 'severe' in intensity:
                gad7_scores[5] = 3
            elif 'moderate' in intensity:
                gad7_scores[5] = 2
            elif 'mild' in intensity or 'low' in intensity:
                gad7_scores[5] = 1
            else:
                gad7_scores[5] = 1
        
        # Question 6: Becoming easily annoyed or irritable
        if any(keyword in description or keyword in quote for keyword in ['annoyed', 'irritable', 'irritability', 'frustrated']):
            if 'high' in intensity or 'severe' in intensity:
                gad7_scores[6] = 3
            elif 'moderate' in intensity:
                gad7_scores[6] = 2
            elif 'mild' in intensity or 'low' in intensity:
                gad7_scores[6] = 1
            else:
                gad7_scores[6] = 1
        
        # Question 7: Feeling afraid, as if something awful might happen
        if any(keyword in description or keyword in quote for keyword in ['afraid', 'fear', 'terrible', 'awful', 'catastrophic']):
            if 'high' in intensity or 'severe' in intensity:
                gad7_scores[7] = 3
            elif 'moderate' in intensity:
                gad7_scores[7] = 2
            elif 'mild' in intensity or 'low' in intensity:
                gad7_scores[7] = 1
            else:
                gad7_scores[7] = 1
    
    # Calculate total score
    total_score = sum(gad7_scores.values())
    
    # Determine severity category
    if total_score <= 4:
        severity = "Minimal anxiety"
    elif total_score <= 9:
        severity = "Mild anxiety"
    elif total_score <= 14:
        severity = "Moderate anxiety"
    else:
        severity = "Severe anxiety"
    
    return {
        'scores': gad7_scores,
        'total_score': total_score,
        'severity': severity
    }


def map_to_phq9(symptoms, json_data):
    """Map extracted symptoms to PHQ-9 assessment"""
    phq9_scores = {q: 0 for q in range(1, 10)}
    
    # Process symptoms
    for symptom in symptoms:
        description = symptom['description'].lower() if isinstance(symptom['description'], str) else ''
        intensity = symptom['intensity'].lower() if isinstance(symptom['intensity'], str) else ''
        quote = symptom['quote'].lower() if isinstance(symptom['quote'], str) else ''
        
        # Question 1: Little interest or pleasure in doing things
        if any(keyword in description or keyword in quote for keyword in ['anhedonia', 'no interest', 'little interest', 'no pleasure', 'lost interest']):
            if 'high' in intensity or 'severe' in intensity:
                phq9_scores[1] = 3
            elif 'moderate' in intensity:
                phq9_scores[1] = 2
            elif 'mild' in intensity or 'low' in intensity:
                phq9_scores[1] = 1
            else:
                phq9_scores[1] = 1
        
        # Question 2: Feeling down, depressed, or hopeless
        if any(keyword in description or keyword in quote for keyword in ['depressed', 'depression', 'feeling down', 'hopeless', 'despair']):
            if 'high' in intensity or 'severe' in intensity:
                phq9_scores[2] = 3
            elif 'moderate' in intensity:
                phq9_scores[2] = 2
            elif 'mild' in intensity or 'low' in intensity:
                phq9_scores[2] = 1
            else:
                phq9_scores[2] = 1
    
    # Check biological factors for sleep issues (Question 3)
    if isinstance(json_data, dict) and 'Biological Factors' in json_data:
        bio_factors = json_data['Biological Factors']
        if 'Sleep' in bio_factors and bio_factors['Sleep'] and bio_factors['Sleep'] != 'NA':
            sleep_issues = re.search(r'(difficulty|problem|issue|trouble|insomnia|too much|oversleep)', bio_factors['Sleep'], re.IGNORECASE)
            if sleep_issues:
                phq9_scores[3] = 2  # Default to moderate if sleep issues mentioned
    
    # Check for energy levels (Question 4)
    for symptom in symptoms:
        if any(keyword in symptom.get('description', '').lower() or keyword in symptom.get('quote', '').lower() 
              for keyword in ['tired', 'fatigue', 'no energy', 'little energy', 'exhausted']):
            phq9_scores[4] = 2
    
    # Check for appetite issues (Question 5)
    if isinstance(json_data, dict) and 'Biological Factors' in json_data:
        bio_factors = json_data['Biological Factors']
        if 'Nutrition' in bio_factors and bio_factors['Nutrition'] and bio_factors['Nutrition'] != 'NA':
            appetite_issues = re.search(r'(poor appetite|overeating|not eating|eating too much)', bio_factors['Nutrition'], re.IGNORECASE)
            if appetite_issues:
                phq9_scores[5] = 2
    
    # Question 6: Feeling bad about yourself
    for symptom in symptoms:
        if any(keyword in symptom.get('description', '').lower() or keyword in symptom.get('quote', '').lower() 
              for keyword in ['worthless', 'guilt', 'failure', 'blame', 'let down', 'disappointed in self']):
            if 'high' in symptom.get('intensity', '').lower() or 'severe' in symptom.get('intensity', '').lower():
                phq9_scores[6] = 3
            elif 'moderate' in symptom.get('intensity', '').lower():
                phq9_scores[6] = 2
            else:
                phq9_scores[6] = 1
    
    # Question 7: Trouble concentrating
    for symptom in symptoms:
        if any(keyword in symptom.get('description', '').lower() or keyword in symptom.get('quote', '').lower() 
              for keyword in ['concentrate', 'focus', 'attention', 'distracted']):
            if 'high' in symptom.get('intensity', '').lower() or 'severe' in symptom.get('intensity', '').lower():
                phq9_scores[7] = 3
            elif 'moderate' in symptom.get('intensity', '').lower():
                phq9_scores[7] = 2
            else:
                phq9_scores[7] = 1
    
    # Question 8: Moving or speaking slowly
    for symptom in symptoms:
        if any(keyword in symptom.get('description', '').lower() or keyword in symptom.get('quote', '').lower() 
              for keyword in ['slow', 'sluggish', 'restless', 'fidgety', 'agitated', 'psychomotor']):
            if 'high' in symptom.get('intensity', '').lower() or 'severe' in symptom.get('intensity', '').lower():
                phq9_scores[8] = 3
            elif 'moderate' in symptom.get('intensity', '').lower():
                phq9_scores[8] = 2
            else:
                phq9_scores[8] = 1
    
    # Question 9: Thoughts of self-harm
    if isinstance(json_data, dict) and 'Risk Assessment' in json_data:
        risk = json_data['Risk Assessment']
        if 'Suicidal Thoughts or Attempts' in risk and risk['Suicidal Thoughts or Attempts'] != 'NA' and risk['Suicidal Thoughts or Attempts'] != 'No Indication of Risk':
            phq9_scores[9] = 3  # High risk if any suicidal thoughts are mentioned
        elif 'Self Harm' in risk and risk['Self Harm'] != 'NA' and risk['Self Harm'] != 'No Indication of Risk':
            phq9_scores[9] = 3  # High risk if any self-harm is mentioned
        elif 'Hopelessness' in risk and risk['Hopelessness'] != 'NA' and risk['Hopelessness'] != 'No hopelessness expressed or observed.':
            # Check for passive suicidal ideation in hopelessness
            passive_si = re.search(r'(better off dead|not worth living|giving up|end it all)', risk['Hopelessness'], re.IGNORECASE)
            if passive_si:
                phq9_scores[9] = 2
    
    # Calculate total score
    total_score = sum(phq9_scores.values())
    
    # Determine severity category
    if total_score <= 4:
        severity = "None-minimal depression"
    elif total_score <= 9:
        severity = "Mild depression"
    elif total_score <= 14:
        severity = "Moderate depression"
    elif total_score <= 19:
        severity = "Moderately severe depression"
    else:
        severity = "Severe depression"
    
    return {
        'scores': phq9_scores,
        'total_score': total_score,
        'severity': severity
    }


def calculate_symptom_change(symptom1, symptom2):
    """Calculate the change in a symptom between sessions"""
    # Map intensity levels to numeric values
    intensity_map = {
        'none': 0,
        'minimal': 1,
        'mild': 2,
        'low': 2,
        'moderate': 3,
        'high': 4,
        'severe': 5
    }
    
    # Calculate intensity change
    intensity1 = symptom1['intensity'].lower() if isinstance(symptom1['intensity'], str) else 'moderate'
    intensity2 = symptom2['intensity'].lower() if isinstance(symptom2['intensity'], str) else 'moderate'
    
    intensity1_val = next((v for k, v in intensity_map.items() if k in intensity1), 3)  # Default to moderate if not found
    intensity2_val = next((v for k, v in intensity_map.items() if k in intensity2), 3)
    
    intensity_change = intensity1_val - intensity2_val
    
    # Calculate frequency change
    frequency_change = 0
    if 'daily' in symptom1.get('frequency', '').lower() and 'occasional' in symptom2.get('frequency', '').lower():
        frequency_change = 1
    elif 'multiple times a day' in symptom1.get('frequency', '').lower() and 'daily' in symptom2.get('frequency', '').lower():
        frequency_change = 1
    elif 'occasional' in symptom1.get('frequency', '').lower() and 'rare' in symptom2.get('frequency', '').lower():
        frequency_change = 1
    elif 'occasional' in symptom1.get('frequency', '').lower() and 'daily' in symptom2.get('frequency', '').lower():
        frequency_change = -1
    elif 'daily' in symptom1.get('frequency', '').lower() and 'multiple times a day' in symptom2.get('frequency', '').lower():
        frequency_change = -1
    
    # Calculate overall change score (-1 to +1 scale)
    change_score = (intensity_change + frequency_change) / 2
    
    # Determine change direction and description
    if intensity_change > 0 or frequency_change > 0:
        direction = 'improved'
        description = f"Improved from {intensity1} to {intensity2}"
    elif intensity_change < 0 or frequency_change < 0:
        direction = 'worsened'
        description = f"Worsened from {intensity1} to {intensity2}"
    else:
        direction = 'unchanged'
        description = f"Unchanged at {intensity1}"
    
    return {
        'intensity_change': intensity_change,
        'frequency_change': frequency_change,
        'direction': direction,
        'description': description,
        'score': change_score
    }

def calculate_progress(first_session_data, second_session_data):
    """Calculate progress between two sessions"""
    first_symptoms = extract_symptoms(first_session_data)
    second_symptoms = extract_symptoms(second_session_data)
    
    # Match symptoms between sessions
    matched_symptoms = []
    new_symptoms = []
    resolved_symptoms = copy.deepcopy(first_symptoms)
    
    for symptom2 in second_symptoms:
        matched = False
        for i, symptom1 in enumerate(first_symptoms):
            if symptom1['description'].lower() == symptom2['description'].lower():
                matched = True
                matched_symptoms.append({
                    'description': symptom1['description'],
                    'first_intensity': symptom1['intensity'],
                    'second_intensity': symptom2['intensity'],
                    'first_frequency': symptom1['frequency'],
                    'second_frequency': symptom2['frequency'],
                    'change': calculate_symptom_change(symptom1, symptom2)
                })
                # Remove from resolved symptoms if it's still present
                for j, resolved in enumerate(resolved_symptoms):
                    if resolved['description'].lower() == symptom1['description'].lower():
                        resolved_symptoms.pop(j)
                        break
                break
        
        if not matched:
            new_symptoms.append(symptom2)
    
    # Calculate overall progress score
    total_changes = sum(s['change']['score'] for s in matched_symptoms)
    num_symptoms = len(matched_symptoms) if matched_symptoms else 1  # Avoid division by zero
    overall_progress_score = total_changes / num_symptoms
    
    # Map symptoms to standardized assessments
    first_gad7 = map_to_gad7(first_symptoms)
    second_gad7 = map_to_gad7(second_symptoms)
    first_phq9 = map_to_phq9(first_symptoms, first_session_data)
    second_phq9 = map_to_phq9(second_symptoms, second_session_data)
    
    return {
        'matched_symptoms': matched_symptoms,
        'new_symptoms': new_symptoms,
        'resolved_symptoms': resolved_symptoms,
        'overall_progress_score': overall_progress_score,
        'gad7_change': second_gad7['total_score'] - first_gad7['total_score'],
        'phq9_change': second_phq9['total_score'] - first_phq9['total_score'],
        'first_gad7': first_gad7,
        'second_gad7': second_gad7,
        'first_phq9': first_phq9,
        'second_phq9': second_phq9
    }


def generate_insights(progress_data):
    """Generate clinical insights based on progress data"""
    insights = []
    
    # Overall progress insight
    if progress_data['overall_progress_score'] > 0.5:
        insights.append("Client shows significant overall improvement in symptoms.")
    elif progress_data['overall_progress_score'] > 0:
        insights.append("Client shows modest improvement in some symptoms, but continued attention is needed.")
    elif progress_data['overall_progress_score'] < -0.5:
        insights.append("Client shows notable worsening of symptoms, requiring prompt intervention.")
    elif progress_data['overall_progress_score'] < 0:
        insights.append("Client shows slight worsening in some symptoms, suggesting a review of the treatment approach.")
    else:
        insights.append("Client's symptoms remain largely unchanged, suggesting a potential plateau in treatment response.")
    
    # GAD-7 insights
    if progress_data['gad7_change'] <= -5:
        insights.append(f"Significant reduction in anxiety symptoms (GAD-7 score decreased by {-progress_data['gad7_change']} points).")
    elif progress_data['gad7_change'] <= -3:
        insights.append(f"Moderate reduction in anxiety symptoms (GAD-7 score decreased by {-progress_data['gad7_change']} points).")
    elif progress_data['gad7_change'] >= 5:
        insights.append(f"Significant increase in anxiety symptoms (GAD-7 score increased by {progress_data['gad7_change']} points).")
    elif progress_data['gad7_change'] >= 3:
        insights.append(f"Moderate increase in anxiety symptoms (GAD-7 score increased by {progress_data['gad7_change']} points).")
    
    # PHQ-9 insights
    if progress_data['phq9_change'] <= -5:
        insights.append(f"Significant reduction in depressive symptoms (PHQ-9 score decreased by {-progress_data['phq9_change']} points).")
    elif progress_data['phq9_change'] <= -3:
        insights.append(f"Moderate reduction in depressive symptoms (PHQ-9 score decreased by {-progress_data['phq9_change']} points).")
    elif progress_data['phq9_change'] >= 5:
        insights.append(f"Significant increase in depressive symptoms (PHQ-9 score increased by {progress_data['phq9_change']} points).")
    elif progress_data['phq9_change'] >= 3:
        insights.append(f"Moderate increase in depressive symptoms (PHQ-9 score increased by {progress_data['phq9_change']} points).")
    
    # New symptoms insight
    if progress_data['new_symptoms']:
        symptom_list = ', '.join([s['description'] for s in progress_data['new_symptoms']])
        insights.append(f"New symptoms emerged: {symptom_list}. These may require specific attention.")
    
    # Resolved symptoms insight
    if progress_data['resolved_symptoms']:
        symptom_list = ', '.join([s['description'] for s in progress_data['resolved_symptoms']])
        insights.append(f"Resolved symptoms: {symptom_list}. This represents positive progress.")
    
    # Specific symptom insights
    improved_symptoms = [s for s in progress_data['matched_symptoms'] if s['change']['direction'] == 'improved']
    worsened_symptoms = [s for s in progress_data['matched_symptoms'] if s['change']['direction'] == 'worsened']
    
    if improved_symptoms:
        symptom_list = ', '.join([s['description'] for s in improved_symptoms])
        insights.append(f"Improved symptoms: {symptom_list}.")
    
    if worsened_symptoms:
        symptom_list = ', '.join([s['description'] for s in worsened_symptoms])
        insights.append(f"Worsened symptoms: {symptom_list}. Consider adjusting treatment focus.")
    
    return insights

# Main application UI
st.markdown('<h1 class="main-header">Therapy Progress Tracking</h1>', unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", ["Upload Sessions", "Client Dashboard", "Session Comparison", "Help"])

# Upload Sessions Page
if page == "Upload Sessions":
    st.markdown('<h2 class="sub-header">Upload Session Notes</h2>', unsafe_allow_html=True)
    st.write("Upload JSON session notes to track client progress.")
    
    uploaded_file = st.file_uploader("Choose a JSON session file", type="txt")
    if uploaded_file is not None:
        try:
            # Read the content
            content = uploaded_file.read().decode()
            # Clean the content - remove line numbers
            clean_content = re.sub(r'^\d+\|', '', content, flags=re.MULTILINE)
            # Parse the JSON
            json_data = json.loads(clean_content)
            
            # Extract client ID and session info
            client_id = extract_client_id(json_data)
            session_id = str(uuid.uuid4())[:8]  # Generate a short unique ID for the session
            
            # Add client to list if not already there
            if client_id not in st.session_state.client_list:
                st.session_state.client_list.append(client_id)
            
            # Store the uploaded session
            if client_id not in st.session_state.uploaded_sessions:
                st.session_state.uploaded_sessions[client_id] = {}
            
            # Extract the session date or use current date
            session_date = datetime.now().strftime("%Y-%m-%d")
            if isinstance(json_data, dict) and 'Session Date' in json_data:
                session_date = json_data['Session Date']
            
            st.session_state.uploaded_sessions[client_id][session_id] = {
                'data': json_data,
                'date': session_date,
                'file_name': uploaded_file.name
            }
            
            st.success(f"Successfully uploaded session for {client_id} on {session_date}.")
            
            # Update selected client to the one just uploaded
            st.session_state.selected_client = client_id
            
        except json.JSONDecodeError:
            st.error("The uploaded file is not valid JSON. Please check the format.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    
    # Display current sessions
    if st.session_state.uploaded_sessions:
        st.markdown('<h3 class="sub-header">Uploaded Sessions</h3>', unsafe_allow_html=True)
        for client_id, sessions in st.session_state.uploaded_sessions.items():
            with st.expander(f"Client: {client_id}"):
                for session_id, session_info in sessions.items():
                    st.write(f"Session {session_id}: {session_info['date']} - {session_info['file_name']}")

# Client Dashboard Page
elif page == "Client Dashboard":
    st.markdown('<h2 class="sub-header">Client Dashboard</h2>', unsafe_allow_html=True)
    
    if not st.session_state.uploaded_sessions:
        st.info("No sessions have been uploaded yet. Please upload session notes first.")
    else:
        # Client selector
        client_options = list(st.session_state.uploaded_sessions.keys())
        selected_client = st.selectbox(
            "Select Client", 
            options=client_options,
            index=client_options.index(st.session_state.selected_client) if st.session_state.selected_client in client_options else 0
        )
        st.session_state.selected_client = selected_client
        
        if selected_client:
            client_sessions = st.session_state.uploaded_sessions[selected_client]
            
            # Display client information
            st.markdown(f"<div class='info-box'><h3>Client: {selected_client}</h3>", unsafe_allow_html=True)
            st.write(f"Number of sessions: {len(client_sessions)}")
            
            # Show most recent session assessment
            if client_sessions:
                # Sort sessions by date
                sorted_sessions = sorted(
                    client_sessions.items(),
                    key=lambda x: datetime.strptime(x[1]['date'], "%Y-%m-%d") if isinstance(x[1]['date'], str) else datetime.now(),
                    reverse=True
                )
                
                latest_session_id, latest_session = sorted_sessions[0]
                latest_data = latest_session['data']
                
                st.markdown(f"<h3 class='sub-header'>Latest Assessment ({latest_session['date']})</h3>", unsafe_allow_html=True)
                
                # Extract symptoms from latest session
                symptoms = extract_symptoms(latest_data)
                
                # Display symptoms
                if symptoms:
                    st.markdown("<h4>Current Symptoms</h4>", unsafe_allow_html=True)
                    for symptom in symptoms:
                        with st.container():
                            st.markdown(f"<div class='symptom-card'>", unsafe_allow_html=True)
                            st.markdown(f"<strong>{symptom['description']}</strong>", unsafe_allow_html=True)
                            st.write(f"Intensity: {symptom['intensity']}")
                            st.write(f"Frequency: {symptom['frequency']}")
                            if symptom['quote']:
                                st.markdown(f"<em>\"{symptom['quote']}\"</em>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                
                # Map to standardized assessments
                gad7_results = map_to_gad7(symptoms)
                phq9_results = map_to_phq9(symptoms, latest_data)
                
                # Display GAD-7 scores
                with st.container():
                    st.markdown("<div class='assessment-card'>", unsafe_allow_html=True)
                    st.markdown("<h4>GAD-7 Assessment (Anxiety)</h4>", unsafe_allow_html=True)
                    st.write(f"Total Score: {gad7_results['total_score']} - {gad7_results['severity']}")
                    
                    # Create a bar chart for GAD-7 scores
                    gad7_df = pd.DataFrame({
                        'Question': [gad7_questions[q] for q in gad7_results['scores'].keys()],
                        'Score': list(gad7_results['scores'].values())
                    })
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    sns.barplot(x='Score', y='Question', data=gad7_df, palette='Blues_d', orient='h')
                    ax.set_xlim(0, 3)
                    ax.set_xticks([0, 1, 2, 3])
                    ax.set_xticklabels(['Not at all', 'Several days', 'More than half the days', 'Nearly every day'])
                    plt.tight_layout()
                    st.pyplot(fig)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Display PHQ-9 scores
                with st.container():
                    st.markdown("<div class='assessment-card'>", unsafe_allow_html=True)
                    st.markdown("<h4>PHQ-9 Assessment (Depression)</h4>", unsafe_allow_html=True)
                    st.write(f"Total Score: {phq9_results['total_score']} - {phq9_results['severity']}")
                    
                    # Create a bar chart for PHQ-9 scores
                    phq9_df = pd.DataFrame({
                        'Question': [phq9_questions[q] for q in phq9_results['scores'].keys()],
                        'Score': list(phq9_results['scores'].values())
                    })
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(x='Score', y='Question', data=phq9_df, palette='Reds_d', orient='h')
                    ax.set_xlim(0, 3)
                    ax.set_xticks([0, 1, 2, 3])
                    ax.set_xticklabels(['Not at all', 'Several days', 'More than half the days', 'Nearly every day'])
                    plt.tight_layout()
                    st.pyplot(fig)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Check if we have multiple sessions to compare
                if len(sorted_sessions) > 1:
                    st.markdown(f"<h3 class='sub-header'>Progress Tracking</h3>", unsafe_allow_html=True)
                    
                    # Create time series data for symptom tracking
                    session_dates = []
                    gad7_scores = []
                    phq9_scores = []
                    
                    for session_id, session in sorted_sessions:
                        session_date = datetime.strptime(session['date'], "%Y-%m-%d") if isinstance(session['date'], str) else datetime.now()
                        session_dates.append(session_date)
                        
                        # Calculate scores
                        session_symptoms = extract_symptoms(session['data'])
                        session_gad7 = map_to_gad7(session_symptoms)
                        session_phq9 = map_to_phq9(session_symptoms, session['data'])
                        
                        gad7_scores.append(session_gad7['total_score'])
                        phq9_scores.append(session_phq9['total_score'])
                    
                    # Reverse the lists to show chronological order
                    session_dates.reverse()
                    gad7_scores.reverse()
                    phq9_scores.reverse()
                    
                    # Plot assessment scores over time
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(session_dates, gad7_scores, marker='o', linestyle='-', label='GAD-7 (Anxiety)', color='blue')
                    ax.plot(session_dates, phq9_scores, marker='s', linestyle='-', label='PHQ-9 (Depression)', color='red')
                    ax.set_xlabel('Session Date')
                    ax.set_ylabel('Score')
                    ax.set_title('Assessment Scores Over Time')
                    ax.grid(True, linestyle='--', alpha=0.7)
                    ax.legend()
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Show score interpretation
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("<h4>GAD-7 Interpretation</h4>", unsafe_allow_html=True)
                        st.write("0-4: Minimal anxiety")
                        st.write("5-9: Mild anxiety")
                        st.write("10-14: Moderate anxiety")
                        st.write("15-21: Severe anxiety")
                    
                    with col2:
                        st.markdown("<h4>PHQ-9 Interpretation</h4>", unsafe_allow_html=True)
                        st.write("0-4: None-minimal depression")
                        st.write("5-9: Mild depression")
                        st.write("10-14: Moderate depression")
                        st.write("15-19: Moderately severe depression")
                        st.write("20-27: Severe depression")

# Session Comparison Page
elif page == "Session Comparison":
    st.markdown('<h2 class="sub-header">Session Comparison</h2>', unsafe_allow_html=True)
    
    if not st.session_state.uploaded_sessions:
        st.info("No sessions have been uploaded yet. Please upload session notes first.")
    else:
        # Client selector
        client_options = list(st.session_state.uploaded_sessions.keys())
        selected_client = st.selectbox(
            "Select Client", 
            options=client_options,
            index=client_options.index(st.session_state.selected_client) if st.session_state.selected_client in client_options else 0
        )
        
        if selected_client:
            client_sessions = st.session_state.uploaded_sessions[selected_client]
            
            if len(client_sessions) < 2:
                st.warning("Need at least two sessions for comparison. Please upload more sessions.")
            else:
                # Create session selection options
                session_options = []
                for session_id, session in client_sessions.items():
                    session_options.append({
                        'id': session_id,
                        'label': f"{session['date']} - {session['file_name']}"
                    })
                
                # Sort sessions by date
                session_options.sort(key=lambda x: client_sessions[x['id']]['date'], reverse=True)
                
                # Session selectors
                col1, col2 = st.columns(2)
                with col1:
                    first_session = st.selectbox(
                        "First Session (Earlier)", 
                        options=[s['id'] for s in session_options],
                        format_func=lambda s: next((opt['label'] for opt in session_options if opt['id'] == s), s)
                    )
                
                with col2:
                    # Filter out the selected first session
                    second_options = [s for s in session_options if s['id'] != first_session]
                    second_session = st.selectbox(
                        "Second Session (Later)", 
                        options=[s['id'] for s in second_options],
                        format_func=lambda s: next((opt['label'] for opt in session_options if opt['id'] == s), s)
                    )
                
                # Compare button
                if st.button("Compare Sessions"):
                    # Check if both sessions are selected
                    if first_session and second_session:
                        # Get session data
                        first_data = client_sessions[first_session]['data']
                        second_data = client_sessions[second_session]['data']
                        
                        # Calculate progress
                        progress_data = calculate_progress(first_data, second_data)
                        
                        # Store in session state for reference
                        comparison_key = f"{first_session}_{second_session}"
                        if selected_client not in st.session_state.session_comparisons:
                            st.session_state.session_comparisons[selected_client] = {}
                        st.session_state.session_comparisons[selected_client][comparison_key] = progress_data
                        
                        # Display comparison results
                        st.markdown("<h3 class='sub-header'>Comparison Results</h3>", unsafe_allow_html=True)
                        
                        # Overall progress
                        st.markdown("<h4>Overall Progress</h4>", unsafe_allow_html=True)
                        overall_score = progress_data['overall_progress_score']
                        
                        if overall_score > 0.3:
                            st.markdown(f"<p class='progress-improved'>Significant Improvement: {overall_score:.2f}</p>", unsafe_allow_html=True)
                        elif overall_score > 0:
                            st.markdown(f"<p class='progress-improved'>Slight Improvement: {overall_score:.2f}</p>", unsafe_allow_html=True)
                        elif overall_score < -0.3:
                            st.markdown(f"<p class='progress-worsened'>Significant Worsening: {overall_score:.2f}</p>", unsafe_allow_html=True)
                        elif overall_score < 0:
                            st.markdown(f"<p class='progress-worsened'>Slight Worsening: {overall_score:.2f}</p>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<p class='progress-unchanged'>Unchanged: {overall_score:.2f}</p>", unsafe_allow_html=True)
                        
                        # Assessment changes
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("<h4>GAD-7 Change</h4>", unsafe_allow_html=True)
                            gad7_change = progress_data['gad7_change']
                            
                            st.write(f"First Session: {progress_data['first_gad7']['total_score']} ({progress_data['first_gad7']['severity']})")
                            st.write(f"Second Session: {progress_data['second_gad7']['total_score']} ({progress_data['second_gad7']['severity']})")
                            
                            if gad7_change < 0:
                                st.markdown(f"<p class='progress-improved'>Improved by {-gad7_change} points</p>", unsafe_allow_html=True)
                            elif gad7_change > 0:
                                st.markdown(f"<p class='progress-worsened'>Worsened by {gad7_change} points</p>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<p class='progress-unchanged'>No change in score</p>", unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("<h4>PHQ-9 Change</h4>", unsafe_allow_html=True)
                            phq9_change = progress_data['phq9_change']
                            
                            st.write(f"First Session: {progress_data['first_phq9']['total_score']} ({progress_data['first_phq9']['severity']})")
                            st.write(f"Second Session: {progress_data['second_phq9']['total_score']} ({progress_data['second_phq9']['severity']})")
                            
                            if phq9_change < 0:
                                st.markdown(f"<p class='progress-improved'>Improved by {-phq9_change} points</p>", unsafe_allow_html=True)
                            elif phq9_change > 0:
                                st.markdown(f"<p class='progress-worsened'>Worsened by {phq9_change} points</p>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<p class='progress-unchanged'>No change in score</p>", unsafe_allow_html=True)
                        
                        # Symptom changes
                        st.markdown("<h4>Symptom Changes</h4>", unsafe_allow_html=True)
                        
                        if progress_data['matched_symptoms']:
                            for symptom in progress_data['matched_symptoms']:
                                with st.container():
                                    st.markdown(f"<div class='symptom-card'>", unsafe_allow_html=True)
                                    st.markdown(f"<strong>{symptom['description']}</strong>", unsafe_allow_html=True)
                                    
                                    # Display the change direction with appropriate styling
                                    if symptom['change']['direction'] == 'improved':
                                        st.markdown(f"<p class='progress-improved'>{symptom['change']['description']}</p>", unsafe_allow_html=True)
                                    elif symptom['change']['direction'] == 'worsened':
                                        st.markdown(f"<p class='progress-worsened'>{symptom['change']['description']}</p>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"<p class='progress-unchanged'>{symptom['change']['description']}</p>", unsafe_allow_html=True)
                                    
                                    # Show more details
                                    st.write(f"First Session: {symptom['first_intensity']} ({symptom['first_frequency']})")
                                    st.write(f"Second Session: {symptom['second_intensity']} ({symptom['second_frequency']})")
                                    st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.write("No matched symptoms between sessions.")
                        
                        # New symptoms
                        if progress_data['new_symptoms']:
                            st.markdown("<h4>New Symptoms</h4>", unsafe_allow_html=True)
                            for symptom in progress_data['new_symptoms']:
                                with st.container():
                                    st.markdown(f"<div class='symptom-card'>", unsafe_allow_html=True)
                                    st.markdown(f"<strong>{symptom['description']}</strong>", unsafe_allow_html=True)
                                    st.write(f"Intensity: {symptom['intensity']}")
                                    st.write(f"Frequency: {symptom['frequency']}")
                                    if symptom['quote']:
                                        st.markdown(f"<em>\"{symptom['quote']}\"</em>", unsafe_allow_html=True)
                                    st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Resolved symptoms
                        if progress_data['resolved_symptoms']:
                            st.markdown("<h4>Resolved Symptoms</h4>", unsafe_allow_html=True)
                            for symptom in progress_data['resolved_symptoms']:
                                with st.container():
                                    st.markdown(f"<div class='symptom-card'>", unsafe_allow_html=True)
                                    st.markdown(f"<strong>{symptom['description']}</strong> (Resolved)", unsafe_allow_html=True)
                                    st.write(f"Previous Intensity: {symptom['intensity']}")
                                    st.write(f"Previous Frequency: {symptom['frequency']}")
                                    st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Clinical insights
                        st.markdown("<h4>Clinical Insights</h4>", unsafe_allow_html=True)
                        insights = generate_insights(progress_data)
                        
                        for insight in insights:
                            st.markdown(f"<div class='info-box'>• {insight}</div>", unsafe_allow_html=True)

# Help Page
elif page == "Help":
    st.markdown('<h2 class="sub-header">Help & Documentation</h2>', unsafe_allow_html=True)
    
    st.markdown("""### About This Application
    
This application helps therapists track client progress across therapy sessions by analyzing session notes. 

### Key Features

1. **Upload Session Notes**: Upload JSON-formatted session notes to build client profiles.
   
2. **Client Dashboard**: View client details, symptom assessments, and progress metrics.
   
3. **Session Comparison**: Compare any two sessions to track changes in symptoms and assessments.
   
4. **Standardized Assessments**: Automatic mapping of symptoms to GAD-7 (anxiety) and PHQ-9 (depression) assessments.

### How To Use

1. Start by uploading session notes for your clients in the "Upload Sessions" page.
   
2. View individual client dashboards to see their current symptoms and assessment scores.
   
3. Compare sessions to analyze progress, see resolved symptoms, and get clinical insights.

### Session Notes Format

The application expects session notes in a specific JSON format with the following key sections:

- **Presentation**: Client's presenting concerns
- **Psychological Factors**: Symptoms, cognitive patterns, emotional responses
- **Biological Factors**: Sleep, nutrition, exercise, medication
- **Social Factors**: Family dynamics, social support, work/school
- **Risk Assessment**: Suicidality, self-harm, hopelessness
- **Mental Status Exam**: Clinical observations

### Assessment Interpretations

**GAD-7 (Anxiety)**
- 0-4: Minimal anxiety
- 5-9: Mild anxiety
- 10-14: Moderate anxiety
- 15-21: Severe anxiety

**PHQ-9 (Depression)**
- 0-4: Minimal depression
- 5-9: Mild depression
- 10-14: Moderate depression
- 15-19: Moderately severe depression
- 20-27: Severe depression
""")
