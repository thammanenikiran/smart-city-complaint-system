# AI Architecture — Smart City Complaint Management System

## Overview

This document describes the AI/ML pipeline used to analyze civic complaints.
The system uses a multimodal approach combining NLP text analysis with
Computer Vision (Gemini Vision LLM) to automatically classify, prioritize,
and route complaints to appropriate departments.

---

## Pipeline Flow

```
Citizen Submission
       │
       ▼
┌─────────────────────────────────────────┐
│         COMPLAINT SUBMITTED             │
│  (text + optional image/video + location)│
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌───────────┐    ┌──────────────┐
│ NLP TEXT  │    │ GEMINI VISION│
│ PIPELINE  │    │  (on image)  │
└─────┬─────┘    └──────┬───────┘
      │                 │
      ▼                 ▼
┌──────────────────────────────┐
│    MULTIMODAL FUSION         │
│  (confidence-based merge)    │
└──────────────┬───────────────┘
               │
    ┌──────────┼───────────┐
    │          │           │
    ▼          ▼           ▼
┌────────┐ ┌────────┐ ┌───────────┐
│PRIORITY│ │DEPT    │ │DUPLICATE  │
│ENGINE  │ │ROUTING │ │DETECTION  │
└────────┘ └────────┘ └───────────┘
```

---

## 1. NLP Text Analysis Pipeline

### 1.1 Language Detection
- **Service**: `services/nlp_service.py`
- **Model**: `langdetect` library
- **Output**: ISO language code (en, hi, ta, etc.)

### 1.2 Intent Classification
- **Service**: `services/intent_classifier.py`
- **Model**: `facebook/bart-large-mnli` (zero-shot classification)
- **Labels**:
  - REPORT_ISSUE
  - REQUEST_REPAIR
  - REPORT_HAZARD
  - REPORT_OVERFLOW
  - REPORT_DAMAGE
  - GENERAL_QUERY
- **Output**: Intent label + confidence score

### 1.3 Category Classification
- **Service**: `services/intent_classifier.py`
- **Model**: `facebook/bart-large-mnli` (zero-shot classification)
- **Categories**:
  - pothole, damaged_road, garbage, overflowing_bin,
    broken_streetlight, water_leakage, damaged_traffic_sign,
    fallen_tree, damaged_crosswalk, other
- **Output**: Category label + confidence score

### 1.4 Named Entity Recognition (NER)
- **Service**: `services/ner_service.py`
- **Model**: `dslim/bert-base-NER`
- **Extracts**: Person names, locations, organizations from text
- **Output**: List of entity dictionaries

### 1.5 Sentiment Analysis
- **Service**: `services/sentiment_service.py`
- **Model**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Output**: POSITIVE/NEGATIVE + confidence score
- **Usage**: Fed into priority engine (angry = higher urgency)

### 1.6 Urgency Classification
- **Service**: `services/intent_classifier.py`
- **Model**: `facebook/bart-large-mnli` (zero-shot)
- **Output**: HIGH / MEDIUM / LOW + confidence

### 1.7 Text Summarization
- **Service**: `services/summarization_service.py`
- **Model**: `google/flan-t5-small` (text2text-generation)
- **Input**: Long complaint description
- **Output**: Concise one-sentence summary
- **Fallback**: Text truncation if model unavailable

---

## 2. Vision Analysis (PRIMARY)

### 2.1 Gemini Vision LLM
- **Service**: `services/vision_service.py`
- **Model**: `gemini-3.6-flash` (Google Gemini)
- **Role**: PRIMARY image understanding system
- **Input**: Complaint image file
- **Output**: Structured JSON with:
  - `issue`: Detected civic problem type
  - `severity`: HIGH / MEDIUM / LOW
  - `department`: Suggested department
  - `description`: Detailed image description
  - `confidence`: Confidence score (0-1)

