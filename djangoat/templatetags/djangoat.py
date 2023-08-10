import math

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from .. import DJANGOAT_DATA

register = template.Library()




# FILTERS
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
def mod(a, b):
    """Return the result of ``a % b``

    :param a: the number to be divided
    :param b: the number to divide by
    :return: the remainder of the division
    """
    try:
        return a % b
    except:
        return ''



@register.filter
def partition(lst, by=3):
    """Returns a front-weighted list of lists.

    Suppose we have an alphabetized list of X items that we want to divide into Y columns, and we want to maintain
    alphabetic ordering, such that items appear in order when reading from top to bottom and left to right. This tag
    will divide items in this list into sub-lists, which may then looped through to get our results.

    For example, if we have ``items = range(10)``, this tag will divide the list up into the following list of lists:
    ``[[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]``. We may then loop through these as follows to form our columns.

    ..  code-block:: python

        <div class="row">
            {% for ilist in items|partition %}
                <div class="col-sm-4">
                    {% for i in ilist %}<p>{{ i }}</p>{% endfor %}
                </div>
            {% endfor %}
        </div>

    :param lst: a list or object that can be converted to a list
    :param by: how many groups to divide the list into (defaults to 3)
    :return: a front-weighted list of lists
    """
    r = []
    lst = list(lst)
    ll = len(lst)
    s = 0
    while by > 1:
        e = s + math.ceil((ll - s) / by)
        r.append(lst[s:e])
        s = e
        by -= 1
    r.append(lst[s:])
    return r



@register.filter
def seconds_to_units(s):
    """Breaks seconds down into meaningful units.

    If an API gives us the duration of something in seconds, we'll likely want to display this in a form that will be
    more meaningful to the user. This tag divides seconds into its component parts, so you can work with them.

    :param s: seconds
    :return: a dict of the form {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}
    """
    m = h = d = 0
    if s > 59:
        m = int(s / 60)
        s -= m * 60
        if m > 59:
            h = int(m / 60)
            m -= h * 60
            if h > 23:
                d = int(h / 24)
                h -= d * 24
    return {'days': d, 'hours': h, 'minutes': m, 'seconds': s}




# TAGS
@register.simple_tag
def call_function(func, *args):
    """Calls a function that takes arguments.

    ``func`` will need to be passed into context data to be called within a template. Alternatively, if we want a
    function to be available globally, we may instead consider storing a function in ``DJANGOAT_DATA`` and calling
    it via the ``data`` tag.

    :param func: the function we want to call
    :param args: arguments to pass to ``func``
    :return: the return value of the function
    """
    return func(*args)



@register.simple_tag
def call_method(obj, method, *args):
    """Executes an object method that takes arguments.

    :param obj: the object whose ``method`` we want to call
    :param method: the method to call
    :param args: arguments to pass to ``method``
    :return: the return value of the method
    """
    return getattr(obj, method)(*args)



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
    may also use the ``dataf`` filter below, which operates on the same principle but uses filter syntax.

    As for how various querysets and functions make their way into the ``DJANGOAT_DATA``, this is a matter of
    preference. Adding them at the bottom of an app's ``models.py`` file saves importing models but may result in
    circular imports in certain instances. You may instead consider making a ``data.py`` file for each app or a single
    file placed in the project root.

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



@register.simple_tag(takes_context=True)
def pager(context,
          queryset,
          items_per_page=getattr(settings, 'DJANGOAT_PAGER_ITEMS_PER_PAGE', 20),
          previous_page_text=getattr(settings, 'DJANGOAT_PAGER_PREVIOUS_PAGE_TEXT', '« Prev'),
          next_page_text=getattr(settings, 'DJANGOAT_PAGER_NEXT_PAGE_TEXT', 'Next »'),
          show_plus_or_minus=getattr(settings, 'DJANGOAT_PAGER_SHOW_PLUS_OR_MINUS', 3),
          query=getattr(settings, 'DJANGOAT_PAGER_QUERY', 'page')):
    """Returns a widget and queryset based on the current page.

    Suppose we have a queryset ``books``. To enable paging on these objects we would begin by invoking this template
    tag somewhere prior to the display of our book records.

    ..  code-block:: python

        {% pager books %}

    The pager will get total records, calculate starting and ending item numbers, create a basic paging widget, and
    and inject the following variables into the template context:

    - ``pager_queryset``: the provided queryset, sliced according to the current page
    - ``pager_start``: the number of the starting record of ``pager_queryset``
    - ``pager_end``: the number of the ending record of ``pager_queryset``
    - ``pager_total``: the total number of records
    - ``pager``: a widget for navigating pages

    We would then display out book records and the paging widget using something like the following:

    ..  code-block:: python

        {% for book in pager_queryset %}
            <p>{{ book.title }}</p>
        {% endfor %}
        <hr>
        {{ pager }}

    Pagers may be set on an individual basis by passing arguments, and overall defaults may be set by setting the
    following in Django settings:

    - ``DJANGOAT_PAGER_ITEMS_PER_PAGE``
    - ``DJANGOAT_PAGER_NEXT_PAGE_TEXT``
    - ``DJANGOAT_PAGER_PREVIOUS_PAGE_TEXT``
    - ``DJANGOAT_PAGER_QUERY``
    - ``DJANGOAT_PAGER_SHOW_PLUS_OR_MINUS``

    Note that the pager relies on the current request object being present in the template context to retrieve the
    current page from the query string, so be sure to include this in context on any pages where pager is used.

    :param context: the template context
    :param queryset: the queryset through which to page
    :param items_per_page: items to show per page (defaults to 20)
    :param previous_page_text: text to display for previous page (defaults to "« Prev")
    :param next_page_text: text to display for next page (defaults to "Next »")
    :param show_plus_or_minus: how many pages to show left and right of the active page (defaults to 3)
    :param query: the query variable to indicate hte page (defaults to "page")
    """
    try:
        p = int(context['request'].GET.get(query, 1))
    except:
        p = 1
    if p < 1:
        p = 1
    t = queryset.count()
    pt = math.ceil(t / items_per_page)
    ps = (p - 1) * items_per_page
    pe = p * items_per_page
    if pe > t:
        pe = t

    # Build the widget
    w = []
    if p > 1:
        w.append(f'<a href="?{query}={p - 1}">{previous_page_text}</a>')
    rl = p - show_plus_or_minus
    ru = p + show_plus_or_minus
    if rl > 1:
        w.append(f'<a href="?{query}=1">1</a>')
        if rl > 2:
            w.append(' ... ')
    for i in range(1 if rl < 0 else rl, (pt if ru > pt else ru) + 1):
        w.append('<a href="javascript:void(0)" class="active">%d</a>' % p if i == p else '<a href="?{query}={i}">{i}</a>')
    if ru < pt - 1:
        w.append(' ... ')
    if ru < pt:
        w.append(f'<a href="?{query}={pt}">{pt}</a>')
    if pt and p != pt:
        w.append(f'<a href="?{query}={p + 1}">{next_page_text}</a>')
    context.update({
        'pager_start': ps + 1,
        'pager_end': pe,
        'pager_queryset': queryset[ps:pe],
        'pager_total': t,
        'pager': mark_safe('<div class="djangoat-pager">%s%s</div>' % (
            f'<div class="pages">{"".join(w)}</div>',
            f'<div class="showing">Showing {ps} - {pe} of {t}</div>'
        )),
    })
    return ''
