"""Entrena el clasificador Naive Bayes y guarda los artefactos en Backend/models/.

Uso:  python Backend/scripts/train_nb.py
Deps: pip install -r Backend/scripts/requirements-train.txt
"""
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_CANDIDATES = [BACKEND_DIR / "data" / "spam.csv", Path("spam.csv")]
MODELS_DIR = BACKEND_DIR / "models"

csv_path = next((p for p in DATA_CANDIDATES if p.exists()), None)
if csv_path is None:
    sys.exit("No se encontró 'spam.csv' en Backend/data/.")

print(f"Usando dataset: {csv_path}")
df = pd.read_csv(csv_path, encoding="latin-1")[["v1", "v2"]]
df.columns = ["label", "text"]
df["label"] = df["label"].map({"ham": 0, "spam": 1})

X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
)

vectorizer = CountVectorizer()
X_train_vect = vectorizer.fit_transform(X_train)
X_test_vect = vectorizer.transform(X_test)

model = MultinomialNB()
model.fit(X_train_vect, y_train)

y_pred = model.predict(X_test_vect)
print(f"Precisión: {accuracy_score(y_test, y_pred):.3f}")
print(classification_report(y_test, y_pred, digits=3))

MODELS_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODELS_DIR / "modelo_entrenado.pkl")
joblib.dump(vectorizer, MODELS_DIR / "vectorizer.pkl")
print(f"Guardados en {MODELS_DIR}: modelo_entrenado.pkl, vectorizer.pkl")
