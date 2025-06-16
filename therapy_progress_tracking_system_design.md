# System Design: Therapy Progress Tracking Application

## Implementation approach

After analyzing the requirements and sample data files, I've identified the key challenges and selected appropriate technologies for implementing the therapy progress tracking application:

### Key Technical Challenges

1. **Complex Data Extraction**: The system must accurately extract and compare symptom information from structured JSON therapy notes, which requires sophisticated parsing and natural language understanding.

2. **Standardized Assessment Mapping**: We need to map extracted symptoms to standardized assessment frameworks (GAD-7, PHQ-9) while preserving clinical validity.

3. **Meaningful Progress Tracking**: The system must detect subtle changes in symptoms and accurately measure client progress across sessions.

4. **Intuitive Visualization**: Therapists need clear visual representations of client progress that are easy to interpret and actionable.

### Selected Technologies

1. **Frontend**: 
   - React.js for building the user interface
   - Tailwind CSS for responsive and consistent styling
   - Chart.js for interactive data visualizations
   - React Router for navigation between application views

2. **Backend**:
   - FastAPI (Python) for efficient API development
   - Pydantic for data validation and serialization
   - CORS middleware for secure cross-origin requests

3. **AI Processing**:
   - spaCy for NLP tasks and entity recognition
   - Scikit-learn for progress prediction modeling
   - Sentence-Transformers for semantic text comparison
   - Hugging Face Transformers for advanced NLP tasks

4. **Deployment**:
   - Docker for containerization
   - Docker Compose for service orchestration
   - Nginx for serving static assets and reverse proxy

### Open Source Libraries

1. **NLP and Machine Learning**:
   - spaCy (v3.6.0): Industrial-strength NLP library for symptom extraction
   - Scikit-learn (v1.2.2): For implementing the progress prediction model
   - Sentence-Transformers (v2.2.2): For semantic comparison of symptoms across sessions
   - NLTK (v3.8): For text preprocessing and analysis

2. **Web Development**:
   - React (v18.2.0): For building the user interface
   - Tailwind CSS (v3.3.0): For styling the application
   - Chart.js (v4.3.0): For creating interactive visualizations
   - React Router (v6.10.0): For client-side routing

3. **API Development**:
   - FastAPI (v0.95.1): For building the backend API
   - Pydantic (v1.10.7): For data validation
   - Uvicorn (v0.22.0): ASGI server for FastAPI
   - Python-multipart (v0.0.6): For handling file uploads

4. **Testing and Documentation**:
   - Jest (v29.5.0): For frontend testing
   - Pytest (v7.3.1): For backend testing
   - Swagger UI: For API documentation (built into FastAPI)
   - ReDoc: Alternative API documentation (built into FastAPI)

## Architecture Overview

The Therapy Progress Tracking application follows a modern microservice-oriented architecture with clear separation of concerns:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│                  │     │                  │     │                  │
│   Frontend UI    │────▶│   REST API       │────▶│   AI Processing  │
│   (React.js)     │◀────│   (FastAPI)      │◀────│   Services       │
│                  │     │                  │     │                  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Frontend Architecture

The frontend follows a component-based architecture using React:

```
┌────────────────────────────────────────────────────┐
│                  App Container                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Dashboard  │  │  Session    │  │  Progress   │ │
│  │  View       │  │  Comparison │  │  Details    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│  ┌─────────────┐  ┌─────────────┐                 │
│  │  Upload     │  │  Settings   │                 │
│  │  Component  │  │  Panel      │                 │
│  └─────────────┘  └─────────────┘                 │
└────────────────────────────────────────────────────┘
```

### Backend Architecture

The backend uses a service-oriented architecture with the following components:

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ API Gateway   │────▶│ Session       │────▶│ Symptom       │
│ (FastAPI)     │     │ Service       │     │ Extractor     │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Assessment    │     │ Progress      │     │ Insight       │
│ Mapper        │     │ Tracker      │     │ Generator     │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                     │
        └─────────────┬─────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Visualization │
              │ Service       │
              └───────────────┘
