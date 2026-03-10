"""
Seed script: Inserts 20+ GRE-style questions into MongoDB.
Each question has calibrated IRT parameters (a, b, c).

Usage:
    python -m scripts.seed_questions
"""

import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


GRE_QUESTIONS = [
    # ─── Algebra (Difficulty 0.1–1.0) ───────────────────────────────
    {
        "question_text": "If 3x + 7 = 22, what is the value of x?",
        "options": ["3", "5", "7", "15"],
        "correct_answer": "B",
        "difficulty": 0.2,
        "discrimination": 1.0,
        "guessing": 0.25,
        "topic": "Algebra",
        "tags": ["linear-equations", "basic"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "What is the sum of the roots of the equation x² - 5x + 6 = 0?",
        "options": ["5", "6", "-5", "11"],
        "correct_answer": "A",
        "difficulty": 0.4,
        "discrimination": 1.2,
        "guessing": 0.20,
        "topic": "Algebra",
        "tags": ["quadratic-equations", "roots"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "If f(x) = 2x² - 3x + 1, what is f(3)?",
        "options": ["10", "8", "12", "6"],
        "correct_answer": "A",
        "difficulty": 0.3,
        "discrimination": 1.1,
        "guessing": 0.20,
        "topic": "Algebra",
        "tags": ["functions", "evaluation"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "Solve for x: |2x - 4| = 10",
        "options": ["x = 7 or x = -3", "x = 3 or x = 7", "x = -7 or x = 3", "x = 7 only"],
        "correct_answer": "A",
        "difficulty": 0.5,
        "discrimination": 1.5,
        "guessing": 0.15,
        "topic": "Algebra",
        "tags": ["absolute-value", "equations"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "If log₂(x) = 5, what is x?",
        "options": ["10", "25", "32", "64"],
        "correct_answer": "C",
        "difficulty": 0.6,
        "discrimination": 1.6,
        "guessing": 0.20,
        "topic": "Algebra",
        "tags": ["logarithms", "exponents"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "What is the value of ∑(k=1 to 4) k² ?",
        "options": ["20", "30", "10", "25"],
        "correct_answer": "B",
        "difficulty": 0.7,
        "discrimination": 1.8,
        "guessing": 0.15,
        "topic": "Algebra",
        "tags": ["summation", "series"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "If the geometric sequence starts with 3 and has a common ratio of 2, what is the 6th term?",
        "options": ["48", "64", "96", "192"],
        "correct_answer": "C",
        "difficulty": 0.8,
        "discrimination": 2.0,
        "guessing": 0.15,
        "topic": "Algebra",
        "tags": ["sequences", "geometric"],
        "created_at": datetime.utcnow()
    },

    # ─── Vocabulary ─────────────────────────────────────────────────
    {
        "question_text": "Select the word most similar in meaning to 'BENEVOLENT':",
        "options": ["Malicious", "Kind", "Indifferent", "Hostile"],
        "correct_answer": "B",
        "difficulty": 0.2,
        "discrimination": 1.0,
        "guessing": 0.25,
        "topic": "Vocabulary",
        "tags": ["synonyms", "basic"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "Choose the word that best completes: 'The professor's _____ lecture put half the class to sleep.'",
        "options": ["riveting", "soporific", "animated", "concise"],
        "correct_answer": "B",
        "difficulty": 0.4,
        "discrimination": 1.3,
        "guessing": 0.20,
        "topic": "Vocabulary",
        "tags": ["context-clues", "sentence-completion"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "PERSPICACIOUS most nearly means:",
        "options": ["Transparent", "Shrewd", "Persistent", "Sweaty"],
        "correct_answer": "B",
        "difficulty": 0.6,
        "discrimination": 1.5,
        "guessing": 0.15,
        "topic": "Vocabulary",
        "tags": ["definitions", "advanced"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "Select the antonym of 'LACONIC':",
        "options": ["Brief", "Verbose", "Terse", "Pithy"],
        "correct_answer": "B",
        "difficulty": 0.5,
        "discrimination": 1.4,
        "guessing": 0.20,
        "topic": "Vocabulary",
        "tags": ["antonyms", "intermediate"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "'OBSEQUIOUS' best describes someone who is:",
        "options": ["Rebellious", "Excessively compliant", "Highly intelligent", "Extremely lazy"],
        "correct_answer": "B",
        "difficulty": 0.7,
        "discrimination": 1.7,
        "guessing": 0.15,
        "topic": "Vocabulary",
        "tags": ["definitions", "advanced"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "The word 'SESQUIPEDALIAN' refers to:",
        "options": ["A type of dinosaur", "Having many sides", "Using long words", "Walking on tiptoes"],
        "correct_answer": "C",
        "difficulty": 0.9,
        "discrimination": 2.2,
        "guessing": 0.15,
        "topic": "Vocabulary",
        "tags": ["definitions", "expert"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "Choose the word that best completes: 'The diplomat's _____ response avoided committing to either side.'",
        "options": ["forthright", "equivocal", "unambiguous", "candid"],
        "correct_answer": "B",
        "difficulty": 0.6,
        "discrimination": 1.5,
        "guessing": 0.20,
        "topic": "Vocabulary",
        "tags": ["sentence-completion", "advanced"],
        "created_at": datetime.utcnow()
    },

    # ─── Reading Comprehension ──────────────────────────────────────
    {
        "question_text": "A passage states: 'The industrial revolution fundamentally altered the relationship between labor and capital.' The author's primary purpose is to:",
        "options": [
            "Criticize industrialization",
            "Describe a historical transformation",
            "Advocate for workers' rights",
            "Compare economic systems"
        ],
        "correct_answer": "B",
        "difficulty": 0.3,
        "discrimination": 1.1,
        "guessing": 0.25,
        "topic": "Reading Comprehension",
        "tags": ["main-idea", "basic"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "Based on the claim 'While correlation does not imply causation, the data strongly suggest a link between education spending and literacy rates,' the author would most likely agree that:",
        "options": [
            "Education spending directly causes higher literacy",
            "More research is needed to establish causation",
            "Literacy rates are independent of spending",
            "Correlation is sufficient for policy decisions"
        ],
        "correct_answer": "B",
        "difficulty": 0.5,
        "discrimination": 1.4,
        "guessing": 0.20,
        "topic": "Reading Comprehension",
        "tags": ["inference", "intermediate"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "In the sentence 'The scientist's iconoclastic theory challenged decades of established wisdom,' the word 'iconoclastic' most nearly means:",
        "options": [
            "Traditional",
            "Convention-breaking",
            "Well-supported",
            "Widely accepted"
        ],
        "correct_answer": "B",
        "difficulty": 0.6,
        "discrimination": 1.5,
        "guessing": 0.15,
        "topic": "Reading Comprehension",
        "tags": ["vocabulary-in-context", "intermediate"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "A passage argues that biodiversity loss accelerates climate change. Which evidence would MOST WEAKEN this argument?",
        "options": [
            "Regions with high biodiversity also have high carbon absorption",
            "Climate change has occurred during periods of stable biodiversity",
            "Deforestation contributes to carbon emissions",
            "Species extinction rates are increasing globally"
        ],
        "correct_answer": "B",
        "difficulty": 0.8,
        "discrimination": 2.0,
        "guessing": 0.10,
        "topic": "Reading Comprehension",
        "tags": ["critical-reasoning", "advanced"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "The author uses the phrase 'a Pyrrhic victory' to suggest that:",
        "options": [
            "The victory was easily achieved",
            "The cost of winning outweighed the benefits",
            "The victory was unexpected",
            "The battle was insignificant"
        ],
        "correct_answer": "B",
        "difficulty": 0.5,
        "discrimination": 1.3,
        "guessing": 0.20,
        "topic": "Reading Comprehension",
        "tags": ["rhetorical-analysis", "intermediate"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "If the passage states 'The Renaissance was not a sudden rupture but a gradual evolution,' the author's tone can best be described as:",
        "options": [
            "Dismissive and critical",
            "Nuanced and corrective",
            "Enthusiastic and celebratory",
            "Neutral and detached"
        ],
        "correct_answer": "B",
        "difficulty": 0.7,
        "discrimination": 1.6,
        "guessing": 0.15,
        "topic": "Reading Comprehension",
        "tags": ["tone", "advanced"],
        "created_at": datetime.utcnow()
    },
    {
        "question_text": "A paragraph discusses how 'urban sprawl has led to increased commute times, energy consumption, and social isolation.' The organizational pattern used is:",
        "options": [
            "Chronological order",
            "Cause and effect",
            "Compare and contrast",
            "Problem and solution"
        ],
        "correct_answer": "B",
        "difficulty": 0.4,
        "discrimination": 1.2,
        "guessing": 0.25,
        "topic": "Reading Comprehension",
        "tags": ["text-structure", "basic"],
        "created_at": datetime.utcnow()
    },
]


async def seed():
    """Seed the questions collection with GRE-style questions."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]

    # Check if already seeded
    count = await db.questions.count_documents({})
    if count > 0:
        print(f"⚠️  Questions collection already has {count} documents. Skipping seed.")
        print("   To re-seed, drop the collection first: db.questions.drop()")
        client.close()
        return

    result = await db.questions.insert_many(GRE_QUESTIONS)
    print(f"✅ Seeded {len(result.inserted_ids)} GRE-style questions into '{settings.DATABASE_NAME}.questions'")
    print(f"   Topics: Algebra ({sum(1 for q in GRE_QUESTIONS if q['topic'] == 'Algebra')}), "
          f"Vocabulary ({sum(1 for q in GRE_QUESTIONS if q['topic'] == 'Vocabulary')}), "
          f"Reading Comprehension ({sum(1 for q in GRE_QUESTIONS if q['topic'] == 'Reading Comprehension')})")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
