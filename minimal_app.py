#!/usr/bin/env python
"""Minimal Flask app for testing"""
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Flask is working!</h1>"

@app.route("/login")
def login():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Login</title></head>
    <body>
        <h1>Login Page</h1>
        <form method="post">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """

if __name__ == "__main__":
    print("Starting minimal Flask app on port 5000...")
    app.run(debug=True, host="0.0.0.0", port=5000)
