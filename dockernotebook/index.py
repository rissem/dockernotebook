from flask import Flask
import docker

client = docker.Client(base_url='unix:///var/run/docker.sock',
                  version='1.9',
                  timeout=10)

#print client.info()
container = client.create_container("unfairbanks/docker-ipython-notebook", ports=[8080])

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/create")
def create():
    container = client.create_container("unfairbanks/docker-ipython-notebook", ports=[8080])
    containerId = container['Id']
    client.start(containerId, publish_all_ports=True)
    port = client.port(containerId, 8080)[0]["HostPort"]
    return port

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
