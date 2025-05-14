from flask import Flask, render_template, request, jsonify
import nexai.src.agents.Search_Agent as Agent1 # Import the agent functions from agent.py
import nexai.src.agents.Assistant_Agent as Assistant
import nexai.src.agents.Ad_Performance_Predictor as Performance

app = Flask(__name__, template_folder="nexai/templates", static_folder="nexai/static")

chat_history = []  # Store chat history for the assistant

@app.route("/", methods=["GET", "POST"])
def index():
    generated_ad = ""
    similar_ads_html = ""
    suggested_questions = []

    if request.method == "POST":
        product_desc = request.form["product"]

        # Step 1: Generate ad
        generated_ad = Agent1.generate_ad(product_desc)

        # Step 2: Search for similar ads
        similar_ads_list = Agent1.find_similar_ads(generated_ad)

        # Step 3: Rank and filter the ads
        top_ads = Agent1.rank_and_filter_ads(similar_ads_list)

        # Step 4: Format the ads for HTML rendering
        similar_ads_html = Agent1.format_ads_html(top_ads)
        # Step 5: Prepare context for suggested questions
        context = f"{generated_ad}\n\nSimilar Ads:\n" + "\n".join([ad.get('ad_title', '') for ad in top_ads])
        # Step 6: Get suggested questions
        suggested_questions = Assistant.suggest_questions(context)
        

    return render_template("index.html", generated_ad=generated_ad, similar_ads=similar_ads_html, suggested_questions=suggested_questions)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["message"]

    # Get assistant reply
    assistant_reply = Assistant.get_chat_response(chat_history, user_message)

    # Update chat history
    chat_history.append((user_message, assistant_reply))

    return {"assistant_reply": assistant_reply}


@app.route("/predict_ctr", methods=["POST"])
def predict_ctr():
    product_desc = request.form.get("product")
    if not product_desc:
        return jsonify({"error": "Product description is required"}), 400

    # Step 1: Predict CTR
    predicted_ctr = Performance.predict_ctr_from_description(product_desc)

    if predicted_ctr is None:
        return jsonify({"error": "Failed to predict CTR"}), 500

    # Step 2: Ask LLM to evaluate this CTR
    evaluation = Performance.evaluate_ctr_with_llm(predicted_ctr, product_desc)

    return jsonify({
        "ctr": predicted_ctr * 100,  # percentage format
        "evaluation": evaluation
    })

if __name__ == "__main__":
    app.run(debug=True)