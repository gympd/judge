from lib.util import smart_truncate

"""
Finds differences between two strings and returns human friendly message.
It attempts to find all common user errors.
"""


def diff(a: str, b: str, limit=50) -> str:
	a_lines, b_lines = a.splitlines(keepends=True), b.splitlines(keepends=True)

	if len(a_lines) != len(b_lines):
		return f'Náš výstup má {len(a_lines)} riadkov, ale tvoj má {len(b_lines)} riadkov'

	for i in range(len(a_lines)):
		if a_lines[i] != b_lines[i]:
			if a_lines[i].endswith('\n') and not b_lines[i].endswith('\n'):
				return f'Na riadku {i+1} ti chýba koniec riadku (\\n)'

			if b_lines[i].endswith('\n') and not a_lines[i].endswith('\n'):
				return f'Na riadku {i+1} máš navyše (\\n)'

			return f'Náš {i+1}. riadok je: {smart_truncate(a_lines[i], 50)}Ale tvoj riadok je: {smart_truncate(b_lines[i], 50)}'

	return 'Divné, toto by sa nemalo stať... Kontaktuj prosím administrátora testovača.'
