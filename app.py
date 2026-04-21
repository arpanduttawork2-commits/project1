from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Deployment Successful!</h1><p>Render is successfully running your Flask app. Next step: Add the database and HTML templates.</p>"

if __name__ == "__main__":
    # Render provides a PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)