import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report
import joblib
from pathlib import Path
import sys


CANDIDATE_PATHS = [
    Path("spam.csv"),
    Path("data/spam.csv"),
    Path("./datasets/spam.csv"),
]

csv_path = next((p for p in CANDIDATE_PATHS if p.exists()), None)
if csv_path is None:
    sys.exit(" No se encontró 'spam.csv'. Colócalo en la carpeta del proyecto o en 'data/spam.csv' y vuelve a correr.")

print(f" Usando dataset: {csv_path}")

# Carga y preprocesado
df = pd.read_csv(csv_path, encoding="latin-1")[["v1", "v2"]]
df.columns = ["label", "text"]
df["label"] = df["label"].map({"ham": 0, "spam": 1})

X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
)

# Vectorizador + modelo
vectorizer = CountVectorizer()
X_train_vect = vectorizer.fit_transform(X_train)
X_test_vect  = vectorizer.transform(X_test)

model = MultinomialNB()
model.fit(X_train_vect, y_train)

# Métricas rápidas
y_pred = model.predict(X_test_vect)
acc = accuracy_score(y_test, y_pred)
print(f" Precisión: {acc:.3f}")
print(classification_report(y_test, y_pred, digits=3))

# Guardar artefactos
joblib.dump(model, "modelo_entrenado.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
print(" Guardados: modelo_entrenado.pkl, vectorizer.pkl")
