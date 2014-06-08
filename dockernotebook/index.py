from flask import Flask, redirect, request
import docker

client = docker.Client(base_url='unix:///var/run/docker.sock',
                  version='1.9',
                  timeout=10)

#print client.info()

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/create")
def create():
    repo = request.args.get("repo")
    repoDir = request.args.get("repoDir")
    containerImage = request.args.get("containerImage")
    if repo:
        env = {"GIT_REPO": repo}
    else:
        env = {}
    if repoDir:
        env["REPO_DIR"] = repoDir
    if not containerImage:
        containerImage = "226ceaf95c3c"

    container = client.create_container(containerImage, ports=[8080], environment=env)
    containerId = container['Id']
    client.start(containerId, publish_all_ports=True)
    port = client.port(containerId, 8080)[0]["HostPort"]
    return ("<a href='http://dockernotebook.com:" + port + "/'>Your Notebook</a>")

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
