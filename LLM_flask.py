from flask import Flask, jsonify, request
from LLM_processing import *
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes


# This URI is used if google search results need to be used while asking for url response
@app.route('/serp', methods = ['GET'])
def get_chatgpt_repsonse_from_url():
    args = request.args
    url = args.get('url')
    output = get_response_from_URL(url)
    print(output)
    if output:
        return jsonify({"output":output["output_text"]})
    else:
        return jsonify({"output":"NO Response"})

# This URI is used if google search results are not used, the query is directly asked to LLM
@app.route('/query', methods = ['GET'])
def get_chatgpt_repsonse_from_query():
    args = request.args
    query = args.get('query')
    output = get_response_from_query(query)
    print(output)
    if output:
        return jsonify({"output":output["output_text"]})
    else:
        return jsonify({"output":"NO Response"})
        


if __name__ == '__main__':
    app.run(debug=True, port=5000)
