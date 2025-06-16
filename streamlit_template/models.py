from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

@dataclass
class Symptom:
    """Represents a symptom with its attributes"""
    description: str
    intensity: str
    frequency: str
    duration: str
    quote: str = ""

@dataclass
class SymptomChange:
    """Tracks changes in a symptom between sessions"""
    intensity_change: int
    frequency_change: int
    direction: str  # 'improved', 'worsened', or 'unchanged'
    description: str
    score: float

@dataclass
class MatchedSymptom:
    """Represents a symptom that appears in both sessions being compared"""
    description: str
    first_intensity: str
    second_intensity: str
    first_frequency: str
    second_frequency: str
    change: SymptomChange

@dataclass
class AssessmentResult:
    """Stores results of standardized assessments (GAD-7, PHQ-9)"""
    scores: Dict[int, int]  # Question number -> score
    total_score: int
    severity: str

@dataclass
class ProgressData:
    """Contains all progress data between two sessions"""
    matched_symptoms: List[MatchedSymptom]
    new_symptoms: List[Symptom]
    resolved_symptoms: List[Symptom]
    overall_progress_score: float
    gad7_change: int
    phq9_change: int
    first_gad7: AssessmentResult
    second_gad7: AssessmentResult
    first_phq9: AssessmentResult
    second_phq9: AssessmentResult

@dataclass
class SessionInfo:
    """Stores information about a therapy session"""
    data: Dict[str, Any]
    date: str
    file_name: str

@dataclass
class ClientInfo:
    """Represents a client with their therapy sessions"""
    client_id: str
    sessions: Dict[str, SessionInfo] = field(default_factory=dict)
    gad7_history: List[Dict[str, Any]] = field(default_factory=list)
    phq9_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_session(self, session_id: str, session_data: Dict[str, Any], 
                   session_date: str, file_name: str):
        """Add a new session to the client's record"""
        self.sessions[session_id] = SessionInfo(
            data=session_data,
            date=session_date,
            file_name=file_name
        )
        
        # Update assessment histories
        symptoms = self.extract_symptoms(session_data)
        gad7_result = self.map_to_gad7(symptoms)
        phq9_result = self.map_to_phq9(symptoms, session_data)
        
        self.gad7_history.append({
            'date': session_date,
            'score': gad7_result.total_score,
            'severity': gad7_result.severity
        })
        
        self.phq9_history.append({
            'date': session_date,
            'score': phq9_result.total_score,
            'severity': phq9_result.severity
        })
    
    def extract_symptoms(self, session_data: Dict[str, Any]) -> List[Symptom]:
        """Extract symptoms from session data"""
        symptoms = []
        if 'Psychological Factors' in session_data:
            psych_factors = session_data['Psychological Factors']
            if 'Symptoms' in psych_factors and isinstance(psych_factors['Symptoms'], dict):
                for symptom_key, symptom_data in psych_factors['Symptoms'].items():
                    if isinstance(symptom_data, dict):
                        symptom = Symptom(
                            description=symptom_data.get('Description', 'Unknown'),
                            intensity=symptom_data.get('Intensity', 'Unknown'),
                            frequency=symptom_data.get('Frequency', 'Unknown'),
                            duration=symptom_data.get('Duration', 'Unknown'),
                            quote=symptom_data.get('Quote (Symptom)', '')
                        )
                        symptoms.append(symptom)
        
        # Additional symptom extraction logic...
        return symptoms
    
    def map_to_gad7(self, symptoms: List[Symptom]) -> AssessmentResult:
        """Map symptoms to GAD-7 assessment"""
        # Implementation similar to your existing function
        pass
    
    def map_to_phq9(self, symptoms: List[Symptom], session_data: Dict[str, Any]) -> AssessmentResult:
        """Map symptoms to PHQ-9 assessment"""
        # Implementation similar to your existing function
        pass

@dataclass
class TherapyProgressAppState:
    """Tracks the application state"""
    clients: Dict[str, ClientInfo] = field(default_factory=dict)
    selected_client: Optional[str] = None
    session_comparisons: Dict[str, Dict[str, ProgressData]] = field(default_factory=dict)