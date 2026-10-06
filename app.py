from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os
from datetime import datetime

# Optional AI support
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

app = Flask(__name__)

DATABASE = "events.db"

# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            category TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            registered INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    """)

    conn.commit()

    # Add sample events if database is empty
    count = conn.execute(
        "SELECT COUNT(*) FROM events"
    ).fetchone()[0]

    if count == 0:
        sample_events = [
            (
                "AI & Machine Learning Workshop",
                "Learn the fundamentals of AI and Machine Learning.",
                "2026-11-15 10:00",
                "Hyderabad",
                "Technology",
                100
            ),
            (
                "Web Development Bootcamp",
                "Learn HTML, CSS, JavaScript and modern web development.",
                "2026-11-20 09:30",
                "Bangalore",
                "Technology",
                80
            ),
            (
                "Business Startup Meetup",
                "Meet entrepreneurs and learn how to build a startup.",
                "2026-12-01 11:00",
                "Mumbai",
                "Business",
                150
            )
        ]

        conn.executemany("""
            INSERT INTO events
            (title, description, date, location, category, capacity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, sample_events)

        conn.commit()

    conn.close()


# ============================================================
# HOME PAGE
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>AI Event Management System</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: #f4f7fb;
    color: #1e293b;
}

/* NAVBAR */

nav {
    background: #111827;
    color: white;
    padding: 18px 7%;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

nav h2 {
    margin: 0;
    color: #818cf8;
}

nav span {
    color: #cbd5e1;
}

/* HERO */

.hero {
    background:
        linear-gradient(
            135deg,
            rgba(79,70,229,.95),
            rgba(124,58,237,.95)
        );

    color: white;
    text-align: center;
    padding: 70px 20px;
}

.hero h1 {
    font-size: 45px;
    margin-bottom: 15px;
}

.hero p {
    font-size: 19px;
}

/* CONTAINER */

.container {
    width: 90%;
    max-width: 1200px;
    margin: 35px auto;
}

/* CARDS */

.card {
    background: white;
    padding: 25px;
    border-radius: 15px;
    margin-bottom: 30px;

    box-shadow:
        0 8px 25px rgba(0,0,0,.08);
}

.card h2 {
    color: #4f46e5;
    margin-top: 0;
}

/* EVENT GRID */

.event-grid {
    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(280px, 1fr));

    gap: 20px;
}

.event-card {
    border: 1px solid #e2e8f0;

    border-radius: 12px;

    padding: 20px;

    transition: .3s;
}

.event-card:hover {
    transform: translateY(-5px);

    box-shadow:
        0 10px 25px rgba(0,0,0,.1);
}

.event-card h3 {
    color: #4338ca;
}

/* BADGES */

.badge {
    display: inline-block;

    background: #eef2ff;

    color: #4338ca;

    padding: 5px 10px;

    border-radius: 20px;

    font-size: 13px;

    margin-bottom: 10px;
}

/* FORMS */

input,
textarea,
select {

    width: 100%;

    padding: 13px;

    margin: 8px 0;

    border: 1px solid #cbd5e1;

    border-radius: 8px;

    font-size: 15px;
}

textarea {
    min-height: 100px;
}

/* BUTTON */

button {

    border: none;

    background: #4f46e5;

    color: white;

    padding: 12px 20px;

    border-radius: 8px;

    cursor: pointer;

    font-size: 15px;

    font-weight: bold;

    margin-top: 8px;
}

button:hover {
    background: #3730a3;
}

.delete-btn {
    background: #dc2626;
}

.delete-btn:hover {
    background: #991b1b;
}

.register-btn {
    background: #059669;
}

.register-btn:hover {
    background: #047857;
}

/* AI */

.ai-box {
    background:
        linear-gradient(
            135deg,
            #eef2ff,
            #faf5ff
        );

    border-left: 5px solid #6366f1;
}

.ai-result {

    background: white;

    padding: 20px;

    border-radius: 10px;

    margin-top: 20px;

    white-space: pre-wrap;

    line-height: 1.6;
}

/* DASHBOARD */

.stats {

    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(200px, 1fr));

    gap: 20px;
}

.stat {

    background:
        linear-gradient(
            135deg,
            #4f46e5,
            #7c3aed
        );

    color: white;

    padding: 25px;

    border-radius: 12px;

    text-align: center;
}

.stat h3 {
    font-size: 35px;
    margin: 5px;
}

/* FOOTER */

footer {

    background: #111827;

    color: #cbd5e1;

    text-align: center;

    padding: 30px;

    margin-top: 50px;
}

/* MODAL */

.modal {

    display: none;

    position: fixed;

    top: 0;
    left: 0;

    width: 100%;
    height: 100%;

    background: rgba(0,0,0,.6);

    justify-content: center;

    align-items: center;

    z-index: 1000;
}

.modal-content {

    background: white;

    padding: 30px;

    width: 90%;

    max-width: 500px;

    border-radius: 15px;
}

.close {

    float: right;

    font-size: 25px;

    cursor: pointer;

    color: red;
}

/* SEARCH */

.search-box {

    display: flex;

    gap: 10px;

    margin-bottom: 20px;
}

.search-box input {
    margin: 0;
}

@media(max-width:600px) {

    .hero h1 {
        font-size: 30px;
    }

    nav {
        flex-direction: column;
        gap: 10px;
    }

}

</style>

</head>

<body>

<!-- NAVIGATION -->

<nav>

    <h2>🤖 AI Events</h2>

    <span>
        Smart Event Management System
    </span>

</nav>


<!-- HERO -->

<section class="hero">

    <h1>
        AI-Powered Event Management
    </h1>

    <p>
        Create, discover, manage and register for events
        using intelligent AI technology.
    </p>

</section>


<div class="container">


<!-- DASHBOARD -->

<div class="card">

<h2>📊 Event Dashboard</h2>

<div class="stats">

<div class="stat">
<h3 id="totalEvents">0</h3>
<p>Total Events</p>
</div>

<div class="stat">
<h3 id="totalRegistrations">0</h3>
<p>Total Registrations</p>
</div>

<div class="stat">
<h3 id="totalSeats">0</h3>
<p>Total Seats</p>
</div>

</div>

</div>


<!-- EVENTS -->

<div class="card">

<h2>📅 Available Events</h2>

<div class="search-box">

<input
    type="text"
    id="search"
    placeholder="Search events..."
    onkeyup="searchEvents()">

<select id="categoryFilter"
        onchange="searchEvents()">

<option value="">All Categories</option>

<option value="Technology">
Technology
</option>

<option value="Business">
Business
</option>

<option value="Education">
Education
</option>

<option value="Sports">
Sports
</option>

<option value="Entertainment">
Entertainment
</option>

</select>

</div>

<div id="events"
     class="event-grid">

</div>

</div>


<!-- CREATE EVENT -->

<div class="card">

<h2>➕ Create New Event</h2>

<form onsubmit="createEvent(event)">

<input
    id="title"
    placeholder="Event Title"
    required>

<textarea
    id="description"
    placeholder="Event Description"
    required></textarea>

<input
    id="date"
    type="datetime-local"
    required>

<input
    id="location"
    placeholder="Location"
    required>

<select id="category" required>

<option value="">
Select Category
</option>

<option>Technology</option>
<option>Business</option>
<option>Education</option>
<option>Sports</option>
<option>Entertainment</option>

</select>

<input
    id="capacity"
    type="number"
    placeholder="Maximum Capacity"
    min="1"
    required>

<button type="submit">
Create Event
</button>

</form>

</div>


<!-- AI RECOMMENDATION -->

<div class="card ai-box">

<h2>🧠 AI Event Recommendation</h2>

<p>
Tell the AI what kind of event you are interested in.
</p>

<input
    id="interest"
    placeholder="Example: AI, business, sports, music">

<button onclick="recommendEvents()">
🤖 Get AI Recommendations
</button>

<div id="recommendation"
     class="ai-result"
     style="display:none">
</div>

</div>


<!-- AI CHATBOT -->

<div class="card ai-box">

<h2>💬 AI Event Assistant</h2>

<p>
Ask the AI anything about events.
</p>

<textarea
    id="question"
    placeholder="Example: Which event is best for a student interested in technology?">
</textarea>

<button onclick="askAI()">
🤖 Ask AI
</button>

<div id="answer"
     class="ai-result"
     style="display:none">
</div>

</div>

</div>


<!-- REGISTRATION MODAL -->

<div id="registerModal"
     class="modal">

<div class="modal-content">

<span class="close"
      onclick="closeModal()">
×
</span>

<h2>🎟️ Event Registration</h2>

<input
    id="regName"
    placeholder="Your Name">

<input
    id="regEmail"
    type="email"
    placeholder="Your Email">

<button onclick="submitRegistration()">
Register Now
</button>

<input
    type="hidden"
    id="selectedEvent">

</div>

</div>


<footer>

<p>
AI Event Management System © 2026
</p>

<p>
Built using Python, Flask, SQLite and AI
</p>

</footer>


<script>

/* =========================================================
   LOAD EVENTS
========================================================= */

let allEvents = [];

async function loadEvents() {

    const response =
        await fetch("/api/events");

    allEvents =
        await response.json();

    displayEvents(allEvents);

    updateDashboard();
}


/* =========================================================
   DISPLAY EVENTS
========================================================= */

function displayEvents(events) {

    const container =
        document.getElementById("events");

    if (events.length === 0) {

        container.innerHTML =
            "<p>No events found.</p>";

        return;
    }

    container.innerHTML =
        events.map(event => `

        <div class="event-card">

            <span class="badge">
                ${event.category}
            </span>

            <h3>
                ${event.title}
            </h3>

            <p>
                ${event.description}
            </p>

            <p>
                📅 <b>Date:</b>
                ${event.date}
            </p>

            <p>
                📍 <b>Location:</b>
                ${event.location}
            </p>

            <p>
                👥 <b>Seats:</b>
                ${event.registered}
                /
                ${event.capacity}
            </p>

            <button
                class="register-btn"
                onclick="openRegister(${event.id})">

                🎟️ Register

            </button>

            <button
                class="delete-btn"
                onclick="deleteEvent(${event.id})">

                🗑️ Delete

            </button>

        </div>

    `).join("");

}


/* =========================================================
   SEARCH
========================================================= */

function searchEvents() {

    const search =
        document
        .getElementById("search")
        .value
        .toLowerCase();

    const category =
        document
        .getElementById("categoryFilter")
        .value;

    const filtered =
        allEvents.filter(event => {

            const matchesSearch =
                event.title
                .toLowerCase()
                .includes(search)
                ||
                event.description
                .toLowerCase()
                .includes(search);

            const matchesCategory =
                category === ""
                ||
                event.category === category;

            return matchesSearch &&
                   matchesCategory;

        });

    displayEvents(filtered);
}


/* =========================================================
   CREATE EVENT
========================================================= */

async function createEvent(e) {

    e.preventDefault();

    const event = {

        title:
            document
            .getElementById("title")
            .value,

        description:
            document
            .getElementById("description")
            .value,

        date:
            document
            .getElementById("date")
            .value,

        location:
            document
            .getElementById("location")
            .value,

        category:
            document
            .getElementById("category")
            .value,

        capacity:
            document
            .getElementById("capacity")
            .value

    };

    const response =
        await fetch("/api/events", {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify(event)

        });

    const result =
        await response.json();

    if (response.ok) {

        alert(
            "✅ Event created successfully!"
        );

        document.querySelector("form")
                .reset();

        loadEvents();

    } else {

        alert(
            "❌ " + result.message
        );

    }

}


/* =========================================================
   DELETE EVENT
========================================================= */

async function deleteEvent(id) {

    if (
        !confirm(
            "Are you sure you want to delete this event?"
        )
    ) {
        return;
    }

    const response =
        await fetch(
            "/api/events/" + id,
            {
                method: "DELETE"
            }
        );

    if (response.ok) {

        alert(
            "Event deleted successfully."
        );

        loadEvents();

    }

}


/* =========================================================
   REGISTRATION MODAL
========================================================= */

function openRegister(id) {

    document
        .getElementById("selectedEvent")
        .value = id;

    document
        .getElementById("registerModal")
        .style.display = "flex";

}


function closeModal() {

    document
        .getElementById("registerModal")
        .style.display = "none";

}


/* =========================================================
   REGISTER
========================================================= */

async function submitRegistration() {

    const eventId =
        document
        .getElementById("selectedEvent")
        .value;

    const name =
        document
        .getElementById("regName")
        .value;

    const email =
        document
        .getElementById("regEmail")
        .value;

    if (!name || !email) {

        alert(
            "Please enter your name and email."
        );

        return;

    }

    const response =
        await fetch(
            "/api/events/"
            + eventId
            + "/register",
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify({
                        name,
                        email
                    })

            }
        );

    const result =
        await response.json();

    if (response.ok) {

        alert(
            "🎉 Registration successful!"
        );

        closeModal();

        document
            .getElementById("regName")
            .value = "";

        document
            .getElementById("regEmail")
            .value = "";

        loadEvents();

    } else {

        alert(
            "❌ " + result.message
        );

    }

}


/* =========================================================
   AI RECOMMENDATION
========================================================= */

async function recommendEvents() {

    const interest =
        document
        .getElementById("interest")
        .value;

    if (!interest) {

        alert(
            "Please enter your interests."
        );

        return;

    }

    const box =
        document
        .getElementById("recommendation");

    box.style.display = "block";

    box.innerHTML =
        "🤖 AI is analyzing events...";

    const response =
        await fetch(
            "/api/ai/recommend",
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify({
                        interest,
                        events: allEvents
                    })

            }
        );

    const result =
        await response.json();

    box.innerHTML =
        result.recommendation;

}


/* =========================================================
   AI CHAT
========================================================= */

async function askAI() {

    const question =
        document
        .getElementById("question")
        .value;

    if (!question) {

        alert(
            "Please enter a question."
        );

        return;

    }

    const box =
        document
        .getElementById("answer");

    box.style.display = "block";

    box.innerHTML =
        "🤖 AI is thinking...";

    const response =
        await fetch(
            "/api/ai/chat",
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify({
                        question
                    })

            }
        );

    const result =
        await response.json();

    box.innerHTML =
        result.answer;

}


/* =========================================================
   DASHBOARD
========================================================= */

async function updateDashboard() {

    const totalEvents =
        allEvents.length;

    const totalRegistrations =
        allEvents.reduce(
            (sum, event) =>
                sum + event.registered,
            0
        );

    const totalSeats =
        allEvents.reduce(
            (sum, event) =>
                sum + event.capacity,
            0
        );

    document
        .getElementById("totalEvents")
        .innerText = totalEvents;

    document
        .getElementById("totalRegistrations")
        .innerText =
            totalRegistrations;

    document
        .getElementById("totalSeats")
        .innerText =
            totalSeats;

}


/* =========================================================
   START
========================================================= */

loadEvents();

</script>

</body>

</html>
"""


# ============================================================
# ROUTE: HOME
# ============================================================

@app.route("/")
def home():
    return render_template_string(HTML)


# ============================================================
# API: GET EVENTS
# ============================================================

@app.route("/api/events", methods=["GET"])
def get_events():

    conn = get_db()

    events = conn.execute(
        "SELECT * FROM events ORDER BY date"
    ).fetchall()

    conn.close()

    return jsonify([
        dict(event)
        for event in events
    ])


# ============================================================
# API: CREATE EVENT
# ============================================================

@app.route("/api/events", methods=["POST"])
def create_event():

    data = request.json

    required = [
        "title",
        "description",
        "date",
        "location",
        "category",
        "capacity"
    ]

    for field in required:

        if not data.get(field):

            return jsonify({
                "message":
                    f"{field} is required"
            }), 400

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO events
        (
            title,
            description,
            date,
            location,
            category,
            capacity
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["title"],
        data["description"],
        data["date"],
        data["location"],
        data["category"],
        int(data["capacity"])
    ))

    conn.commit()

    event_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "message": "Event created",
        "id": event_id
    }), 201


