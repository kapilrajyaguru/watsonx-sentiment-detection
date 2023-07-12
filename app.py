from flask import Flask, render_template, request, jsonify
import traceback
import psycopg2
import requests
import json

app = Flask(__name__)

# Replace the following database credentials with your own
DB_NAME = 'your_database_name'
DB_USER = 'your_username'
DB_PASSWORD = 'your_password'
DB_HOST = 'your_host'
DB_PORT = 'your_port'

def create_table():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS comments (
        id SERIAL PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        gender TEXT,
        country TEXT,
        comment_text TEXT,
        sentiment TEXT
    )
    '''
)

    conn.commit()
    cursor.close()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            gender = request.form['gender']
            country = request.form['country']
            comment_text = request.form['comment']
            insert_comment(first_name, last_name, gender, country, comment_text)
        except Exception as e:
            traceback.print_exc()
            return jsonify({'error': str(e)})
    return render_template('index.html')


def get_sentiment(review):
    url = "https://us-south.ml.cloud.ibm.com/ml/v1-beta/generation/text?version=2023-05-29"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer <your_access_token>'
    }
    data = {
        "model_id": "ibm/mpt-7b-instruct2",
        "input": f"Classify this review as positive or negative.\\n\\nReview:\\n{review}\\n\\nClassification:\\n",
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 6,
            "min_new_tokens": 0,
            "stop_sequences": [],
            "repetition_penalty": 1,
            "time_limit": 60
        },
        "project_id": "<your_project_id>"
    }
    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()
    results = response_json.get('results')
    if results and len(results) > 0:
        generated_text = results[0].get('generated_text')
        if generated_text:
            sentiment_start_index = generated_text.rfind(':') + 1
            sentiment = generated_text[sentiment_start_index:].strip(' "')
            return sentiment
    return None


def insert_comment(first_name, last_name, gender, country, comment_text):
    sentiment = get_sentiment(comment_text)
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO comments (first_name, last_name, gender, country, comment_text, sentiment)
        VALUES (%s, %s, %s, %s, %s, %s)
        ''',
        (first_name, last_name, gender, country, comment_text, sentiment)
    )
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    create_table()
    app.run()