### 2.2 YOLO Object Detection (OPTIONAL FALLBACK)
- **Service**: `services/object_detection.py`, `services/yolo_detector.py`
- **Models**:
  - `yolo11n.pt` — General object detection
  - Custom trained model — Civic issue detection
- **Role**: Optional/experimental fallback, not loaded on startup

---

## 3. Multimodal Fusion

- **Service**: `services/fusion_service.py`
- **Strategy**: Confidence-based fusion

### Decision Logic:
| Scenario | Action |
|---|---|
| Text + Image AGREE | Boost confidence (FUSED), auto-classify |
| Text + Image DISAGREE | Use higher-confidence result, flag if below 0.80 |
| Text ONLY | Use NLP, flag if below 0.80 |
| Image ONLY | Use Vision, flag if below 0.80 |
| NEITHER | Flag for manual review |

### Confidence Thresholds:
- **≥ 0.80**: Auto-classify (no review needed)
- **0.50 – 0.79**: Flag for admin review
- **< 0.50**: Require manual review

---

## 4. Priority Engine

- **Service**: `services/priority_service.py`
- **Algorithm**: Weighted multimodal scoring

### Weights:
| Factor | Weight |
|---|---|
| NLP Urgency | 30% |
| Vision Severity | 30% |
| Sentiment | 15% |
| Safety Keywords | 15% |
| Duplicate Status | 10% |

### Priority Mapping:
| Score Range | Priority |
|---|---|
| ≥ 0.75 | CRITICAL |
| 0.55 – 0.74 | HIGH |
| 0.35 – 0.54 | MEDIUM |
| < 0.35 | LOW |

---

## 5. Duplicate Detection

- **Service**: `services/similarity_service.py`
- **Model**: `all-MiniLM-L6-v2` (Sentence-BERT)
- **Algorithm**: Cosine similarity on sentence embeddings
- **Threshold**: 85% similarity = duplicate
- **Scope**: Checks against last 100 complaints

---

## 6. Department Routing

- **Service**: `services/department_router.py`
- **Algorithm**: Category → Department mapping (centralized dictionary)
- **Priority**: Vision-based routing first, NLP fallback

### Category → Department:
| Category | Department |
|---|---|
| pothole, damaged_road, damaged_crosswalk | Roads |
| garbage, overflowing_bin | Sanitation |
| water_leakage | Water Supply |
| broken_streetlight | Electrical |
| damaged_traffic_sign | Traffic |
| fallen_tree | Parks and Gardens |
| (health hazards) | Public Health |

---

## 7. Model Loading Strategy

All AI models are loaded as **module-level singletons** on first import.
This means:
- Models load once at application startup
- No per-request model loading overhead
- ~2-3GB RAM required for all NLP models
- Gemini Vision uses API calls (no local model weight)

### Models in Memory:
1. BART-MNLI (zero-shot classifier) — ~400MB
2. BERT-NER — ~400MB
3. DistilBERT-Sentiment — ~250MB
4. Sentence-BERT (MiniLM) — ~90MB
5. FLAN-T5-small — ~300MB

---

## 8. AI Result Storage

All AI analysis results are stored in the `ai_results` table:

### NLP Fields:
- language, intent, detected_category, sentiment, urgency
- summary, keywords, entities
- confidence, model_name
- intent_confidence, urgency_confidence, sentiment_confidence

### Vision Fields:
- vision_issue, vision_severity, vision_department
- vision_description, vision_confidence

---

## 9. Technology Stack

| Component | Technology |
|---|---|
| NLP Framework | HuggingFace Transformers |
| Zero-shot | facebook/bart-large-mnli |
| NER | dslim/bert-base-NER |
| Sentiment | distilbert-base-uncased-finetuned-sst-2-english |
| Embeddings | all-MiniLM-L6-v2 (sentence-transformers) |
| Summarization | google/flan-t5-small |
| Vision LLM | Google Gemini (gemini-3.6-flash) |
| Object Detection | YOLO v11 (optional) |
| Language Detection | langdetect |