# ============================================================
# API: DELETE EVENT
# ============================================================

@app.route(
    "/api/events/<int:event_id>",
    methods=["DELETE"]
)
def delete_event(event_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM registrations WHERE event_id = ?",
        (event_id,)
    )

    conn.execute(
        "DELETE FROM events WHERE id = ?",
        (event_id,)
    )

    conn.commit()

    conn.close()

    return jsonify({
        "message":
            "Event deleted successfully"
    })


# ============================================================
# API: REGISTER
# ============================================================

@app.route(
    "/api/events/<int:event_id>/register",
    methods=["POST"]
)
def register_event(event_id):

    data = request.json

    name = data.get("name")
    email = data.get("email")

    if not name or not email:

        return jsonify({
            "message":
                "Name and email are required"
        }), 400

    conn = get_db()

    event = conn.execute(
        "SELECT * FROM events WHERE id = ?",
        (event_id,)
    ).fetchone()

    if not event:

        conn.close()

        return jsonify({
            "message": "Event not found"
        }), 404

    if event["registered"] >= event["capacity"]:

        conn.close()

        return jsonify({
            "message":
                "❌ Event is fully booked"
        }), 400

    conn.execute("""
        INSERT INTO registrations
        (event_id, name, email)
        VALUES (?, ?, ?)
    """, (
        event_id,
        name,
        email
    ))

    conn.execute("""
        UPDATE events
        SET registered = registered + 1
        WHERE id = ?
    """, (event_id,))

    conn.commit()

    conn.close()

    return jsonify({
        "message":
            "🎉 Registration successful!"
    })