```

## Data structures and interfaces

The system uses a comprehensive set of data structures to model the therapy progress tracking domain. Please refer to the class diagram in `therapy_progress_tracking_class_diagram.mermaid` for a detailed view of the data structures and their relationships.

### Key API Endpoints

1. **Session Management**
   - `POST /api/sessions/upload`: Upload a new session file
   - `GET /api/sessions/list`: List available sessions
   - `GET /api/sessions/{id}`: Get session details

2. **Comparison**
   - `POST /api/sessions/compare`: Compare two sessions
   - `GET /api/comparison/{id}`: Get comparison results
   - `GET /api/comparison/{id}/details`: Get detailed comparison

3. **Assessment**
   - `GET /api/sessions/{id}/assessments`: Get assessment scores
   - `GET /api/comparison/{id}/assessment-changes`: Get assessment changes

4. **Insights**
   - `GET /api/comparison/{id}/insights`: Get insights
   - `GET /api/comparison/{id}/recommendations`: Get recommendations

5. **Visualization**
   - `GET /api/visualization/progress-chart/{id}`: Get progress chart data
   - `GET /api/visualization/symptom-chart/{id}`: Get symptom chart data
   - `GET /api/visualization/assessment-chart/{id}`: Get assessment chart data

### Data Flow

1. **Session Upload Flow**
   - Client sends JSON file to backend
   - Backend validates and stores the file
   - Backend extracts symptoms and client information
   - Backend maps symptoms to standardized assessments
   - Backend returns session metadata to client

2. **Comparison Flow**
   - Client requests comparison of two sessions
   - Backend retrieves both sessions
   - Backend performs symptom matching across sessions
   - Backend calculates progress metrics and scores
   - Backend generates insights and recommendations
   - Backend returns comparison results to client

## Program call flow

The detailed program call flow is documented in the sequence diagram in `therapy_progress_tracking_sequence_diagram.mermaid`. The diagram illustrates the interactions between system components during key operations such as session upload, comparison, and visualization.

## Technical Implementation Strategy

### 1. Frontend Implementation

#### Component Structure

```
src/
├── components/
│   ├── common/
│   │   ├── Header.jsx
│   │   ├── Footer.jsx
│   │   ├── Sidebar.jsx
│   │   └── ...
│   ├── dashboard/
│   │   ├── Dashboard.jsx
│   │   ├── ProgressSummary.jsx
│   │   ├── RecentSessions.jsx
│   │   └── ...
│   ├── upload/
│   │   ├── UploadForm.jsx
│   │   ├── FileValidator.jsx
│   │   └── ...
│   ├── comparison/
│   │   ├── ComparisonView.jsx
│   │   ├── SymptomComparison.jsx
│   │   ├── AssessmentScores.jsx
│   │   └── ...
│   ├── visualization/
│   │   ├── ProgressChart.jsx
│   │   ├── SymptomChart.jsx
│   │   ├── AssessmentChart.jsx
│   │   └── ...
│   └── insights/
│       ├── InsightList.jsx
│       ├── RecommendationCard.jsx
│       └── ...
├── services/
│   ├── api.js
│   ├── sessionService.js
│   ├── comparisonService.js
│   └── ...
├── hooks/
│   ├── useSession.js
│   ├── useComparison.js
│   └── ...
├── utils/
│   ├── formatters.js
│   ├── validators.js
│   └── ...
├── contexts/
│   ├── SessionContext.js
│   ├── ComparisonContext.js
│   └── ...
└── App.jsx
```

#### UI Screens

1. **Upload Screen**
   - File drag-and-drop area
   - Session metadata form
   - Upload progress indicator
   - Validation feedback

2. **Dashboard**
   - Client session overview
   - Recent uploads list
   - Quick comparison launcher
   - Progress summary cards

3. **Session Comparison**
   - Side-by-side session summary
   - Overall progress score
   - Symptom change visualization
   - Assessment score comparison

4. **Detailed Analysis**
   - Comprehensive symptom analysis
   - Trend charts and graphs
   - Insight and recommendation cards
   - Export/share options

### 2. Backend Implementation

#### Service Structure

```
app/
├── api/
│   ├── routes/
│   │   ├── sessions.py
│   │   ├── comparisons.py
│   │   ├── assessments.py
│   │   ├── insights.py
│   │   └── visualization.py
│   └── dependencies.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── logging.py
├── models/
│   ├── session.py
│   ├── symptom.py
│   ├── assessment.py
│   ├── comparison.py
│   └── insight.py
├── services/
│   ├── session_service.py
│   ├── symptom_extractor.py
│   ├── progress_tracker.py
│   ├── assessment_mapper.py
│   └── insight_generator.py
├── utils/
│   ├── json_processor.py
│   ├── nlp_utils.py
│   └── math_utils.py
├── ai/
│   ├── models/
│   │   ├── symptom_classifier.py
│   │   └── progress_predictor.py
│   ├── data/
│   │   ├── gad7_questions.json
│   │   └── phq9_questions.json
│   └── utils/
│       ├── text_preprocessing.py
│       └── model_helpers.py
└── main.py
```

#### AI Processing Modules

1. **Symptom Extractor**
   - Parse JSON structure
   - Extract symptom entities and attributes
   - Classify symptoms by category
   - Calculate severity scores

2. **Symptom Matcher**
   - Create embeddings for symptoms
   - Calculate similarity between symptoms
   - Match symptoms across sessions
   - Detect new and resolved symptoms

3. **Progress Tracker**
   - Calculate change metrics for symptoms
   - Identify improved and worsened symptoms
   - Compute overall progress score
   - Generate progress summaries

4. **Assessment Mapper**
   - Map symptoms to GAD-7 questions
   - Map symptoms to PHQ-9 questions
   - Calculate assessment scores
   - Compare scores across sessions

5. **Insight Generator**
   - Analyze progress patterns
   - Identify key areas of change
   - Generate actionable recommendations
   - Prioritize insights by relevance

### 3. Implementation Phases

#### Phase 1: Core Foundation

1. Setup project structure and dependencies
2. Implement basic session file upload and parsing
3. Develop initial symptom extraction logic
4. Create minimal UI with upload and session list views
5. Establish CI/CD pipeline for development

#### Phase 2: Analysis Engine

1. Implement symptom matching algorithm
2. Develop progress tracking metrics
3. Create standardized assessment mappers
4. Build comparison logic and data models
5. Implement initial API endpoints

#### Phase 3: Visualization and UI

1. Develop dashboard components and views
2. Create data visualization charts and graphs
3. Implement comparison view with interactive elements
4. Design and build detailed analysis screens
5. Add export functionality for reports

#### Phase 4: Advanced AI and Insights

1. Enhance symptom extraction with advanced NLP
2. Fine-tune progress prediction model
3. Implement insight generation algorithm
4. Create recommendation engine
5. Improve assessment mapping accuracy

## Anything UNCLEAR

1. **Data Privacy and Security**: While not fully addressed in the POC requirements, production implementation would need to comply with healthcare data regulations (HIPAA). For the POC, we'll focus on temporary data storage with no permanent retention.

2. **Scale of Deployment**: The requirements don't specify the expected user load or data volume. The current design assumes a moderate scale appropriate for a POC.

3. **Authentication Requirements**: The POC doesn't specify authentication needs. We'll design a simple authentication system that can be expanded in future versions.

4. **Integration Points**: While mentioned as a future consideration, the specific integration requirements with existing Mentalyc systems are unclear. We'll design flexible APIs that can facilitate future integration.

5. **Clinical Validation**: The accuracy of the symptom extraction and assessment mapping will need clinical validation. We should establish a process for therapists to verify and provide feedback on the system's outputs.

## Conclusion

The proposed system architecture for the Therapy Progress Tracking application provides a solid foundation for developing a POC that meets the requirements specified in the PRD. The combination of modern web technologies, AI capabilities, and clinical assessment frameworks will enable therapists to track client progress effectively and gain valuable insights to improve therapy outcomes.

The modular design allows for incremental development and easy extension as requirements evolve. The use of open-source libraries and industry-standard practices ensures maintainability and scalability for future enhancements.