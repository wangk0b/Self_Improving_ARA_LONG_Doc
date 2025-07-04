# Self-Improving Agentic Framework for Long-Context Arabic Document Understanding

This repository contains the implementation of our **Self-Improving Multi-Agent Interactive QA Generation Pipeline**. The system automatically crawls, preprocesses, and generates high-quality, context-aware question–answer pairs from multi-page Arabic documents, iteratively refining its own performance through a closed feedback loop.

---
![UI Screenshot](./qa_agent.png)
## 🔍 Key Features

- **End-to-End Automation**  
  From web crawling to final QA pair validation—no human annotation required.

- **Multi-Agent Collaboration**  
  Five specialized agents:
  1. **Layout Agent**: Segments pages into logical elements (text, tables, figures).  
  2. **Question Generator**: Drafts context-aware questions.  
  3. **Answer Generator/Extractor**: Produces and extracts candidate answers.  
  4. **Evaluation Agent**: Scores QA pairs and issues feedback.  
  5. **Validator Agent**: Verifies evidence and finalizes QA pairs.

- **Self-Improvement Loop**  
  Low-confidence outputs trigger automatic regeneration and model updates, progressively boosting difficulty and accuracy.

- **Controllable Difficulty**  
  Adjustable accuracy thresholds (No Gate / 50% / 25%) to generate data from easy recall to deep inference—ideal for curriculum learning.

- **Benchmark & Dataset**  
  Includes **AraLongBench**, a large-scale, multi-page Arabic QA benchmark for long-context evaluation.

---

## 📂 Project Structure

```text
.
├── config.yaml                 # Pipeline configuration (input paths, thresholds, model names)
├── multi_agent_interactive.py  # Main entrypoint for the self-improving QA pipeline
├── agents/
│   ├── layout_agent.py         # Page segmentation and layout parsing
│   ├── question_agent.py       # Question drafting & refinement
│   ├── answer_agent.py         # Answer generation and extraction
│   ├── evaluation_agent.py     # QA scoring and feedback
│   └── validator_agent.py      # Final QA validation
├── data_acquisition/
│   ├── crawler.py              # Web crawler and license‐compliance filtering
│   ├── scraper.py              # HTML/PDF scraping utilities
│   └── normalization.py        # Text cleaning, bidi handling, diacritics
├── preprocessing/
│   ├── ocr_agent.py            # OCR wrapper (Tesseract / custom models)
│   └── chunker.py              # Document chunking with overlap
├── benchmarks/
│   └── AraLongBench/           # Benchmark definitions and evaluation scripts
├── requirements.txt            # Python dependencies
└── README.md                   # This file

