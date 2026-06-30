import re


"""
Given a string like "10, 'ten', days=10, days_str='ten'", this regex via "findall" allows us to parse
the string in to an args array and kwargs dict via ``utils.get_args_kwargs_from_string``, resulting in
the following for the given string.
- Args: [10, 'ten']
- Kwargs: {'days': 10, 'days_str': 'ten'}
"""
ARGS_KWARGS_REGEX = re.compile(r'(?:(\w+)=)?([\w\.-]+|"[^"]+?"|\'[^\']+?\')')

DURATION_STRING_REGEX = re.compile(r' *([A-Za-z]+)[,; ]*')