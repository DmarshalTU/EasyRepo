import os
import shutil
import git
import quart
import quart_cors
from quart import jsonify
from quart import request
from pydriller import Repository


app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")
api_key=os.environ.get("API_KEY")

def analyze_code(repo_url):
    results = []
    for commit in Repository(repo_url).traverse_commits():
        commit_info = {
            "hash": commit.hash,
            "message": commit.msg,
            "author": commit.author.name,
            "modified_files": [file.filename for file in commit.modified_files]
        }
        results.append(commit_info)
    return results


@app.get("/repo-info")
def fetch_repo_info():
    repo_url = request.args.get('url')

    if repo_url is None:
        return jsonify({"error": "No URL provided"}), 400

    try:
        repo_dir = f"tmp/repo/{repo_url.split('/')[-1]}"

        if not os.path.exists(repo_dir):
            git.Repo.clone_from(repo_url, repo_dir)
            app.logger.info(f"Cloned repo {repo_url} to {repo_dir}")
        
        with open(f'{repo_dir}/README.md', "r") as readme_file:
            readme = readme_file.read()

        return jsonify({"readme": readme})

    except Exception as e:
        app.logger.error("Error: " + str(e))
        return jsonify({"error": str(e)}), 400


@app.get("/code-analysis")
def code_analysis():
    repo_url = request.args.get('url')

    if repo_url is None:
        return jsonify({"error": "No URL provided"}), 400

    try:
        analysis = analyze_code(repo_url)
        return jsonify({"analysis": analysis})

    except Exception as e:
        app.logger.error("Error: " + str(e))
        return jsonify({"error": str(e)}), 400


# ________________MUST BE SET FOR EasyRepo TO WORK________________
# on every change to endpoint, update openapi.yaml and ai-plugin.json!

@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open(".well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("./openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

# ________________/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\________________


def main():
    try:
        shutil.rmtree('tmp')
    except:
        pass
    app.run(debug=True, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