# ============================================================
# AI RECOMMENDATION
# ============================================================

@app.route(
    "/api/ai/recommend",
    methods=["POST"]
)
def ai_recommend():

    data = request.json

    interest = data.get(
        "interest",
        ""
    )

    events = data.get(
        "events",
        []
    )

    # ------------------------------------
    # If OpenAI is available
    # ------------------------------------

    api_key = os.environ.get(
        "OPENAI_API_KEY"
    )

    if OPENAI_AVAILABLE and api_key:

        try:

            client = OpenAI(
                api_key=api_key
            )

            prompt = f"""
You are an AI event recommendation system.

User interest:
{interest}

Available events:
{events}

Recommend the best 3 events.

For each event explain why it
matches the user's interest.

Keep the response simple.
"""

            response = client.responses.create(
                model="gpt-5",
                input=prompt
            )

            return jsonify({
                "recommendation":
                    response.output_text
            })

        except Exception as e:

            print(e)

    # ------------------------------------
    # Fallback AI-like recommendation
    # ------------------------------------

    interest_words = set(
        interest.lower().split()
    )

    scored = []

    for event in events:

        text = (
            event["title"]
            + " "
            + event["description"]
            + " "
            + event["category"]
        ).lower()

        score = sum(
            1
            for word in interest_words
            if word in text
        )

        scored.append(
            (score, event)
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    top = scored[:3]

    if not top:

        recommendation = (
            "No matching events found."
        )

    else:

        recommendation = (
            "🤖 AI Event Recommendations\n\n"
        )

        for score, event in top:

            recommendation += (
                f"📌 {event['title']}\n"
                f"Category: {event['category']}\n"
                f"Location: {event['location']}\n"
                f"Date: {event['date']}\n"
                f"Why: This event matches "
                f"your interest in "
                f"'{interest}'.\n\n"
            )

    return jsonify({
        "recommendation":
            recommendation
    })


# ============================================================
# AI CHATBOT
# ============================================================

@app.route(
    "/api/ai/chat",
    methods=["POST"]
)
def ai_chat():

    data = request.json

    question = data.get(
        "question",
        ""
    )

    api_key = os.environ.get(
        "OPENAI_API_KEY"
    )

    # ------------------------------------
    # Real AI
    # ------------------------------------

    if OPENAI_AVAILABLE and api_key:

        try:

            client = OpenAI(
                api_key=api_key
            )

            prompt = f"""
You are an AI assistant for an
Event Management System.

Answer this question clearly:

{question}

Help users with:
- Event selection
- Event planning
- Registration
- Event ideas
- Technology events
- Business events
- Education events
- Sports events
- Entertainment events
"""

            response = client.responses.create(
                model="gpt-5",
                input=prompt
            )

            return jsonify({
                "answer":
                    response.output_text
            })

        except Exception as e:

            print(e)

    # ------------------------------------
    # Fallback response
    # ------------------------------------

    question_lower = question.lower()

    if "create" in question_lower:

        answer = """
To create an event:

1. Enter the event title.
2. Add a description.
3. Select the date and time.
4. Enter the location.
5. Select a category.
6. Enter the maximum capacity.
7. Click Create Event.
"""

    elif "register" in question_lower:

        answer = """
To register for an event:

1. Find your preferred event.
2. Click Register.
3. Enter your name.
4. Enter your email.
5. Click Register Now.
"""

    elif "technology" in question_lower:

        answer = """
Technology events are excellent for
students interested in programming,
Artificial Intelligence, Machine Learning,
Web Development and software engineering.
"""

    elif "business" in question_lower:

        answer = """
Business events can help you learn
entrepreneurship, startups, marketing,
finance and management.
"""

    else:

        answer = """
I am your AI Event Assistant.

I can help you with:

• Finding suitable events
• Event registration
• Event planning
• Technology events
• Business events
• Education events
• Sports events
• Event ideas

For more advanced AI responses,
add your OPENAI_API_KEY.
"""

    return jsonify({
        "answer": answer
    })


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    init_db()

    print()
    print("==========================================")
    print("🤖 AI EVENT MANAGEMENT SYSTEM")
    print("==========================================")
    print("Server: http://127.0.0.1:5000")
    print("==========================================")
    print()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
