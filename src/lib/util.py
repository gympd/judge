def get_key_value(s: str) -> dict[str, str]:
	out = {}

	for line in s.splitlines():
		(key, value) = line.split(':', 1)
		out[key] = value

	return out

# https://stackoverflow.com/a/250373/19880397
def smart_truncate(content: str, length = 100, suffix = '...'):
	if len(content) <= length:
		return content
	else:
		return content[:length].rsplit(' ', 1)[0]+suffix