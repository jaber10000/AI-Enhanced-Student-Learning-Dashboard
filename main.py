from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import random

app = FastAPI(title="Personalized Learning Path Platform")

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "student-scores.csv")
df = pd.read_csv(CSV_PATH)

# Compute average if not already in CSV
if 'average_score' not in df.columns:
    df['average_score'] = df[[s for s in df.columns if s.endswith('_score')]].mean(axis=1)


subjects = [
    'math_score','history_score','physics_score',
    'chemistry_score','biology_score','english_score','geography_score'
]

# Sample learning resources database
LEARNING_RESOURCES = {
    'math': [
        {'title': 'Algebra Basics', 'type': 'video', 'difficulty': 'easy', 'url': '#', 'duration': '15 min'},
        {'title': 'Calculus Fundamentals', 'type': 'article', 'difficulty': 'medium', 'url': '#', 'duration': '20 min'},
        {'title': 'Advanced Geometry', 'type': 'interactive', 'difficulty': 'hard', 'url': '#', 'duration': '30 min'},
    ],
    'physics': [
        {'title': 'Newton\'s Laws', 'type': 'video', 'difficulty': 'easy', 'url': '#', 'duration': '12 min'},
        {'title': 'Thermodynamics', 'type': 'article', 'difficulty': 'medium', 'url': '#', 'duration': '25 min'},
        {'title': 'Quantum Mechanics', 'type': 'pdf', 'difficulty': 'hard', 'url': '#', 'duration': '45 min'},
    ],
    'chemistry': [
        {'title': 'Periodic Table', 'type': 'video', 'difficulty': 'easy', 'url': '#', 'duration': '10 min'},
        {'title': 'Chemical Bonding', 'type': 'interactive', 'difficulty': 'medium', 'url': '#', 'duration': '20 min'},
        {'title': 'Organic Chemistry', 'type': 'pdf', 'difficulty': 'hard', 'url': '#', 'duration': '40 min'},
    ],
}

# Badge system
BADGES = {
    'first_steps': {'name': 'First Steps', 'description': 'Complete your first task', 'icon': '🎯', 'xp': 50},
    'quick_learner': {'name': 'Quick Learner', 'description': 'Complete 5 tasks in a day', 'icon': '⚡', 'xp': 100},
    'math_master': {'name': 'Math Master', 'description': 'Score above 85 in Math', 'icon': '🧮', 'xp': 150},
    'streak_7': {'name': '7 Day Streak', 'description': 'Study for 7 consecutive days', 'icon': '🔥', 'xp': 200},
    'top_scorer': {'name': 'Top Scorer', 'description': 'Rank in top 10', 'icon': '👑', 'xp': 300},
}

# --- Helper Functions ---
def get_student(student_id: int):
    matches = df[df['id'] == student_id]
    return matches.iloc[0] if not matches.empty else None

def safe_average(student):
    scores = {subj: int(student[subj]) if subj in student and not pd.isna(student[subj]) else 0 for subj in subjects}
    avg = float(student['average_score']) if 'average_score' in student and not pd.isna(student['average_score']) else sum(scores.values())/len(subjects)
    return avg, scores

def top_strengths_weaknesses(scores):
    sorted_scores = dict(sorted(scores.items(), key=lambda x:x[1], reverse=True))
    strongest = dict(list(sorted_scores.items())[:3])
    weakest = dict(list(sorted_scores.items())[-3:])
    return strongest, weakest

def generate_recommendations(scores):
    recs = {}
    for subj, score in scores.items():
        if score < 60:
            recs[subj] = f"Focus on {subj.replace('_score','').replace('_',' ').title()} basics. Start with fundamentals."
        elif score < 75:
            recs[subj] = f"Practice {subj.replace('_score','').replace('_',' ').title()} regularly. Aim for intermediate level."
        elif score < 90:
            recs[subj] = f"Enhance {subj.replace('_score','').replace('_',' ').title()} with advanced concepts."
        else:
            recs[subj] = f"{subj.replace('_score','').replace('_',' ').title()} is excellent! Challenge yourself with expert problems."
    return recs

