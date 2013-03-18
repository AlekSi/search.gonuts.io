import json
import logging
import urlparse

from google.appengine.api import search


try:
    from config import secret_token
except ImportError:
    secret_token = ''


INDEX = search.Index(name="nuts")
NO_RESPONSE_SENT = object()


def send_json(start_response, status, headers, data):
    res = ''
    if data is not None:
        res = json.dumps(data)

    headers.append(("Content-Type", "application/json"))
    headers.append(("Content-Length", str(len(res))))
    start_response(status, headers)
    return res


def check_method(environ, start_response, expected_method):
    if environ["REQUEST_METHOD"].upper() != expected_method:
        response = {"Message": "405 Method Not Allowed: use %s" % expected_method}
        return send_json(start_response, "405 Method Not Allowed", [("Allow", expected_method)], response)

    return NO_RESPONSE_SENT


def check_secret_token(environ, start_response):
    try:
        token = urlparse.parse_qs(environ["QUERY_STRING"])["token"][0]
        if token != secret_token:
            raise KeyError(token)
    except (KeyError, IndexError) as e:
        logging.warning("Bad token: %r", e)
        response = {"Message": "403 Forbidden: bad token"}
        return send_json(start_response, "403 Forbidden", [], response)

    return NO_RESPONSE_SENT


def find(environ, start_response):
    """
    Search nuts.

    Input: q.
    Output:
        {
          "Message": "OK",
          "Nuts": [
            {
              "Vendor": "aleksi",
              "Name": "test_nut1"
            }
          ]
        }
    """

    res = check_method(environ, start_response, "GET")
    if res is not NO_RESPONSE_SENT:
        return res

    try:
        q = urlparse.parse_qs(environ["QUERY_STRING"])["q"][0]
    except (KeyError, IndexError) as e:
        logging.warning("Bad request: %r", e)
        return send_json(start_response, "400 Bad Request", [], {"Message": "400 Bad Request: %r" % e})

    results = INDEX.search(q)

    response = {"Nuts": []}
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

    Input:
        {
          "Nut": {
            "Vendor": "aleksi",
            "Name": "test_nut1",
            "Doc": "Package test_nut1 is used to test nut."
          }
        }
    """

    res = check_method(environ, start_response, "POST")
    if res is NO_RESPONSE_SENT:
        res = check_secret_token(environ, start_response)
    if res is not NO_RESPONSE_SENT:
        return res

    data = json.load(environ["wsgi.input"])
    logging.info("Adding %r", data)

    vendor = data["Nut"]["Vendor"]
    name = data["Nut"]["Name"]
    doc  = data["Nut"]["Doc"]
    if doc.lower().startswith("package %s " % name.lower()):
        doc = " ".join(doc.split(" ")[2:])
    if doc.endswith("."):
        doc = doc[:-1]

    # TODO rank
    fields = [
        search.TextField(name="Vendor", value=vendor),
        search.TextField(name="Name", value=name),
        search.TextField(name="Doc",  value=doc),
    ]
    doc_id = "%s/%s" % (vendor, name)
    d = search.Document(doc_id=doc_id, fields=fields)
    INDEX.put(d)

    return send_json(start_response, "201 Created", [], {"Message": "OK"})


def remove(environ, start_response):
    """
    Remove nut from search index.

    Input:
        {
          "Nut": {
            "Vendor": "aleksi",
            "Name": "test_nut1"
          }
        }
    """

    res = check_method(environ, start_response, "POST")
    if res is NO_RESPONSE_SENT:
        res = check_secret_token(environ, start_response)
    if res is not NO_RESPONSE_SENT:
        return res

    data = json.load(environ["wsgi.input"])
    logging.info("Removing %r", data)

    vendor = data["Nut"]["Vendor"]
    name = data["Nut"]["Name"]
    doc_id = "%s/%s" % (vendor, name)
    INDEX.delete(doc_id)

    return send_json(start_response, '204 No Content', [], None)
