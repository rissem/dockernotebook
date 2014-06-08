from flask import Flask, redirect, request
import docker
import re

client = docker.Client(base_url='unix:///var/run/docker.sock',
                  version='1.9',
                  timeout=10)

imageNameTagRE = re.compile(r'(?P<name>[^:]*)(:(?P<tag>.*))?$')

#print client.info()

app = Flask(__name__)

@app.route("/")
def hello():
    return app.send_static_file('index.html')

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
        containerImage = "unfairbanks/docker-ipython-notebook:latest"

    # If we aren't given a tag let's use "latest"
    reGroups = imageNameTagRE.search(containerImage).groupdict()
    imageName = reGroups['name']
    imageTag = reGroups['tag']
    if imageTag == '' or imageTag is None:
        imageTag = "latest"

    fullImageName = '%s:%s' % (imageName, imageTag)

    for image in client.images():
        client.pull(imageName, tag="latest")

    container = client.create_container(fullImageName, environment=env)
    client.start(container, publish_all_ports=True, privileged=True)

    containerLinks = ""
    ipythonPort = -1
    for port, mapping in client.inspect_container(container)['NetworkSettings']['Ports'].items():
        hostPort = mapping[0]['HostPort']
        if port == '8080/tcp':
            ipythonPort = hostPort
            containerLinks = "<a href='http://dockernotebook.com:%s'>Your IPython Notebook</a><br/>%s" % (hostPort, containerLinks)
        else:
            containerLinks = "%s<a href='http://dockernotebook.com:%s'>Serving on additional port %s (%s)</a><br/>" % (containerLinks, hostPort, hostPort, port)
    return (containerLinks)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