def get_learning_resources(subject, difficulty='easy'):
    """Get recommended resources based on subject and difficulty"""
    subject_key = subject.replace('_score', '').lower()
    if subject_key in LEARNING_RESOURCES:
        resources = LEARNING_RESOURCES[subject_key]
        return [r for r in resources if r['difficulty'] == difficulty] or resources[:2]
    return []

def calculate_xp(scores):
    """Calculate XP based on performance"""
    avg_score = sum(scores.values()) / len(scores)
    base_xp = int(avg_score * 10)
    return base_xp

def get_leaderboard_rank(student_id):
    """Calculate student's rank based on average score"""
    df_sorted = df.sort_values('average_score', ascending=False).reset_index(drop=True)
    try:
        rank = df_sorted[df_sorted['id'] == student_id].index[0] + 1
        total_students = len(df_sorted)
        return rank, total_students
    except:
        return None, len(df)

def badge_color(score):
    if score < 60:
        return 'red'
    elif score < 85:
        return 'yellow'
    else:
        return 'green'

def predicted_improvement(score):
    if score < 60:
        return min(score + 10, 100)
    elif score < 85:
        return min(score + 5, 100)
    else:
        return min(score + 2, 100)

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Personalized Learning Platform</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            @keyframes gradient {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            .gradient-bg {
                background: linear-gradient(-45deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
                background-size: 400% 400%;
                animation: gradient 15s ease infinite;
            }
        </style>
    </head>
    <body class="gradient-bg min-h-screen flex flex-col items-center justify-center p-5">
        <div class="bg-white/95 backdrop-blur shadow-2xl rounded-2xl p-10 w-full max-w-lg">
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600 mb-3">
                    🎓 Personalized Learning Path
                </h1>
                <p class="text-gray-600 text-lg">Your AI-Powered Education Partner</p>
            </div>
            
            <form action="/search" method="post" class="flex flex-col gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Student ID</label>
                    <input type="number" name="student_id" placeholder="Enter your Student ID" required
                           class="w-full border-2 border-purple-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition">
                </div>
                <button type="submit" class="bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg hover:shadow-lg transform hover:-translate-y-0.5 transition font-semibold text-lg">
                    🚀 Start Learning Journey
                </button>
            </form>
            
            <div class="mt-6 p-4 bg-blue-50 rounded-lg">
                <h3 class="font-semibold text-blue-900 mb-2">✨ Platform Features:</h3>
                <ul class="text-sm text-blue-800 space-y-1">
                    <li>• AI-Powered Learning Recommendations</li>
                    <li>• Personalized Study Plans</li>
                    <li>• Gamification & Achievements</li>
                    <li>• Real-time Progress Tracking</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

@app.post("/search", response_class=HTMLResponse)
def search(student_id: int = Form(...)):
    student = get_student(student_id)
    if student is None:
        return f"""
        <html><body class="bg-gradient-to-br from-red-100 to-red-200 flex items-center justify-center min-h-screen">
            <div class="bg-white p-10 rounded-2xl shadow-2xl text-center max-w-md">
                <div class="text-6xl mb-4">❌</div>
                <h2 class="text-3xl font-bold text-red-600 mb-4">Student Not Found</h2>
                <p class="text-gray-600 mb-6">Student ID {student_id} doesn't exist in our database.</p>
                <a href="/" class="inline-block bg-gradient-to-r from-red-500 to-pink-500 text-white px-6 py-3 rounded-lg hover:shadow-lg transition">
                    ← Go Back
                </a>
            </div>
        </body></html>
        """

    avg_score, scores = safe_average(student)
    strongest, weakest = top_strengths_weaknesses(scores)
    recs = generate_recommendations(scores)
    predicted_scores = {k: predicted_improvement(v) for k,v in scores.items()}
    
    # XP and Rank
    xp = calculate_xp(scores)
    rank, total_students = get_leaderboard_rank(student_id)
    
    # Class averages
    class_avg = {subj: round(df[subj].mean(),2) for subj in subjects}
    
    bar_colors = ['rgba(34,197,94,0.7)' if s in strongest else 'rgba(239,68,68,0.7)' if s in weakest else 'rgba(107,114,128,0.6)' for s in subjects]

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - {student['first_name']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-50 to-purple-50 min-h-screen">
        <!-- Navigation -->
        <nav class="bg-white shadow-lg border-b-4 border-purple-500">
            <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                <h1 class="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600">
                    🎓 Learning Dashboard
                </h1>
                <div class="flex gap-4 items-center">
                    <div class="text-right">
                        <p class="text-sm text-gray-600">Welcome back,</p>
                        <p class="font-bold text-purple-600">{student['first_name']} {student['last_name']}</p>
                    </div>
                    <div class="bg-gradient-to-r from-yellow-400 to-orange-400 text-white px-4 py-2 rounded-lg font-bold">
                        ⚡ {xp} XP
                    </div>
                </div>
            </div>
        </nav>

        <div class="max-w-7xl mx-auto p-6">
            <!-- Quick Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <div class="bg-gradient-to-br from-purple-500 to-purple-700 text-white p-6 rounded-xl shadow-lg">
                    <div class="text-3xl mb-2">📊</div>
                    <div class="text-3xl font-bold">{round(avg_score,1)}%</div>
                    <div class="text-purple-200">Overall Average</div>
                </div>
                
                <div class="bg-gradient-to-br from-blue-500 to-blue-700 text-white p-6 rounded-xl shadow-lg">
                    <div class="text-3xl mb-2">🏆</div>
                    <div class="text-3xl font-bold">#{rank}</div>
                    <div class="text-blue-200">Class Rank</div>
                </div>
                
                <div class="bg-gradient-to-br from-green-500 to-green-700 text-white p-6 rounded-xl shadow-lg">
                    <div class="text-3xl mb-2">💪</div>
                    <div class="text-2xl font-bold">{list(strongest.keys())[0].replace('_score','').title()}</div>
                    <div class="text-green-200">Top Strength</div>
                </div>
                
                <div class="bg-gradient-to-br from-orange-500 to-red-500 text-white p-6 rounded-xl shadow-lg">
                    <div class="text-3xl mb-2">🎯</div>
                    <div class="text-2xl font-bold">{list(weakest.keys())[0].replace('_score','').title()}</div>
                    <div class="text-orange-200">Focus Area</div>
                </div>
            </div>

            <!-- Main Content Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Left Column: Charts and Analysis -->
                <div class="lg:col-span-2 space-y-6">
                    <!-- Performance Chart -->
                    <div class="bg-white p-6 rounded-xl shadow-lg">
                        <h2 class="text-2xl font-bold text-gray-800 mb-4">📈 Performance Analysis</h2>
                        <canvas id="scoreChart" height="100"></canvas>
                    </div>

                    <!-- Strengths & Weaknesses -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl shadow-lg border-2 border-green-300">
                            <h2 class="text-xl font-bold text-green-800 mb-4 flex items-center gap-2">
                                <span class="text-2xl">💪</span> Top 3 Strengths
                            </h2>
                            <ul class="space-y-3">
                                {"".join(f'''<li class="bg-white p-3 rounded-lg shadow">
                                    <div class="font-bold text-green-700">{k.replace('_score','').replace('_',' ').title()}</div>
                                    <div class="text-sm text-gray-600">{v}% - {recs[k]}</div>
                                </li>''' for k,v in strongest.items())}
                            </ul>
                        </div>
                        
                        <div class="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-xl shadow-lg border-2 border-red-300">
                            <h2 class="text-xl font-bold text-red-800 mb-4 flex items-center gap-2">
                                <span class="text-2xl">🎯</span> Areas to Improve
                            </h2>
                            <ul class="space-y-3">
                                {"".join(f'''<li class="bg-white p-3 rounded-lg shadow">
                                    <div class="font-bold text-red-700">{k.replace('_score','').replace('_',' ').title()}</div>
                                    <div class="text-sm text-gray-600">{v}% - {recs[k]}</div>
                                </li>''' for k,v in weakest.items())}
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Right Column: Actions and Resources -->
                <div class="space-y-6">
                    <!-- Quick Actions -->
                    <div class="bg-white p-6 rounded-xl shadow-lg">
                        <h2 class="text-xl font-bold text-gray-800 mb-4">🚀 Quick Actions</h2>
                        <div class="space-y-3">
                            <a href="/learning-path/{student_id}" class="block bg-gradient-to-r from-purple-500 to-purple-700 text-white px-4 py-3 rounded-lg hover:shadow-lg transition text-center font-semibold">
                                📚 View Learning Path
                            </a>
                            <a href="/todo/{student_id}" class="block bg-gradient-to-r from-green-500 to-green-700 text-white px-4 py-3 rounded-lg hover:shadow-lg transition text-center font-semibold">
                                ✅ My To-Do List
                            </a>
                            <a href="/quiz/{student_id}" class="block bg-gradient-to-r from-blue-500 to-blue-700 text-white px-4 py-3 rounded-lg hover:shadow-lg transition text-center font-semibold">
                                🎯 Take Quiz
                            </a>
                            <a href="/achievements/{student_id}" class="block bg-gradient-to-r from-yellow-500 to-orange-500 text-white px-4 py-3 rounded-lg hover:shadow-lg transition text-center font-semibold">
                                🏆 Achievements
                            </a>
                            <a href="/leaderboard" class="block bg-gradient-to-r from-pink-500 to-red-500 text-white px-4 py-3 rounded-lg hover:shadow-lg transition text-center font-semibold">
                                👑 Leaderboard
                            </a>
                        </div>
                    </div>

                    <!-- Recent Badges -->
                    <div class="bg-white p-6 rounded-xl shadow-lg">
                        <h2 class="text-xl font-bold text-gray-800 mb-4">🏅 Recent Badges</h2>
                        <div class="grid grid-cols-2 gap-3">
                            <div class="bg-gradient-to-br from-yellow-100 to-yellow-200 p-3 rounded-lg text-center">
                                <div class="text-3xl mb-1">🎯</div>
                                <div class="text-xs font-semibold">First Steps</div>
                            </div>
                            <div class="bg-gradient-to-br from-blue-100 to-blue-200 p-3 rounded-lg text-center">
                                <div class="text-3xl mb-1">⚡</div>
                                <div class="text-xs font-semibold">Quick Learner</div>
                            </div>
                        </div>
                    </div>

                    <!-- Study Streak -->
                    <div class="bg-gradient-to-br from-orange-100 to-red-100 p-6 rounded-xl shadow-lg border-2 border-orange-300">
                        <h2 class="text-xl font-bold text-orange-800 mb-3 flex items-center gap-2">
                            <span class="text-2xl">🔥</span> Study Streak
                        </h2>
                        <div class="text-4xl font-bold text-orange-600 mb-2">5 Days</div>
                        <div class="text-sm text-gray-600">Keep it up! 2 more days to unlock the 7-day badge!</div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const ctx = document.getElementById('scoreChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps([s.replace('_score','').replace('_',' ').title() for s in subjects])},
                    datasets: [
                        {{
                            label: 'Your Score',
                            data: {json.dumps(list(scores.values()))},
                            backgroundColor: {json.dumps(bar_colors)},
                            borderRadius: 8,
                        }},
                        {{
                            label: 'Predicted Score',
                            data: {json.dumps(list(predicted_scores.values()))},
                            backgroundColor: 'rgba(147,51,234,0.5)',
                            borderRadius: 8,
                        }},
                        {{
                            label: 'Class Average',
                            data: {json.dumps(list(class_avg.values()))},
                            backgroundColor: 'rgba(156,163,175,0.5)',
                            borderRadius: 8,
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100,
                            ticks: {{
                                callback: function(value) {{
                                    return value + '%';
                                }}
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{
                            position: 'top',
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return context.dataset.label + ': ' + context.parsed.y + '%';
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

# Continue in next artifact for remaining routes...



# Complete the learning-path route and add remaining routes to app.py

@app.get("/learning-path/{student_id}", response_class=HTMLResponse)
def learning_path(student_id: int):
    student = get_student(student_id)
    if student is None:
        return f"<h2>Student not found</h2><a href='/'>Go Back</a>"
    
    avg_score, scores = safe_average(student)
    strongest, weakest = top_strengths_weaknesses(scores)
    
    # Generate learning path based on weakest subjects
    learning_paths = []
    for subj, score in weakest.items():
        subj_name = subj.replace('_score', '')
        difficulty = 'easy' if score < 60 else 'medium' if score < 75 else 'hard'
        resources = get_learning_resources(subj, difficulty)
        
        learning_paths.append({
            'subject': subj_name.replace('_', ' ').title(),
            'current_score': score,
            'target_score': min(score + 15, 100),
            'difficulty': difficulty,
            'resources': resources,
            'status': 'locked' if score < 50 else 'in_progress' if score < 80 else 'completed'
        })
    
    # Generate resource cards HTML
    resource_cards = []
    for path in learning_paths:
        resources_html = ""
        for res in path['resources']:
            icon = '📹' if res['type'] == 'video' else '📄' if res['type'] == 'article' else '🎮' if res['type'] == 'interactive' else '📑'
            resources_html += f'''
            <div class="bg-gradient-to-br from-blue-50 to-purple-50 p-4 rounded-lg border border-blue-200 hover:shadow-md transition">
                <div class="flex items-center gap-2 mb-2">
                    <span class="text-2xl">{icon}</span>
                    <span class="text-xs font-semibold text-purple-600 uppercase">{res['type']}</span>
                </div>
                <h4 class="font-bold text-gray-800 mb-1">{res['title']}</h4>
                <div class="flex justify-between items-center text-xs text-gray-600">
                    <span>⏱️ {res['duration']}</span>
                    <a href="{res['url']}" class="bg-purple-500 text-white px-3 py-1 rounded hover:bg-purple-600 transition">
                        Start →
                    </a>
                </div>
            </div>
            '''
        
        status_color = 'border-red-500' if path['status'] == 'locked' else 'border-yellow-500' if path['status'] == 'in_progress' else 'border-green-500'
        status_badge = '🔒 Locked' if path['status'] == 'locked' else '⏳ In Progress' if path['status'] == 'in_progress' else '✅ Completed'
        status_bg = 'bg-red-100 text-red-700' if path['status'] == 'locked' else 'bg-yellow-100 text-yellow-700' if path['status'] == 'in_progress' else 'bg-green-100 text-green-700'
        icon = '🔒' if path['status'] == 'locked' else '📚' if path['status'] == 'in_progress' else '🎓'
        progress = min(int((path['current_score']/path['target_score'])*100), 100)
        
        resource_cards.append(f'''
        <div class="bg-white rounded-xl shadow-lg p-6 border-l-4 {status_color}">
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <div class="flex items-center gap-3 mb-2">
                        <h2 class="text-2xl font-bold text-gray-800">{path['subject']}</h2>
                        <span class="px-3 py-1 rounded-full text-sm font-semibold {status_bg}">
                            {status_badge}
                        </span>
                    </div>
                    <div class="flex items-center gap-4 text-sm text-gray-600">
                        <span>Current: <strong class="text-purple-600">{path['current_score']}%</strong></span>
                        <span>→</span>
                        <span>Target: <strong class="text-green-600">{path['target_score']}%</strong></span>
                        <span class="ml-4 bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-semibold">
                            {path['difficulty'].title()} Level
                        </span>
                    </div>
                </div>
                <div class="text-5xl">{icon}</div>
            </div>

            <!-- Progress Bar -->
            <div class="mb-6">
                <div class="flex justify-between text-sm text-gray-600 mb-2">
                    <span>Progress to Target</span>
                    <span>{progress}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-3">
                    <div class="bg-gradient-to-r from-purple-500 to-blue-500 h-3 rounded-full transition-all duration-1000" 
                         style="width: {progress}%"></div>
                </div>
            </div>

            <!-- Recommended Resources -->
            <div>
                <h3 class="font-semibold text-gray-800 mb-3">📖 Recommended Learning Resources:</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {resources_html}
                </div>
            </div>
        </div>
        ''')
    
    first_name = student['first_name']
    cards_html = ''.join(resource_cards)
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Learning Path - {first_name}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-purple-50 to-blue-50 min-h-screen p-6">
        <div class="max-w-6xl mx-auto">
            <!-- Header -->
            <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600">
                            🗺️ Your Personalized Learning Path
                        </h1>
                        <p class="text-gray-600 mt-2">Curated recommendations based on your performance</p>
                    </div>
                    <form method="post" action="/search" style="display:inline;">
                        <input type="hidden" name="student_id" value="{student_id}">
                        <button type="submit" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition">
                            ← Back to Dashboard
                        </button>
                    </form>
                </div>
            </div>

            <!-- Learning Path Roadmap -->
            <div class="space-y-6">
                {cards_html}
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/todo/{student_id}", response_class=HTMLResponse)
def todo_list(student_id: int):
    student = get_student(student_id)
    if student is None:
        return f"<h2>Student not found</h2><a href='/'>Go Back</a>"
    
    avg_score, scores = safe_average(student)
    strongest, weakest = top_strengths_weaknesses(scores)
    
    # Generate daily tasks based on weak subjects
    tasks = []
    for subj, score in weakest.items():
        subj_name = subj.replace('_score', '').replace('_', ' ').title()
        if score < 60:
            tasks.append({
                'title': f'Complete {subj_name} fundamentals module',
                'priority': 'high',
                'duration': '30 min',
                'xp': 50
            })
        elif score < 75:
            tasks.append({
                'title': f'Practice {subj_name} intermediate problems',
                'priority': 'medium',
                'duration': '25 min',
                'xp': 40
            })
        else:
            tasks.append({
                'title': f'Challenge yourself with advanced {subj_name}',
                'priority': 'low',
                'duration': '20 min',
                'xp': 30
            })
    
    # Add general tasks
    tasks.extend([
        {'title': 'Review yesterday\'s notes', 'priority': 'medium', 'duration': '15 min', 'xp': 25},
        {'title': 'Complete daily quiz', 'priority': 'high', 'duration': '10 min', 'xp': 35},
    ])
    
    task_html = ""
    for i, task in enumerate(tasks):
        priority_color = 'from-red-500 to-red-600' if task['priority'] == 'high' else 'from-yellow-500 to-yellow-600' if task['priority'] == 'medium' else 'from-green-500 to-green-600'
        priority_badge = 'bg-red-100 text-red-700' if task['priority'] == 'high' else 'bg-yellow-100 text-yellow-700' if task['priority'] == 'medium' else 'bg-green-100 text-green-700'
        priority_text = task['priority'].upper()
        
        task_html += f'''
        <div class="bg-white p-5 rounded-xl shadow-md border-l-4 border-purple-500 hover:shadow-lg transition">
            <div class="flex items-center gap-3">
                <input type="checkbox" id="task{i}" class="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500">
                <label for="task{i}" class="flex-1 cursor-pointer">
                    <div class="font-semibold text-gray-800">{task['title']}</div>
                    <div class="flex gap-3 mt-1 text-sm text-gray-600">
                        <span class="px-2 py-0.5 rounded {priority_badge} font-medium">
                            {priority_text}
                        </span>
                        <span>⏱️ {task['duration']}</span>
                        <span>⚡ +{task['xp']} XP</span>
                    </div>
                </label>
            </div>
        </div>
        '''
    
    first_name = student['first_name']
    total_tasks = len(tasks)
    total_xp = sum(t['xp'] for t in tasks)
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>To-Do List - {first_name}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-50 to-purple-50 min-h-screen p-6">
        <div class="max-w-4xl mx-auto">
            <!-- Header -->
            <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600">
                            ✅ Daily Learning Tasks
                        </h1>
                        <p class="text-gray-600 mt-2">Stay on track with your personalized study plan</p>
                    </div>
                    <form method="post" action="/search" style="display:inline;">
                        <input type="hidden" name="student_id" value="{student_id}">
                        <button type="submit" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition">
                            ← Dashboard
                        </button>
                    </form>
                </div>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-3 gap-4 mb-6">
                <div class="bg-gradient-to-br from-purple-500 to-purple-700 text-white p-4 rounded-xl text-center">
                    <div class="text-3xl font-bold">{total_tasks}</div>
                    <div class="text-sm">Total Tasks</div>
                </div>
                <div class="bg-gradient-to-br from-green-500 to-green-700 text-white p-4 rounded-xl text-center">
                    <div class="text-3xl font-bold">0</div>
                    <div class="text-sm">Completed</div>
                </div>
                <div class="bg-gradient-to-br from-yellow-500 to-orange-500 text-white p-4 rounded-xl text-center">
                    <div class="text-3xl font-bold">{total_xp}</div>
                    <div class="text-sm">Total XP</div>
                </div>
            </div>

            <!-- Tasks -->
            <div class="space-y-4">
                {task_html}
            </div>
        </div>

        <script>
            document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {{
                checkbox.addEventListener('change', function() {{
                    if(this.checked) {{
                        this.parentElement.parentElement.style.opacity = '0.6';
                        this.parentElement.querySelector('label > div').style.textDecoration = 'line-through';
                    }} else {{
                        this.parentElement.parentElement.style.opacity = '1';
                        this.parentElement.querySelector('label > div').style.textDecoration = 'none';
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """


@app.get("/achievements/{student_id}", response_class=HTMLResponse)
def achievements(student_id: int):
    student = get_student(student_id)
    if student is None:
        return f"<h2>Student not found</h2><a href='/'>Go Back</a>"
    
    avg_score, scores = safe_average(student)
    xp = calculate_xp(scores)
    rank, total = get_leaderboard_rank(student_id)
    
    # Determine unlocked badges
    unlocked = []
    locked = []
    
    for badge_id, badge in BADGES.items():
        is_unlocked = False
        if badge_id == 'first_steps':
            is_unlocked = True
        elif badge_id == 'quick_learner':
            is_unlocked = True
        elif badge_id == 'math_master' and scores.get('math_score', 0) > 85:
            is_unlocked = True
        elif badge_id == 'top_scorer' and rank and rank <= 10:
            is_unlocked = True
        
        if is_unlocked:
            unlocked.append(badge)
        else:
            locked.append(badge)
    
    unlocked_html = ""
    for badge in unlocked:
        unlocked_html += f'''
        <div class="bg-gradient-to-br from-yellow-100 to-yellow-200 p-6 rounded-xl shadow-lg border-2 border-yellow-400 transform hover:scale-105 transition">
            <div class="text-6xl mb-3 text-center">{badge['icon']}</div>
            <h3 class="font-bold text-lg text-gray-800 text-center mb-1">{badge['name']}</h3>
            <p class="text-sm text-gray-600 text-center mb-3">{badge['description']}</p>
            <div class="text-center">
                <span class="bg-yellow-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                    +{badge['xp']} XP
                </span>
            </div>
        </div>
        '''
    
    locked_html = ""
    for badge in locked:
        locked_html += f'''
        <div class="bg-gray-100 p-6 rounded-xl shadow-md border-2 border-gray-300 opacity-60">
            <div class="text-6xl mb-3 text-center grayscale">🔒</div>
            <h3 class="font-bold text-lg text-gray-600 text-center mb-1">{badge['name']}</h3>
            <p class="text-sm text-gray-500 text-center mb-3">{badge['description']}</p>
            <div class="text-center">
                <span class="bg-gray-400 text-white px-3 py-1 rounded-full text-sm font-bold">
                    +{badge['xp']} XP
                </span>
            </div>
        </div>
        '''
    
    first_name = student['first_name']
    unlocked_count = len(unlocked)
    total_badges = len(BADGES)
    completion_rate = int((unlocked_count/total_badges)*100)
    unlocked_content = unlocked_html if unlocked_html else '<p class="text-gray-500 col-span-full text-center p-8">No badges unlocked yet. Start learning to earn your first badge!</p>'
    locked_content = locked_html if locked_html else '<p class="text-gray-500 col-span-full text-center p-8">You have unlocked all badges! 🎉</p>'
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Achievements - {first_name}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-yellow-50 to-orange-50 min-h-screen p-6">
        <div class="max-w-6xl mx-auto">
            <!-- Header -->
            <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-600 to-orange-600">
                            🏆 Your Achievements
                        </h1>
                        <p class="text-gray-600 mt-2">Unlock badges and earn XP by completing challenges</p>
                    </div>
                    <form method="post" action="/search" style="display:inline;">
                        <input type="hidden" name="student_id" value="{student_id}">
                        <button type="submit" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition">
                            ← Dashboard
                        </button>
                    </form>
                </div>
            </div>

            <!-- Progress Stats -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-gradient-to-br from-purple-500 to-purple-700 text-white p-6 rounded-xl shadow-lg text-center">
                    <div class="text-4xl mb-2">⚡</div>
                    <div class="text-3xl font-bold">{xp}</div>
                    <div class="text-purple-200">Total XP</div>
                </div>
                <div class="bg-gradient-to-br from-yellow-500 to-orange-500 text-white p-6 rounded-xl shadow-lg text-center">
                    <div class="text-4xl mb-2">🏅</div>
                    <div class="text-3xl font-bold">{unlocked_count}/{total_badges}</div>
                    <div class="text-yellow-200">Badges Unlocked</div>
                </div>
                <div class="bg-gradient-to-br from-blue-500 to-blue-700 text-white p-6 rounded-xl shadow-lg text-center">
                    <div class="text-4xl mb-2">📊</div>
                    <div class="text-3xl font-bold">{completion_rate}%</div>
                    <div class="text-blue-200">Completion Rate</div>
                </div>
            </div>

            <!-- Unlocked Badges -->
            <div class="mb-8">
                <h2 class="text-2xl font-bold text-gray-800 mb-4">✨ Unlocked Badges</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {unlocked_content}
                </div>
            </div>

            <!-- Locked Badges -->
            <div>
                <h2 class="text-2xl font-bold text-gray-800 mb-4">🔒 Locked Badges</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {locked_content}
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/leaderboard", response_class=HTMLResponse)
def leaderboard():
    top_students = df.nlargest(10, 'average_score')[['id', 'first_name', 'last_name', 'average_score']]
    
    leaderboard_html = ""
    for idx, row in top_students.iterrows():
        rank = top_students.index.get_loc(idx) + 1
        medal = '🥇' if rank == 1 else '🥈' if rank == 2 else '🥉' if rank == 3 else f'#{rank}'
        bg_color = 'from-yellow-100 to-yellow-200 border-yellow-400' if rank == 1 else 'from-gray-100 to-gray-200 border-gray-400' if rank == 2 else 'from-orange-100 to-orange-200 border-orange-400' if rank == 3 else 'from-blue-50 to-blue-100 border-blue-300'
        
        leaderboard_html += f'''
        <div class="bg-gradient-to-r {bg_color} p-5 rounded-xl shadow-md border-2 hover:shadow-lg transition">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <div class="text-4xl font-bold">{medal}</div>
                    <div>
                        <div class="font-bold text-lg text-gray-800">{row['first_name']} {row['last_name']}</div>
                        <div class="text-sm text-gray-600">Student ID: {row['id']}</div>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-3xl font-bold text-purple-600">{round(row['average_score'], 1)}%</div>
                    <div class="text-sm text-gray-600">Average Score</div>
                </div>
            </div>
        </div>
        '''
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Leaderboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-purple-50 to-pink-50 min-h-screen p-6">
        <div class="max-w-4xl mx-auto">
            <!-- Header -->
            <div class="bg-white rounded-xl shadow-lg p-6 mb-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">
                            👑 Top Performers Leaderboard
                        </h1>
                        <p class="text-gray-600 mt-2">See how you rank among your peers</p>
                    </div>
                    <a href="/" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition">
                        ← Home
                    </a>
                </div>
            </div>

            <!-- Leaderboard -->
            <div class="space-y-4">
                {leaderboard_html}
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/quiz/{student_id}", response_class=HTMLResponse)
def quiz(student_id: int):
    student = get_student(student_id)
    if student is None:
        return f"<h2>Student not found</h2><a href='/'>Go Back</a>"
    
    first_name = student['first_name']
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Quiz - {first_name}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-green-50 to-blue-50 min-h-screen p-6">
        <div class="max-w-3xl mx-auto">
            <div class="bg-white rounded-xl shadow-lg p-8">
                <div class="text-center mb-8">
                    <h1 class="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-blue-600 mb-2">
                        🎯 Daily Challenge Quiz
                    </h1>
                    <p class="text-gray-600">Test your knowledge and earn XP!</p>
                </div>

                <div class="bg-gradient-to-r from-blue-100 to-purple-100 p-6 rounded-xl text-center mb-8">
                    <div class="text-6xl mb-4">🚧</div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">Coming Soon!</h2>
                    <p class="text-gray-600">Interactive quizzes are being prepared for you.</p>
                    <p class="text-sm text-gray-500 mt-2">Stay tuned for personalized assessments based on your learning path.</p>
                </div>

                <form method="post" action="/search" class="text-center">
                    <input type="hidden" name="student_id" value="{student_id}">
                    <button type="submit" class="bg-gradient-to-r from-purple-500 to-blue-500 text-white px-6 py-3 rounded-lg hover:shadow-lg transition font-semibold">
                        ← Back to Dashboard
                    </button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """