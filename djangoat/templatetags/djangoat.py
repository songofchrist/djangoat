from django import template

from .. import DJANGOAT_DATA

register = template.Library()




# FILTERS
@register.filter
def get(dictionary, key):
    """Retrieves the value of a dictionary entry with the given key.

    In a Django template, to return a value using a static key we would normally use ``{{ DICT.KEY }}``. But if KEY is
    variable, this won't work. With this tag, we may instead use ``{{ DICT|get:VARIABLE_KEY }}`` to get the
    desired value.

    :param dictionary: a dict
    :param key: a key in ``dictionary`` whose value we want to return
    :return: the value corresponding to ``key``
    """
    return dictionary.get(key, None)



@register.filter
def dataf(key, arg=None):
    """Retrieves the value of ``DJANGOAT_DATA[key]`` or, if the value is a callable, the result of the callable.

    The logic behind this filter is the same as that for the ``data`` tag. The only difference is that, because this
    is a filter, it is limited to at most one argument. But also because it is a filter, it can be included directly
    in for loops or chained directly to other filters, which may prove more convenient in certain cases. See the
    ``data`` tag for more on the theory behind this filter.

    :param key: a key in ``DJANGOAT_DATA``
    :param arg: an argument to pass to ``DJANGOAT_DATA[key]`` when its value is callable
    :return: the value of ``DJANGOAT_DATA[key]`` or, if the value is a callable, the result of the callable
    """
    d = DJANGOAT_DATA[key]
    return (d(arg) if arg else d()) if callable(d) else d




# TAGS
@register.simple_tag(takes_context=True)
def data(context, key, *args):
    """Retrieves the value of ``DJANGOAT_DATA[key]`` or, if the value is a callable, the result of the callable.

    To understand the usefulness of this template tag, we first need to understand the problem it solves. Suppose we
    use the queryset below in a number of different views throughout our site.

    ..  code-block:: python

        Book.objects.filter(type='novel')

    We might handle this in a few ways:

    1. Rebuild the queryset in every view that uses it and pass it in context.
    2. Add the queryset to context processors to make it available in all templates.
    3. Create a template tag specifically for this query, so it can be loaded as needed.

    But each of these approaches comes with disadvantages:

    1. Including the queryset in every view means repetitive imports, potential for inconsistency from one view to the next in more complex queries, and wasted processing when the queryset doesn't actually get used.
    2. Including it in context processors circumvents the issues of the first approach but requires rebuilding the queryset on every page load, whether it is used or not, and this adds up when one has hundreds of such queries.
    3. Query-specific template tags address both of these issues, but this approach multiplies template tags unnecessarily and requires us to remember where each tag is located and how to load it, making it less than ideal.

    The ``data`` template tag solves all of these issues by consolidating all such querysets into a single dict,
    which is formed once upon restart and reused thereafter only when actually called via ``data`` within a
    template. To make the queryset above universally accessible to all templates without the need to rebuild it on
    every request, we might place the following in the file where the Book model is declared:

    ..  code-block:: python

        from djangoat import DJANGOAT_DATA

        class Book(models.Model):
            . . .

        DJANGOAT_DATA.update({
            'novels': Book.objects.filter(type='novel')
        })

    To access this within a template, we might do one of the following:

    ..  code-block:: python

        {% load djangoat %}

        {% data 'novels' %}
        {% data 'novels' as good_books %}
        {% data 'novels>' %}

    The first of these will dump the queryset directly into the template as-is. The next will store the queryset in
    the ``good_books`` variable. And the last will inject the queryset into context under the name of its key,
    "novels".

    But what if we have several authors stored in an ``authors`` variable and want to retrieve only novels by those
    authors. In this case, we'd need to store the query as a lambda function, which will only evaluate when called.
    This and any other queryset which would evaluate, such as those that call ``first()`` or ``count()``, **should be
    couched in a lambda function**, so that they can be reused. For example, in the models file, we might update the
    code as follows:

    ..  code-block:: python

        DJANGOAT_DATA.update({
            'novels': Book.objects.filter(type='novel')
            'novels_by_authors': lambda authors: Book.objects.filter(type='novel', authors__in=authors)
        })

    We would then use one of the following to get our results:

    ..  code-block:: python

        {% load djangoat %}

        {% data 'novels_by_authors' authors %}
        {% data 'novels_by_authors' authors as good_books %}
        {% data 'novels_by_authors>' authors %}

    This approach has all of the advantages of registering a separate template tag for every unique queryset or
    callable, but with a lot less headache.

    But what if we want to make use of one value in ``DJANGOAT_DATA`` within another? To do this, we'd do something
    like the following:

    ..  code-block:: python

        DJANGOAT_DATA.update({
            'novels': Book.objects.filter(type='novel')
            'novels_by_authors': lambda authors: Book.objects.filter(type='novel', authors__in=authors)
            'classic_novels': lambda: Book.objects.filter(type='novel', authors__in=DJANGOAT_DATA['classic_authors'])
        })

    Because the ``classic_novels`` queryset exists within a function, it makes no difference when
    ``DJANGOAT_DATA['classic_authors']`` is added. As long as it is added somewhere along the line,
    so that it will be available when needed, we'll be able to retrieve these novels without issue. Using this
    method, we can effectively chain together various queries within ``DJANGOAT_DATA``, which may in certain cases
    prove advantageous.

    The ``data`` tag can accept as many arguments as necessary, but for functions with fewer than two arguments, you
    may also use the ``dataf`` filter below, which operates on the same principle but uses filter syntax

    In summary, this tag represents a way of thinking that results in a particular process. If this process agrees with
    you, the tag may save you a good deal of hassle.

    :param context: the template context
    :param key: a key in ``DJANGOAT_DATA``; if ``key`` ends in ">", then we'll inject the corresponding value into
        ``context`` under the name of this key
    :param args: arguments to pass to ``DJANGOAT_DATA[key]`` when its value is callable
    :return: the value of ``DJANGOAT_DATA[key]`` or, if the value is a callable, the result of the callable or, if
        ``key`` ends in ">", nothing, as the return value will be injected into ``context`` instead
    """
    inject = False
    if key[-1] == '>':
        inject = True
        key = key[:-1]
    d = DJANGOAT_DATA[key]
    v = d(*args) if callable(d) else d
    if inject:
        context[key] = v
        return ''
    return v
