import json
import logging
import urlparse

from google.appengine.api import search


try:
    from config import add_secret_token
except ImportError:
    add_secret_token = ''


INDEX_NAME = "nuts"


def send_json(start_response, status, headers, data):
    headers.append(("Content-Type", "application/json"))
    start_response(status, headers)
    return json.dumps(data)


def find(environ, start_response):
    """Search nuts."""

    response = {}

    if environ["REQUEST_METHOD"].upper() != "GET":
        response["Message"] = "405 Method Not Allowed: use GET"
        return send_json(start_response, "405 Method Not Allowed", [("Allow", "GET")], response)

    try:
        q = urlparse.parse_qs(environ["QUERY_STRING"])["q"][0]
    except (KeyError, IndexError) as e:
        logging.warning("Bad request: %r", e)
        response["Message"] = "400 Bad Request: %r" % e
        return send_json(start_response, "400 Bad Request", [], response)

    results = search.Index(name=INDEX_NAME).search(q)

    response["Nuts"] = []
    for res in results:
        nut = {"Rank": res.rank}
        for f in res.fields:
            nut[f.name] = f.value
        response["Nuts"].append(nut)
    response["Message"] = "OK"
    return send_json(start_response, "200 OK", [], response)


def add(environ, start_response):
    """
    Add nut to search index.

    Input: {"Nut": {"Name": "test_nut1",
                    "Doc": "Package test_nut1 is used to test nut."}}
    """

    response = {}

    if environ["REQUEST_METHOD"].upper() != "POST":
        response["Message"] = "405 Method Not Allowed: use POST"
        return send_json(start_response, "405 Method Not Allowed", [("Allow", "POST")], response)

    try:
        token = urlparse.parse_qs(environ["QUERY_STRING"])["token"][0]
        if token != add_secret_token:
            raise KeyError(token)
    except (KeyError, IndexError) as e:
        logging.warning("Bad token: %r", e)
        response["Message"] = "403 Forbidden: bad token"
        return send_json(start_response, "403 Forbidden", [], response)

    data = json.load(environ["wsgi.input"])
    logging.info("Adding %r", data)

    name = data["Nut"]["Name"]
    doc  = data["Nut"]["Doc"]
    if doc.lower().startswith("package %s " % name.lower()):
        doc = " ".join(doc.split(" ")[2:])
    if doc.endswith("."):
        doc = doc[:-1]

    # TODO rank
    fields = [
        search.TextField(name="Name", value=name),
        search.TextField(name="Doc",  value=doc),
    ]
    d = search.Document(doc_id=name, fields=fields)
    search.Index(name=INDEX_NAME).put(d)

    response["Message"] = "OK"
    return send_json(start_response, "201 Created", [], response)
