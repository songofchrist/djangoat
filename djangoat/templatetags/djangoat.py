from django import template

register = template.Library()




# FILTERS
@register.filter
def get(dictionary, key):
    """
    Retrieve the value of a dictionary entry with the given key.

    In a Django template, to return a value using a static key we would just use `{{ DICT.KEY }}`. But if KEY is
    variable, we need another solution. With this tag, we may instead write `{{ DICT|get:VARIABLE_KEY }}` to get the
    desired value.

    :param dictionary: a dict
    :param key: a key in `dictionary` whose value we want to return
    :return: the value corresponding to `key`
    """
    return dictionary.get(key, None)



@register.filter
def data(key, arg=None):
    """Return the data associated with "key".

    To set this up, create a file somewhere in your project. In settings, set
    MY_DATA_PATH to the file's location. For example, if the file is in "server/data.py", then this path should be set
    to "server.data". We will import from this path to access data.

    Add to the file the following dictionary:

        MY_DATA = {
            'KEY1': [DATA_1],
            'KEY2': [DATA_2],
            . . .
        }

    The data will then be accessible in templates using a call like the following:

        {{ 'KEY1'|data }}

    Note that if a DATA value is callable, it will be called by the filter when accessed, and the result of the call
    will be passed. This feature may be helpful, for example, if the data is somehow dynamic and needs to be
    recalculated each time it's retrieved or if a queryset needs to be evaluated to get results.

    As an example of usage, let's say we want to make a particular queryset accessible in all templates. We might
    create a context processor and include it there, but this will not work in certain instances, such as calls to
    render_to_string, where this context is not available. Instead, we can assign the queryset to "some_queryset" in
    MY_DATA. This will make it available in all templates everywhere via the following call:

        {{ 'some_queryset'|data }}

    Note that querysets are cached, so we'll want to avoid doing anything when assigning these to MY_DATA that might
    cause them to evaluate prematurely.

    Also, see the "data" tag, which functions similarly but which allows for additional arguments for functions that
    require more than one argument.

    :param key: a key to data stored in MY_DATA at the path specified in MY_DATA_URL
    :param arg: an argument to pass to a callable when retrieved data is a callable
    :return: the data associated with "key"
    """
    d = my_data.MY_DATA.get(key, None)
    return (d(arg) if arg else d()) if callable(d) else d




# TAGS
@register.simple_tag(takes_context=True)
def data(context, key, *args):
    """Return the data associated with "key".

    This tag functions similarly to the "data" filter with two exceptions. Because it is a tag, it can accept as many
    arguments as required. When the data corresponding to "key" is a function, these arguments will be passed to that
    function, allowing for more varied results than the filter. Secondly, a tag can set a template variable using the
    "as" keyword. Say a function returns an object like the following:

        {
            'text': 'My Text',
            'img': 'my_img.jpg'
        }

    We could use the following to access these keys as follows:

        {% data 'key' as result %}
        Text: {{ result.text }}
        Img: {{ result.img }}

    :param key: a key to data stored in MY_DATA at the path specified in MY_DATA_URL
    :param args: arguments to pass to a callable
    :return: the data associated with "key"
    """
    key = key.split('=')
    if len(key) == 1:  # save result in context variable with the name KEY
        var = key = key[0]
    else:  # key has the form "VARIABLE_NAME=KEY"
        var = key[0]
        key = key[1]
    d = my_data.MY_DATA.get(key, None)
    context[var] = d(*args) if callable(d) else d
    return context[var]
