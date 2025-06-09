import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
import joblib

# 1. Cargar el dataset
df = pd.read_csv("spam.csv", encoding='latin-1')[["v1", "v2"]]
df.columns = ["label", "text"]

# 2. Convertir etiquetas
df["label"] = df["label"].map({"ham": 0, "spam": 1})

# 3. Separar datos
X = df["text"]
y = df["label"]

# 4. Dividir en entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Vectorización
vectorizer = CountVectorizer()
X_train_vect = vectorizer.fit_transform(X_train)
X_test_vect = vectorizer.transform(X_test)

# 6. Modelo
model = MultinomialNB()
model.fit(X_train_vect, y_train)

# 7. Evaluación
y_pred = model.predict(X_test_vect)
print(f"✅ Precisión del modelo: {accuracy_score(y_test, y_pred):.2f}")

# 8. Guardar modelo y vectorizador
joblib.dump(model, "modelo_entrenado.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
