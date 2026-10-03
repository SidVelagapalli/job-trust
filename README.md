# Job Trust Score

Scores a job posting for two kinds of risk:

- **Scam risk** — a trained machine-learning model estimates how likely the posting is fraudulent.
- **Ghost-job risk** — a set of **hand-written rules (not machine learning)** estimates how likely the
  posting is for a role the company isn't actively trying to fill.

## What it does

Send a posting (title, description, company profile, requirements, benefits, salary, and a few
yes/no facts) to `POST /score` and get back:

| Field | Meaning |
|---|---|
| `scam_probability` | Model's score from 0 to 1 (higher = more scam-like) |
| `flagged` | `true` if `scam_probability` ≥ 0.4 |
| `reasons` | Up to 5 words or posting facts that pushed the score most toward "scam" (e.g. "no company logo", "data entry") |
| `ghost_score` | 0–100 from the ghost-job rules |
| `ghost_reasons` | Which rules fired and how many points each added |
| `ghost_method` | Always `"rules"` — a reminder that this part is not ML |

The ghost-job rules: no salary listed (15), description under 80 words (15), phrases like "always
hiring" / "talent pool" / "future opportunities" (25), and two optional answers from the user —
posted more than 30 days ago (25) and "I've seen this posted before" (20).

## Data

- **Source:** [Real / Fake Job Posting Prediction](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction)
  on Kaggle, from the University of the Aegean's EMSCAD dataset (downloaded from an identical
  [Hugging Face mirror](https://huggingface.co/datasets/victor/real-or-fake-fake-jobposting-prediction)).
  17,880 postings from 2012–2014, each labelled real or fake; 866 (4.8%) are fake.
- **Deduplication:** 1,814 postings were exact copies of another posting's combined text, so they
  were removed, leaving **16,066**. Without this, copies of the same ad could land in both the
  training and test sets and inflate the results.
- The data file is not committed (`data/` is gitignored).

## Model

- **Text:** title, company profile, description, requirements and benefits are joined and turned
  into numbers with **TF-IDF** (single words and two-word phrases, top 20,000).
- **Metadata:** five yes/no features — has company logo, has screening questions, remote,
  salary listed, has company profile.
- **Classifier:** logistic regression with `class_weight="balanced"` (so the rare scam class isn't
  ignored) and `C=10`, chosen by 5-fold cross-validated grid search on the training set.
- **Threshold:** 0.4, chosen from cross-validated predictions on the training set only.
- **Reasons:** each word's contribution is its TF-IDF value × its weight; each yes/no feature's is
  measured against the opposite answer (so "no company logo" counts). Only contributions of at
  least 0.2 are shown. They rank what pushed toward "scam"; they are not an exact breakdown of
  the score.

Notebooks: `01_explore` (data), `02_baseline` (first model), `03_improve` (final model).

## Results

Final model (v1), evaluated once on the held-out test set (3,214 postings, 144 fake) at threshold 0.4:

| Metric | Baseline (notebook 02) | **v1 (notebook 03)** |
|---|---|---|
| PR-AUC | 0.819 | **0.857** |
| Recall (share of scams caught) | 81.9% | **83.3%** |
| Precision (share of flags that are scams) | 58.7% | **64.9%** |

For comparison, a "model" that calls everything real scores 95.5% accuracy and catches 0% of
scams — which is why accuracy is not used here.

## Limitations

- **Old data (2012–2014).** The model only knows the vocabulary of those postings. Modern terms
  like "ML", "RAG", "AI" and "SWE" are invisible to it, and some fake-leaning words are quirks of
  that era (e.g. "ux", "data science"). Some top scam clues are company names from a cluster of
  fake ads in the dataset, so part of the score is memorising *who* posted scams then.
- **It can miss modern scams.** A hand-written scam using current tech buzzwords ("ML and RAG
  pipeline refining… Paying 25–35/hr") scored 0.12 and was **not** flagged.
- **Missing fields look suspicious.** "No company profile" and "no company logo" are strong
  signals, so a real posting scored without its "About us" text filled in gets pushed toward scam.
- **Overconfident probabilities.** Scores cluster near 0 and 1; treat them as a ranking, not a
  literal percentage.
- **The ghost score is rule-based, not ML.** The dataset labels scams only — no ghost-job labels,
  posting dates or repost history — so the rules and their points are judgement calls that have
  not been validated. A fixed phrase list also misses softer "talent pool" wording.
- **Early test-set exposure.** The test set was scored in notebook 02, before the final model was
  built, and what we saw there (e.g. the company-name clues) shaped later work. Notebooks 01 and 03
  also computed some summary statistics on the full dataset before splitting. So the final test
  numbers are slightly less "untouched" than ideal.

## Why this threshold

_TODO: written by the project owner._

## How to run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Put fake_job_postings.csv in data/ (only needed for the notebooks)

.venv/bin/pytest                              # run the tests
.venv/bin/uvicorn src.api:app --reload        # start the API
```

Then open http://127.0.0.1:8000/docs, click **POST /score → Try it out**, paste a posting, and click **Execute**.

## Layout

- `data/` — dataset (gitignored)
- `notebooks/` — exploration, baseline and improvement notebooks
- `src/predict.py` — scam scoring and reasons
- `src/ghost_rules.py` — ghost-job rules
- `src/api.py` — FastAPI app
- `models/job_trust_v1.joblib` — trained pipeline
- `tests/` — pytest tests
