import json
import urlparse

from google.appengine.api import search


INDEX_NAME = "nuts"


def find(environ, start_response):
	"""Search nuts."""

	q = urlparse.parse_qs(environ['QUERY_STRING'])['q'][0]

	results = search.Index(name=INDEX_NAME).search(q)

	start_response('200 OK', [('Content-type', 'application/json')])
	response = []
	for res in results:
		nut = {"Rank": res.rank}
		for f in res.fields:
			nut[f.name] = f.value
		response.append(nut)
	return json.dumps(response)


def add(environ, start_response):
	"""Add nut to search index."""

	data = json.load(environ['wsgi.input'])

	fields = [
		search.TextField(name="Name", value=data["Name"]),
		search.TextField(name="Doc", value=(' '.join(data["Doc"].split(' ')[2:])))  # strip first words "Package <name>"
	]
	# TODO rank
	doc = search.Document(doc_id=data["Name"], fields=fields)

	search.Index(name=INDEX_NAME).put(doc)

	start_response('201 Created', [])
	return ''


def app(environ, start_response):
	"""Simple router."""

	method = environ['REQUEST_METHOD'].upper()
	if method == 'GET':
		return find(environ, start_response)
	elif method == 'POST':
		return add(environ, start_response)
	else:
		start_response('405 Method Not Allowed', [])
		return ''
