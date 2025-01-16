import logging
from openai import AzureOpenAI, RateLimitError, OpenAIError

# ----------------------------------------------------------------------------------------
# Azure OpenAI API settings:
#   - Replace with your actual API key, Azure endpoint, and API version if necessary.
#   - Make sure to keep these sensitive values secure.
# ----------------------------------------------------------------------------------------
api_key = "************************************"
azure_endpoint = "*************************************"
api_version = "**********************************"

# ----------------------------------------------------------------------------------------
# Initialize the Azure OpenAI client:
#   - This client communicates with the Azure OpenAI service.
#   - It leverages the provided endpoint, API key, and version.
# ----------------------------------------------------------------------------------------
client = AzureOpenAI(
    azure_endpoint=azure_endpoint,
    api_key=api_key,
    api_version=api_version,
)

# ----------------------------------------------------------------------------------------
# Configure logging:
#   - Logging level set to INFO to capture standard info, warnings, and errors.
# ----------------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------------------
# generate_response function:
#   - Accepts input_data (dict) containing 'query', 'questions', 'correct_answers', and 'user_answers'.
#   - Constructs a prompt for GPT-4 to provide feedback for each question.
#   - Returns feedback or error messages in a dictionary.
# ----------------------------------------------------------------------------------------
def generate_response(input_data):
    
    # Extract relevant fields from the input_data dictionary
    query = input_data.get("query", "")
    questions = input_data.get("questions", [])
    correct_answers = input_data.get("correct_answers", [])
    user_answers = input_data.get("user_answers", [])

    # ------------------------------------------------------------------------------------
    # Validate input data:
    #   - Ensure questions, correct_answers, and user_answers are non-empty lists.
    #   - Ensure these lists all have the same length.
    # ------------------------------------------------------------------------------------
    if not questions or not correct_answers or not user_answers:
        logger.error("Invalid input data. Ensure questions, correct_answers, and user_answers are provided.")
        return {"error": "Invalid input data."}

    if len(questions) != len(correct_answers) or len(questions) != len(user_answers):
        logger.error("Mismatch in the length of questions, correct_answers, and user_answers.")
        return {"error": "Length mismatch in input data."}

    # ------------------------------------------------------------------------------------
    # Construct the prompt for GPT-4:
    #   - Provide context to GPT-4: "You are a CCNA exam coach..."
    #   - Include each question, the correct answer, and the user's answer.
    #   - Ask GPT-4 to provide detailed feedback for each question.
    # ------------------------------------------------------------------------------------
    feedback_prompt = (
        "You are a CCNA exam coach. I'm attempting a practice test with questions, here is my query: \"{}\". "
        "For each question, provide detailed feedback. Include the following: \n"
        "- Whether my answer is correct or incorrect. \n"
        "- If incorrect, explain why the chosen answer is wrong. \n"
        "- Offer specific advice on what I should focus on learning to improve. \n"
        "At the end, recommend areas of study based on my answers."
    ).format(query)

    # Append each question block to the feedback prompt
    for i, (question, correct_answer, user_answer) in enumerate(zip(questions, correct_answers, user_answers), 1):
        feedback_prompt += (
            f"\n\nQuestion {i}: {question}\n"
            f"Correct Answer: {correct_answer}\n"
            f"My Answer: {user_answer}\n"
        )

    # Add final instructions for overall performance summary
    feedback_prompt += "\n\nProvide a summary of the overall performance and learning recommendations."

    # ------------------------------------------------------------------------------------
    # Make the API call to the GPT-4 model via the Azure OpenAI client:
    #   - We pass a list of messages: a system prompt followed by the user prompt.
    #   - The system prompt sets the context that GPT-4 is a CCNA coach.
    #   - The user prompt includes the constructed feedback_prompt with all questions/answers.
    # ------------------------------------------------------------------------------------
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Replace this with the specific engine/model name if required
            messages=[
                {"role": "system", "content": "You are a CCNA exam coach."},
                {"role": "user", "content": feedback_prompt},
            ]
        )

        # Extract the response text from GPT-4
        feedback = response.choices[0].message.content.strip()
        return {"feedback": feedback}

    # ------------------------------------------------------------------------------------
    # Handle rate limiting or other known OpenAI exceptions:
    # ------------------------------------------------------------------------------------
    except RateLimitError as e:
        logger.error(f"Rate limit error: {e}")
        return {"error": "Rate limit exceeded. Please try again later."}

    except OpenAIError as e:
        logger.error(f"OpenAI error: {e}")
        return {"error": "An error occurred with the OpenAI API."}

    # ------------------------------------------------------------------------------------
    # Catch-all for any other unexpected exceptions:
    # ------------------------------------------------------------------------------------
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": "An unexpected error occurred."}
