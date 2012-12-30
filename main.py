import json
import logging
import urlparse

from google.appengine.api import search


INDEX_NAME = "nuts"


def find(environ, start_response):
	"""Search nuts."""

	if environ['REQUEST_METHOD'].upper() != 'GET':
		start_response('405 Method Not Allowed', [('Allow', 'GET'), ('Content-Type', 'text/plain')])
		return '405 Method Not Allowed: use GET'

	try:
		q = urlparse.parse_qs(environ['QUERY_STRING'])['q'][0]
	except (KeyError, IndexError) as e:
		logging.warning("Bad request: %r", e)
		start_response('400 Bad Request', [('Content-Type', 'text/plain')])
		return '400 Bad Request: %r' % e

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

	if environ['REQUEST_METHOD'].upper() != 'POST':
		start_response('405 Method Not Allowed', [('Allow', 'POST'), ('Content-Type', 'text/plain')])
		return '405 Method Not Allowed: use POST'

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
