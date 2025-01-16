from flask import Flask, request, jsonify  # For creating and handling Flask API requests/responses
from search import search_questions        # Custom module to search for questions
from generate_response import generate_response  # Custom module to generate AI-powered responses
import psycopg2                            # PostgreSQL database adapter
import random                              # For shuffling question options
from flask_cors import CORS                # For enabling Cross-Origin Resource Sharing (CORS)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes in the Flask app

# --------------------------------------------------------------------
# Database Connection:
#   - Connect to the local PostgreSQL database 'ccna_db'
#   - Update the credentials (dbname, user, password, host) as needed
# --------------------------------------------------------------------
conn = psycopg2.connect(
    dbname="ccna_db",
    user="*********",
    password="*******",
    host="localhost"
)

# --------------------------------------------------------------------
# SEARCH Endpoint (/search):
#   - Expects a JSON payload with a "query" field.
#   - Performs a search for CCNA-related questions using ChromaDB (or another search mechanism).
#   - Returns up to 5 relevant questions, along with their correct/incorrect answers.
# --------------------------------------------------------------------
@app.route('/search', methods=['POST'])
def search_endpoint():
    data = request.json
    query = data.get("query", "")

    # If no query is provided, return a 400 Bad Request response
    if not query:
        return jsonify({"error": "Query is required"}), 400

    # ------------------------------------------------------------------ #
    # Tokenize the user's query into a set of words (for a relevance check)
    # ------------------------------------------------------------------ #
    query_words = set(query.lower().split())

    # Fetch results from the search_questions function with top_k=5
    results = search_questions(query, top_k=5)

    # If the results are nested (as a list of lists from ChromaDB), flatten them
    if len(results) > 0 and isinstance(results[0], list):
        questions_flat = results[0]
    else:
        questions_flat = results

    # If no results are found, respond with an error message
    if not questions_flat:
        return jsonify({"error": "No CCNA-related topics found. Try a different CCNA topic."}), 400

    # ----------------------------------------------------------------------- #
    # Check if at least one question is "relevant" to the user's query:
    #   - If no question intersects with the query_words set, 
    #     assume the topic is not CCNA-related and return a 400 response.
    # ----------------------------------------------------------------------- #
    found_relevant = False
    for question_text in questions_flat:
        question_words = set(question_text.lower().split())
        if query_words.intersection(question_words):
            found_relevant = True
            break

    if not found_relevant:
        return jsonify({
            "error": "The topic should be related to CCNA. "
                     "Please try again with a valid CCNA-related topic."
        }), 400

    # Prepare a list to store the final questions with their correct and incorrect answers
    questions_with_answers = []

    try:
        # For each question retrieved, find its correct and incorrect answers in the database
        for idx, question_text in enumerate(questions_flat, start=1):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT correct_answer, incorrect_answers 
                    FROM questions 
                    WHERE question = %s
                    """,
                    (question_text,)
                )
                result = cur.fetchone()

                # If the question exists in the database, extract its answers
                if result:
                    correct_answer, incorrect_answers = result
                    # Ensure incorrect_answers is a list; handle if it's None or another data type
                    if not isinstance(incorrect_answers, list):
                        incorrect_answers = []
                else:
                    # If the question does not exist, provide placeholders
                    correct_answer = "Correct Answer Not Found"
                    incorrect_answers = ["Incorrect 1", "Incorrect 2", "Incorrect 3"]

                # Add the question data (including answers) to the list
                questions_with_answers.append({
                    "id": idx,
                    "question": question_text,
                    "correct_answer": correct_answer,
                    "incorrect_answers": incorrect_answers
                })

    except Exception as e:
        # Return a 500 Internal Server Error if there's any issue retrieving answers
        return jsonify({"error": f"Error retrieving answers: {e}"}), 500

    # Shuffle the final list of options for each question for randomness
    for question in questions_with_answers:
        options = [question['correct_answer']] + question['incorrect_answers']
        random.shuffle(options)
        question['options'] = options

    # Return the query, along with the question data, as JSON
    return jsonify({"query": query, "results": questions_with_answers})

# --------------------------------------------------------------------
# VALIDATE Endpoint (/validate):
#   - Expects JSON payload with "query", "questions", "correct_answers", "user_answers"
#   - Compares user answers to the correct answers
#   - Uses generate_response to produce feedback
# --------------------------------------------------------------------
@app.route('/validate', methods=['POST'])
def validate_endpoint():
    try:
        # Parse the JSON data from the request
        data = request.json
        # Ensure all required fields are present
        if not data or not all(k in data for k in ("query", "questions", "correct_answers", "user_answers")):
            return jsonify({"error": "Invalid input data. Ensure query, questions, correct_answers, and user_answers are provided."}), 400

        query = data["query"]
        questions = data["questions"]
        correct_answers = data["correct_answers"]
        user_answers = data["user_answers"]

        # Check that the lists of questions, correct_answers, and user_answers have the same length
        if not (len(questions) == len(correct_answers) == len(user_answers)):
            return jsonify({"error": "Mismatch in the length of questions, correct_answers, and user_answers."}), 400

        # Generate feedback (e.g., explanations, correctness checks) from a custom AI or logic
        feedback = generate_response({
            "query": query,
            "questions": questions,
            "correct_answers": correct_answers,
            "user_answers": user_answers
        })

        # Return the generated feedback to the client
        return jsonify({"feedback": feedback})

    except Exception as e:
        # Log the error and return a 500 Internal Server Error
        print(f"Error in /validate endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

# --------------------------------------------------------------------
# Main Server Entry Point:
#   - Runs the Flask app in debug mode.
#   - Remove debug=True in production for security/performance.
# --------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
