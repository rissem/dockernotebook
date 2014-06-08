from flask import Flask, redirect, request, Response, stream_with_context
import docker
import requests
import time

client = docker.Client(base_url='unix:///var/run/docker.sock',
                  version='1.9',
                  timeout=10)

#print client.info()

app = Flask(__name__)

@app.route("/")
def hello():
    return app.send_static_file('index.html')

# it would be nice to proxy; unfortunately iPython notebook has some absolute URLS
# if that were fixed and this proxy worked completely, the create endpoint could
# redirect intead of just sending a link
@app.route("/container")
def container():
    containerId = request.args.get("id")
    port = client.port(containerId, 8080)[0]["HostPort"]
    req = requests.get("http://dockernotebook.com:" + port, stream = True)
    return Response(stream_with_context(req.iter_content()), content_type = req.headers['content-type'])

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
    
    #try to hit port, once we do return this URL to user
    serverStarted = False
    while not serverStarted:
        time.sleep(1)
        try:
            req = requests.get('http://dockernotebook.com:' + port)
            if req.status_code == 200:
                serverStarted = True
        except Exception as e:
            print("CONNECTION ERROR", e)
    return ("<a href='http://dockernotebook.com:" + port + "/'>Your Notebook</a>")

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
