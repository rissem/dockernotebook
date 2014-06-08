from flask import Flask, redirect, request, Response, stream_with_context
import docker
import re
import requests
import time


containerURLPagePart1 = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Docker Notebook</title>

    <!-- Bootstrap -->
    <link href="/static/css/bootstrap.css" rel="stylesheet">
    <link href="/static/css/dockerNotebook.css" rel="stylesheet">

    <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
      <script src="https://oss.maxcdn.com/libs/respond.js/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>
  <body><h1>
"""

containerURLPagePart2 = """
  </h1></body>
</html
"""

client = docker.Client(base_url='unix:///var/run/docker.sock',
                  version='1.9',
                  timeout=10)

imageNameTagRE = re.compile(r'(?P<name>[^:]*)(:(?P<tag>.*))?$')

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
        containerImage = "unfairbanks/docker-ipython-notebook:latest"

    # If we aren't given a tag let's use "latest"
    reGroups = imageNameTagRE.search(containerImage).groupdict()
    imageName = reGroups['name']
    imageTag = reGroups['tag']
    if imageTag == '' or imageTag is None:
        imageTag = "latest"

    fullImageName = '%s:%s' % (imageName, imageTag)

    client.pull(imageName, tag=imageTag)

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

    #try to hit the IPython port, once we do return this URL to user
    serverStarted = False
    while not serverStarted:
        time.sleep(1)
        try:
            req = requests.get('http://dockernotebook.com:' + ipythonPort)
            if req.status_code == 200:
                serverStarted = True
        except Exception as e:
            print("CONNECTION ERROR", e)
    return (containerURLPagePart1 + containerLinks + containerURLPagePart2)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
