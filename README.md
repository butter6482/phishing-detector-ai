🛡️ Phishing Detector — AI-powered email risk analyzer

https://phishing-detector-ai.onrender.com

Phishing Detector analyzes suspicious emails and provides a clear verdict with AI-generated explanations. It combines a local Naive Bayes classifier, real-time URL validation, and an LLM to deliver simple, trustworthy insights.

What’s included

🔍 Local ML (Naive Bayes) to classify phishing vs legit.

🧠 AI explanations via OpenRouter (summary + practical advice).

🌐 Google Safe Browsing for real-time URL validation.

📊 Risk score (0–100) with levels safe / warning / phishing.

🎨 Modern React + Tailwind dashboard UI.

⚡ FastAPI backend with /api/analyze endpoint.

🐳 Easy deployment with Docker + Render/Vercel.


Stack

Frontend: React + Vite + Tailwind

Backend: FastAPI (Uvicorn)

ML: scikit-learn (Naive Bayes)

LLM: OpenRouter

Infra: Docker + Render

How it works (flow)

Paste the email content into the analyzer.

The local model calculates score + suspicious keywords.

Google Safe Browsing checks URLs.

The LLM generates a concise explanation with recommendations.

The user gets a final combined result.
