import datetime
import math

from django.conf import settings
from django.core.cache import InvalidCacheBackendError, caches
from django.core.cache.utils import make_template_fragment_key
from django import template
from django.template.base import Node, TemplateSyntaxError, VariableDoesNotExist
from django.utils import timezone
from django.utils.safestring import mark_safe

from .. import PAGER

from ..models import CACHE_FRAG_KEYS, CacheFrag
from ..utils import get_args_kwargs_from_string, get_data, get_seconds_from_duration_string

register = template.Library()



# FILTERS
@register.filter
def data(key, arg=None):
    """Retrieves the output of `get_data`_ for ``djangoat.DATA[key]``

    The logic behind this filter is the same as that for the `data tag`_. The only difference is that, because this
    is a filter, it's limited to at most one argument. But also, because it's a filter, it can be included directly
    in for loops or chained directly to other filters, which may prove more convenient in certain cases. See the
    `data tag`_ for more on the theory behind this filter.

    :param key: a key in ``djangoat.DATA``
    :param arg: an argument to pass to the function referenced by ``djangoat.DATA[key]`` (otherwise, it's ignored)
    :return: the output of `get_data`_ for ``djangoat.DATA[key]``
    """
    return get_data(key, *([arg] if arg else []))



@register.filter
def div(a, b):
    """Returns the integer result of ``a % b``.

    Note that this method is meant to aid in presentation, not for complex mathematical operations.
    Thus, we'll cast both numbers to integers prior to evaluating and will return the result rounded
    down to the nearest integer.

    :param a: the dividend
    :param b: the divisor
    :return: the integer result of ``a / b``
    """
    return int(int(a) / int(b))


@register.filter
def get(dictionary, key):
    """Retrieves the value of a dictionary entry with the given key.

    In a Django template, to return a value using a static key we would normally use :django:`{{ DICT.KEY }}`. But
    if KEY is variable, this won't work. With this tag, we may instead use :django:`{{ DICT|get:VARIABLE_KEY }}` to
    get the desired value.

    :param dictionary: a dict
    :param key: a key in ``dictionary`` whose value we want to return
    :return: the value corresponding to ``key``
    """
    return dictionary.get(key, None)



@register.filter
def index(lst, index):
    """Retrieve the list value at the given index.

    :param lst: a list (or other iterable)
    :param index: the index of the item to retrieve
    :return: the corresponding value (or an empty string if no such index exists)
    """
    try:
        return lst[index]
    except:
        return ''



@register.filter
def mod(a, b):
    """Returns the integer result of ``a % b``.

    Note that this method is meant to aid in presentation, not for complex mathematical operations.
    Thus, we'll cast both numbers to integers prior to evaluating. Also, if you're using this within
    a loop to do something every ``b`` iterations, consider using the builtin ``divisibleby`` filter
    instead (i.e. ``{% if a|divisibleby:b %} . . . {% endif %}``). Use this filter only when the
    value of the remainder matters.

    :param a: the dividend
    :param b: the divisor
    :return: the remainder of ``a / b``
    """
    return int(a) % int(b)



@register.filter
def mul(a, b):
    """Returns the integer result of ``a * b``.

    Note that this method is meant to aid in presentation, not for complex mathematical operations.
    Thus, we'll cast both numbers to integers prior to evaluating.

    :param a: a number
    :param b: a second number
    :return: the result of ``a * b``
    """
    return int(a) * int(b)



@register.filter
def partition(items, groups=3):
    """Returns a front-weighted list of lists.

    Suppose we have an alphabetized list of X items that we want to divide into Y columns, and we want to maintain
    alphabetic ordering, such that items appear in order when reading from top to bottom, left to right. This tag
    will divide items in this list into sub-lists, which may then looped through to get our results.

    For example, if we have :python:`items = range(10)`, this tag will divide the list up into the following list of
    lists: :python:`[[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]`. We may then loop through these as follows to form our
    columns.

    ..  code-block:: django

        <div class="row">
            {% for ilist in items|partition %}
                <div class="col-sm-4">
                    {% for i in ilist %}<p>{{ i }}</p>{% endfor %}
                </div>
            {% endfor %}
        </div>

    :param items: a list or object that can be converted to a list
    :type items: list, tuple, queryset, etc.
    :param groups: how many groups to divide the list into
    :type groups: int
    :return: a front-weighted list of lists
    """
    r = []
    items = list(items)
    ll = len(items)
    s = 0
    while groups > 1:
        e = s + math.ceil((ll - s) / groups)
        r.append(items[s:e])
        s = e
        groups -= 1
    r.append(items[s:])
    return r



@register.filter
def seconds_to_units(seconds):
    """Breaks seconds down into meaningful units.

    If we have the duration of something in seconds, we'll likely want to display this in a form that will be
    more meaningful to the user. This tag divides seconds into its component parts as shown below:

    ..  code-block:: python

        {
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0
        }

    :param seconds: total seconds to break into different units
    :type seconds: int
    :return: a dict of meaningful time units
    """
    m = h = d = 0
    if seconds > 59:
        m = int(seconds / 60)
        seconds -= m * 60
        if m > 59:
            h = int(m / 60)
            m -= h * 60
            if h > 23:
                d = int(h / 24)
                h -= d * 24
    return {'days': d, 'hours': h, 'minutes': m, 'seconds': seconds}



@register.filter
def split(string, delimiter=','):
    """Derive a list from a delimited string.

    :param string: the string to split
    :param delimiter: the string to split on (defaults to a comma)
    :return: a list
    """
    return string.split(delimiter)



@register.filter
def sub(a, b):
    """Returns the integer result of ``a * b``.

    Note that this method is meant to aid in presentation, not for complex mathematical operations.
    Thus, we'll cast both numbers to integers prior to evaluating.

    :param a: a number
    :param b: a second number
    :return: the result of ``a * b``
    """
    return int(a) - int(b)



@register.filter
def thumb_html(field_file, key):
    return field_file.get_thumb_html(key)



@register.filter
def thumb_url(field_file, key):
    return field_file.get_thumb_url(key)



@register.filter
def timedelta(date, delta_string):
    """Add or subtract a delta to a datetime.

    For example, both of the following add 30 days to "date"::

        {{ date|timedelta:'30' }}
        {{ date|timedelta:'days=30' }}

    And both of the following subtract 30 days from "date"::

        {{ date|timedelta:'-30' }}
        {{ date|timedelta:'-days=30' }}

    We can also work in a combination of units::

        {{ date|timedelta:'days=3, weeks=7' }}
        {{ date|timedelta:'days=2, hours=12' }}
        {{ date|timedelta:'hours=5, minutes=30' }}

    A leading "-" will result in the delta being subtracted from "date". Otherwise, it will be added.

    :param date: the date to which the delta should be added
    :param delta_string: a delta string, expressing the same arguments as expected by timedelta
    :return: the resultant date
    """
    pm = 1
    if delta_string[0] == '-':
        pm = -1
        delta_string = delta_string[1:]
    args, kwargs = get_args_kwargs_from_string(delta_string)
    return date + pm * datetime.timedelta(*args, **kwargs)




# SIMPLE TAGS
@register.simple_block_tag(takes_context=True)
def append(context, content, list_name):
    """Appends block content to the specified list.

    Given a list of ``list_name``, append block ``content`` to that list. If the list, doesn't yet exist, create it
    and then append it. This is useful if we need to render a series of separate template fragments and then pass
    them as a list to another template tag or template.

    :param context: template context
    :param content: the rendered content of the block tag
    :param list_name: the list to which to append ``content`` (will be created if it doesn't exist)
    :return: an empty string
    """
    context.setdefault(list_name, []).append(content)
    return ''



@register.simple_tag(takes_context=True)
def data(context, key, *args, **kwargs):
    """Retrieves the output of `get_data`_ for ``djangoat.DATA[key]`` and either displays it or injects it into context.

    To understand the usefulness of this template tag, we first need to understand the problem it solves. Suppose we
    use the queryset below in a number of different views throughout our site.

    ..  code-block:: python

        Book.objects.filter(type='novel')

    We might handle this in a few ways:

    1. Rebuild the queryset in every view that uses it and pass it in context.
    2. Add the queryset to context processors to make it available in all templates.
    3. Create a template tag specifically for this query, so it can be loaded as needed.

    But each of these approaches comes with disadvantages:

    1. Including the queryset in every view means repetitive imports, potential for inconsistency from one view to
       the next in more complex queries, and wasted processing when the queryset doesn't actually get used.
    2. Including it in context processors circumvents the issues of the first approach but requires rebuilding the
       queryset on every page load, whether it's used or not, and this adds up when we have hundreds of such queries.
    3. Query-specific template tags address both of these issues, but this approach multiplies template tags
       unnecessarily and requires us to remember where each tag is located and how to load it, making it less than
       ideal.

    This template tag solves all of these issues by consolidating all such querysets into a single, globally
    accessible dict, which is formed once upon restart and reused thereafter only when actually called by this tag.
    To make the queryset above universally accessible to all templates without the need to rebuild it on every
    request, we might place the following in the file where the Book model is declared:

    ..  code-block:: python

        from djangoat import DATA

        class Book(models.Model):
            . . .

        DATA.update({
            'novels': Book.objects.filter(type='novel')
            'novels_safe': lambda: Book.objects.filter(type='novel')
        })

    To access this within a template, we might do one of the following:

    ..  code-block:: django

        {% load djangoat %}

        {% data 'novels' %}
        {% data 'novels' as novels %}
        {% data 'novels>' %}

    The first of these will dump the queryset directly into the template as-is. The next will store the queryset in
    the ``novels`` variable, so it can be referenced elsewhere in the template. And the last, which appends ">" to
    the end of the key, is a shorthand for the previous example and results in output being injected into context
    under the name of the preceding key, here "novels".

    Note that, because "novels" here is a queryset, its results will be cached with every call and stored in memory
    until the next call, which may start eating up memory when we're dealing with large querysets. To avoid this,
    we'll place the queryset within a lamda function, as seen in "novels_safe" above. To ensure no side effects,
    we'll use this form for "novels" going forward.

    Now what if we have several authors stored in an ``authors`` variable and want to retrieve only novels by those
    authors. In this case, we'd need to provide an ``authors`` argument for our lambda function, so that we can pass
    this to the queryset. For example, we might update the code as follows:

    ..  code-block:: python

        DATA.update({
            'novels': lambda: Book.objects.filter(type='novel')
            'novels_by_authors': lambda authors: Book.objects.filter(type='novel', authors__in=authors)
        })

    We would then use one of the following to get our results:

    ..  code-block:: django

        {% load djangoat %}

        {% data 'novels_by_authors' authors %}
        {% data 'novels_by_authors' authors as novels_by_authors %}
        {% data 'novels_by_authors>' authors %}

    This would inject results into the template directly or, in the latter two cases, assign results to a
    "novels_by_authors" variable. This approach has all of the advantages of registering a separate template tag
    for every unique queryset or callable, but with a lot less headache.

    But what if we want to reference one value in ``djangoat.DATA`` within another? To do this, we'd do something
    like the following:

    ..  code-block:: python

        from djangoat.utils import get_data

        DATA.update({
            'novels': Book.objects.filter(type='novel')
            'novels_by_authors': lambda authors: Book.objects.filter(type='novel', authors__in=authors)
            'novels_by_authors_alt': lambda authors: get_data('novels').filter(authors__in=authors)
        })

    Here we see that "novels_by_authors_alt" builds upon "novels" by using the `get_data`_ function to retrieve the
    value of the "novels" queryset and then applying an "authors" filter to it before rendering its output. This
    allows us to chain things together, reducing repetition of code. Note that the value referenced by `get_data`_
    can be any key in DATA referenced throughout our project. As long as it's registered somewhere, it's permissible.
    This is especially helpful in alleviating concerns over circular imports.

    This tag will prove especially useful in the context of template caching. For example, consider the following:

    ..  code-block:: django

        <p>Uncached material.</p>
        {% cache 123 test %}
            {% data 'novels_by_authors>' 'authors'|data %}
            {% for novel in novels_by_authors %}
                {{ novel.title }} by {{ novel.author }}<br>
            {% endfor %}
        {% endcache %}

    We see here a call to the data tag, whose output we expect to be injected into context under the variable name
    "novels_by_authors". The corresponding function in DATA requires an ``authors`` argument, which we retrieve via
    a call to ``'authors'|data``, which we'll assume is elsewhere specified and returns authors instances. We then
    process this data via a loop. The results are then cached. The next time this page is hit, it populates from
    the cache, so these querysets never have to be built. And when we do need them, we can call them directly from
    the template, keeping the associated view that much cleaner.

    Note that the `data tag`_ can accept as many arguments as necessary, but for functions with fewer than two
    arguments, you may also use the `data filter`_, which operates the same in principle but uses filter syntax to
    retrieve output.

    As for how various querysets and functions make their way into the ``djangoat.DATA``, this is a matter of
    preference. Adding them at the bottom of an app's ``models.py`` file saves importing models but may result in
    circular imports in certain instances where different apps' DATA entries need to reference each other's models.
    You may instead consider making a single ``data.py`` file alongside project settings, so that any models
    needed to build DATA entries can be imported without danger of circular imports.

    In summary, this tag is intended to do the following:
    * Encourage centralization of commonly used data into a single DATA dict
    * Make this data globally available throughout the project via the `get_data`_ function` (used by tags to
      retrieve data)
    * Provide a way of injecting this data directly into templates, so that it's only accessed when needed

    :param context: the template context
    :type context: dict
    :param key: a key in ``djangoat.DATA``; if ``key`` ends in ">", then we'll inject the corresponding value into
        ``context`` under the name of this key
    :type key: str
    :param args: arguments to pass to ``djangoat.DATA[key]`` when its value is callable (otherwise, args are ignored)
    :param kwargs: keyword arguments to pass to ``djangoat.DATA[key]`` when its value is callable (otherwise, kwargs
        are ignored)
    :return: the output of `get_data`_ for ``djangoat.DATA[key]`` or an empty string when a variable is specified
    """
    inject = False
    if key[-1] == '>':
        inject = True
        key = key[:-1]
    v = get_data(key, *args, **kwargs)
    if inject:
        context[key] = v
        return ''
    return v



@register.simple_tag
def method(obj, meth, *args, **kwargs):
    """Executes an object method that takes arguments.

    Given an instance ``obj``, we'll call its method ``meth``, pass it any args or kwargs provided in the tag, and
    display the output. For example, if we have a ``post`` object we might pass three arbitrary arguments to its
    "example_method" as follows:

    ..  code-block:: django

        {% method post 'example_method' arg1 arg2 arg3 %}

    :param obj: the object whose method we want to call
    :param meth: the name of method to call
    :type meth: str
    :param args: arguments to pass to ``meth``
    :param kwargs: keyword arguments to pass to ``meth``
    :return: the return value of the method
    """
    return getattr(obj, meth)(*args, **kwargs)



@register.simple_tag(takes_context=True)
def pager(context,
          queryset,
          items_per_page=PAGER['items_per_page'],
          plus_or_minus=PAGER['plus_or_minus']):
    """Returns a widget and queryset based on the current page.

    Suppose we have a queryset ``books``. To enable paging on these objects we would begin by invoking this template
    tag somewhere just prior to the display of our book records.

    ..  code-block:: django

        {% pager books %}

    The pager will get total records, calculate starting and ending item numbers, create a basic paging widget, and
    and inject the following variables into the template context:

    - ``pager_queryset``: the provided queryset, sliced according to the current page
    - ``pager_start``: the index of the starting record of ``pager_queryset``
    - ``pager_end``: the index of the ending record of ``pager_queryset``
    - ``pager_total``: the total number of records in this queryset
    - ``pager``: a widget for navigating pages

    We would then display our book records and the paging widget. A list page template might look something like the
    following:

    ..  code-block:: django

        {% pager books %}
        <h1>Books To Read</h1>
        <hr>
        {% for book in pager_queryset %}
          <p><a href="{{ book.get_relative_url }}">{{ book.title }}</a></p>
        {% endfor %}
        <hr>
        {{ pager }}

    Widget defaults are available in ``djangoat.PAGER`` and may be altered by updating this dict, which
    takes the form below:

    ..  code-block:: python

        PAGER = {
            'items_per_page': 20,   # the number of items to show on each page
            'next_text': 'Next »',  # text prompting the user to go to the next page
            'param': 'page',        # the query string parameter containing the current page
            'plus_or_minus': 3,     # how many page links to display to the left and right of the current page
            'prev_text': '« Prev',  # text prompting the user to go to the previous page
            'throttle_at': None     # remove page links beyond this page number to discourage crawling older material
        }

    Note that this tag relies on the current request object being present in the template context to retrieve the
    current page from the query string, so be sure to include this in context on any pages where pager is used.

    :param context: the template context
    :param queryset: the queryset through which to page
    :param items_per_page: items to show per page (defaults to 20)
    :param plus_or_minus: how many links to display on either side of the current page (defaults to 3)
    """
    # Calculate item start / end based on page
    param = PAGER['param']
    throttle_at = PAGER['throttle_at']
    g = context['request'].GET
    cqs = '&'.join([f'{k}={g[k]}' for k in g.keys() if k != param])  # the current query string, excluding the page param
    if cqs:
        cqs += '&'
    total_items = queryset.count()
    total_pages = math.ceil(total_items / items_per_page)
    try:
        page = int(g.get(param, 1))
        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages
    except:
        page = 1
    items_start = (page - 1) * items_per_page + 1
    items_end = page * items_per_page
    if items_end > total_items:
        items_end = total_items

    # Build the widget
    widget = []
    if page > 1:
        widget.append(f'<a href="?{cqs}{param}={page - 1}">{PAGER["prev_text"]}</a>')
    page_low = page - plus_or_minus
    page_high = page + plus_or_minus
    if throttle_at and page_high > throttle_at:  # when throttled, adjust the upper limit for linked pages
        page_high = throttle_at
    if page_low > 1:  # ensure we have a link to page one
        widget.append(f'<a href="?{cqs}{param}=1">1</a>')
        if page_low > 2:
            widget.append(' ... ')
    for i in range(1 if page_low < 1 else page_low, page):
        widget.append(f'<a href="?{cqs}{param}={i}">{i}</a>')  # pages preceding the current page
    widget.append(f'<a href="javascript:void(0)" class="active">{page}</a>')  # the current page
    for i in range(page + 1, (total_pages if page_high > total_pages else page_high) + 1):
        widget.append(f'<a href="?{cqs}{param}={i}">{i}</a>')  # pages after the current page
    if not throttle_at:  # only show the final page link when not throttling is disabled
        if page_high < total_pages - 1:
            widget.append(' ... ')
        if page_high < total_pages:
            widget.append(f'<a href="?{cqs}{param}={total_pages}">{total_pages}</a>')
    if total_pages and page != total_pages:
        widget.append(f'<a href="?{cqs}{param}={page + 1}">{PAGER["next_text"]}</a>')
    context.update({
        'pager': mark_safe(
            '<div class="dg-pager">'
              f'<div class="pages">{"".join(widget)}</div>'
              f'<div class="showing">Showing {items_start} - {items_end} of {total_items}</div>'
            '</div>'
        ),
        'pager_start': items_start + 1,
        'pager_end': items_end,
        'pager_queryset': queryset[items_start - 1:items_end],
        'pager_total': total_items,
    })
    return ''




# CACHE TAGS
class CacheFragNode(Node):
    """
    This class is modeled after the Django's built-in CacheNode class:
    https://github.com/django/django/blob/main/django/templatetags/cache.py

    Modifications have been made to enable the following:
    * Accommodate user / site cache tags
    * Create CacheFrag records in the database
    * Keep CacheFrag ``date_set`` and ``duration`` fields up to date
    * Make cache entries filterable and searchable in the admin based on name, user, site, and args
    * Make cache entries clearable via their corresponding CacheFrag record
    * Allow clearing of all records in a CacheFrag queryset via the ``clear`` method
    * Enable clearing of all cache fragments encountered within the current request
    """
    def __init__(self, nodelist, expire_time_var, fragment_name, vary_on, cache_name, tag, user, site):
        self.nodelist = nodelist
        self.expire_time_var = expire_time_var
        self.fragment_name = fragment_name
        self.vary_on = vary_on
        self.cache_name = cache_name
        self.tag = tag
        self.user = user
        self.site = site

    def render(self, context):
        site_id = user_id = value = None
        try:
            request = context['request']
        except:
            raise KeyError('"%s" tag requires the "request" object to be included in template context' % self.tag)
        if self.user:  # the usercache or usersitecache tag
            user_id = request.user.id
            if not user_id:
                raise Exception('"%s" tag is attempting to cache content for an unauthenticated user' % self.tag)
        if self.site:  # the sitecache or usersitecache tag
            try:
                site_id = settings.SITE_ID
            except:
                raise AttributeError('"%s" tag requires Django\'s Sites framework to be installed' % self.tag)
        try:  # retrieve and save the string representation of the desired duration
            duration = expire_time = self.expire_time_var.resolve(context)
        except VariableDoesNotExist:
            raise TemplateSyntaxError('"%s" tag got an unknown variable: %r' % (self.tag, self.expire_time_var.var))
        if expire_time is not None:
            try:  # the number of seconds in the desired duration
                if isinstance(expire_time, str):
                    expire_time = int(expire_time) if expire_time.isnumeric() else get_seconds_from_duration_string(expire_time)
            except (ValueError, TypeError):
                raise TemplateSyntaxError('"%s" tag got an invalid timeout value: %r' % (self.tag, expire_time))
        if self.cache_name:
            try:
                cache_name = self.cache_name.resolve(context)
            except VariableDoesNotExist:
                raise TemplateSyntaxError('"%s" tag got an unknown variable: %r' % (self.tag, self.cache_name.var))
            try:
                fragment_cache = caches[cache_name]
            except InvalidCacheBackendError:
                raise TemplateSyntaxError('Invalid cache name specified for cache tag: %r' % cache_name)
        else:
            try:
                fragment_cache = caches['template_fragments']
            except InvalidCacheBackendError:
                fragment_cache = caches['default']
        vary_on = [var.resolve(context) for var in self.vary_on]
        key_tuple = self.fragment_name, '|'.join(str(a) for a in vary_on) if self.vary_on else None, user_id, site_id  # a tuple unique to the key we expect from "make_template_fragment_key"
        cache_key = CACHE_FRAG_KEYS.get(key_tuple, None)  # a tuple of the form (CACHE_KEY, DURATION_STRING)
        if cache_key:  # we already have a CacheFrag record for this combination of arguments but may need to update its duration
            cache_key, prev_duration = cache_key
            if prev_duration != duration:  # the duration of this block has changed in the code; update the record to reflect this change
                CacheFrag.objects.filter(key=cache_key).update(date_set=timezone.now(), duration=duration)
                CACHE_FRAG_KEYS[key_tuple] = (cache_key, duration)
                fragment_cache.delete(cache_key)  # refresh cached content, so that it matches the CacheFrag record
        else:  # create a unique key for this combination of arguments and generate a new CacheFrag record
            cache_key = make_template_fragment_key(self.fragment_name, vary_on + [user_id, site_id])
            cf, created = CacheFrag.objects.get_or_create(key=cache_key, name=self.fragment_name)
            if created:
                cf.args = key_tuple[1]
                cf.user_id = user_id
                cf.site_id = site_id
                cf.date_set = timezone.now()
                cf.duration = duration
                cf.save()
            CACHE_FRAG_KEYS[key_tuple] = (cache_key, duration)
        if request.djangoat.cache_refresh:  # clear this and any other fragments encountered on this request
            fragment_cache.delete(cache_key)
        else:
            value = fragment_cache.get(cache_key)
        if value is None:
            value = self.nodelist.render(context)
            fragment_cache.set(cache_key, value, expire_time)
            request.djangoat.cache_keys_set.append(cache_key)  # we'll update the date_set of corresponding records just before sending the response
        return value


def _get_cache_frag_node(parser, token, tag, user=False, site=False):
    """
    This function is modeled after django.templatetags.do_cache function but includes, endtag, site and user
    arguments to accommodate the User and Site tag variations below.
    """
    # This method is the equivalent of django.templatetags.do_cache but includes site and user arguments
    nodelist = parser.parse(('end' + tag,))
    parser.delete_first_token()
    tokens = token.split_contents()
    if len(tokens) < 3:
        raise TemplateSyntaxError("'%r' tag requires at least 2 arguments." % tokens[0])
    if len(tokens) > 3 and tokens[-1].startswith('using='):
        cache_name = parser.compile_filter(tokens[-1][len('using='):])
        tokens = tokens[:-1]
    else:
        cache_name = None
    return CacheFragNode(
        nodelist,
        parser.compile_filter(tokens[1]),  # expiry
        tokens[2],  # fragment_name
        [parser.compile_filter(t) for t in tokens[3:]],  # vary on
        cache_name,
        tag,
        user,
        site
    )


@register.tag
def cache(parser, token):
    """Creates a `CacheFrag`_ record, if needed, and returns cached content.

    This tag expands upon the built-in Django
    `template cache tag <https://docs.djangoproject.com/en/dev/topics/cache/#template-fragment-caching>`__. Like the
    built-in tag, its first two arguments are the seconds to expiration (given as an integer, a variable, or a time
    string) and fragment name, and everything thereafter distinguishes one fragment of a particular name from the next.

    Unlike the built-in cache tag, this tag records each unique fragment, along with its unique key, in the database,
    so that it can be accessed and cleared on demand. For example, if we've cached the nav bar on a particular site
    and want to refresh just that fragment, rather than clearing the entire cache, we can use the `CacheFrag`_ admin
    to clear only that one fragment.

    Also, because the fragment name and other distinguishing arguments are recorded in the database, we can query on
    them to clear or delete all fragments having a particular name, associated with a particular user or site, or
    containing a particular argument. This is especially helpful when certain objects are updated in the database
    that stand to affect cached content.

    For example, suppose the links in the nav bar are updatable within the admin. If a staff member decides to change
    the title or url of a link or the order in which the links appear, we'll want to update the nav bar ASAP. Rather
    than waiting for the nav bar cache to expire, we can query the associated fragment within the ``save_model`` admin
    method associated with nav bar management and clear it immediately, so that it can be repopulated with the
    up-to-date links.

    The following demonstrates how this code might be used:

    ..  code-block:: django

        {% cache 12345 FRAG_NAME "arg1" "arg2" "arg3" %}
            Cached content
        {% endcache %}

    For this call, a `CacheFrag`_ record will be created with the ``name`` FRAG_NAME and an ``args`` value of
    "arg1|arg2|arg3". The ``user`` and ``site_id`` fields of the fragment record will be null.

    The cache expiry can also be set using any time string that can be parsed by `get_seconds_from_duration_string`_.
    For example, we might use the following:

    ..  code-block:: django

        {% cache '3d10h30m' FRAG_NAME "arg1" "arg2" "arg3" %}
            Cached content
        {% endcache %}

    Or we could write "3d;10h;30m", or "30m, 10h, 3d", or "3 days, 10 hours, 30 minutes", or many other variations.
    This human-readable time formatting makes the expiry much easier to understand and is far preferable to having
    to calculate seconds for each new fragment.

    Regardless of whether the time is denoted by a number or by a date string, we will store this value in the
    associated CacheFrag record and update it whenever it changes. From this, we can also calculate the expiration
    date of the fragment. Having these displayed in the admin will further inform users as to what they can expect
    from any particular fragment.

    **Note that the request object MUST be included in template context as "request", either via a context processor
    or by inclusion from a view.** We use the request object as follows:
    * When "request.djangoat.cache_refresh" is set to True, we'll refresh all cache fragments encountered in the
      current request, ensuring the user sees the most up-to-date content
    * We'll record any fragments whose ``date_set`` needs updating in "request.djangoat.cache_keys_set" and will
      update this field on all associated records just prior to sending the response
    * We'll use it to access the user in the ``usercache`` and ``usersitecache`` cache tag variants

    Cache fragments can be cleared in any of the following ways:
    * Allowing the fragment to reach its expiry
    * Filtering and manually selecting records within the admin (see `djangoat.admin.CacheFragAdmin </djangoat.admin.CacheFragAdmin.html>`)
    * Searching for records via a queryset (i.e. CacheFrag.objects.filter(user__is_staff=True).clear())
    * Setting ``request.djangoat.cache_refresh`` to True prior to rendering a view

    One might use a CacheFrag queryset to clear fragments if, for example, every time a post is updated, we want to
    clear certain fragments associated with that post and nothing else. Querysets allow us to programmatically target
    those particular fragments. Setting the cache refresh might be useful if we're viewing a particular page as an
    admin and want all fragments on that page refreshed, so that we can see the most up-to-date version of it.
    """
    return _get_cache_frag_node(parser, token, 'cache')


class MapNode(Node):
    def __init__(self, item_var, items_iterable, new_list_name, nodelist):
        self.item_var = item_var
        self.items_iterable = items_iterable
        self.new_list_name = new_list_name
        self.nodelist = nodelist

    def render(self, context):
        new_list = []
        for item in self.items_iterable.resolve(context, ignore_failures=True):
            context[self.item_var] = item
            new_list.append(self.nodelist.render(context))
        context[self.new_list_name] = new_list
        return ''

@register.tag('map')
def do_map(parser, token):
    """Formats list items using the template fragment in the tag block and outputs the resulting list.

    This tag is meant to emulate the python ``map`` function, accepting a list of X items, rendering them
    one at a time using the template fragment within the map block, and saving the result into a template
    variable, which can then be passed on to another template tag or template.

    For example, suppose we have a list of users and want to wrap each item in the list in HTML. We might
    do this in python as follows before passing it into template context::

        wrapped_users = map(lambda user: f"<div><b>{user.name}</b> from {user.city} ({user.age})</div>", users)

    Or we could do it directly inside a Django template as follows::

        {% map user in users as wrapped_users %}
            <div><b>{{ user.name }}</b> from {{ user.city }} ({{ user.age }})</div>
        {% endmap %}

    Either way, ``wrapped_users`` will now contain one HTML formatted item for each user in ``users``.

    The syntax here is similar to that of a for loop, but unlike the for loop, which renders output in place,
    an "as" clause is required here to indicate the name of the context variable in which the resulting list
    should be stored. This variable will then be injected into context for later use.
    """
    error = False
    try:
        _, item_var, in_kw, items_iterable, as_kw, new_list_name = token.split_contents()
        if in_kw != 'in' or as_kw != 'as':
            error = True
    except:
        error = True
    if error:
        raise TemplateSyntaxError("'map' tags take the form {%% map ITEM_VAR in ITEMS_ITERABLE"
                                  " as NEW_LIST_NAME %%}; you entered {%% %s %%}" % token.contents)
    nodelist = parser.parse(('endmap',))
    parser.delete_first_token()
    items_iterable = parser.compile_filter(items_iterable)
    return MapNode(item_var, items_iterable, new_list_name, nodelist)



class VarNode(template.Node):
    def __init__(self, context):
        self.kwargs = context

    def render(self, context):
        for k, v in self.kwargs.items():
            context[k] = v.resolve(context)
        return ''

@register.tag('var')
def do_var(parser, token):
    """Assign a value to a variable, which will persist within the current scope.

    As with the ``with`` tag, this tag expects one or more variable-value pairs. But rather
    than limiting these variables to being used within a tag block, this tag simply overwrites
    the like-named context variable with the given value. For example, ``{% var one=1 two=2 %}``
    will set the "one" variable to a value of 1 and "two" to a value of 2. This gives us more
    freedom with our logic. For example, suppose we have the following:

    .. code-block::
        {% if worked %}
            {% include 'my/output/template.html' with msg='success' mood='happy' %}
        {% else %}
            {% include 'my/output/template.html' %}
        {% endif %}

    We can condense this to the following:

    .. code-block::
        {% if worked %}{% var msg='success' mood='happy' %}{% endif %}
        {% include 'my/output/template.html' %}

    Also unlike the ``with`` tag, later variables can make use of previous ones within the same
    assignment. For example:

    .. code-block::
        {% var a=2 b=3 c=a|mul:b %}

    "c" here will equal 6.

    :return: an empty string
    """
    return VarNode(template.base.token_kwargs(token.split_contents()[1:], parser))



@register.tag('new_append')
def do_append(parser, token):
    """Append or assign the rendered blocks to the given list, creating the list if it doesn't yet exist.

    Suppose we have a template that is expecting a list of items, some of which we expect to include HTML. The
    standard approach here would be to build this list in a view and then pass it in context. But this is less
    than ideal. Ideally, we'd construct the list within the template itself just prior to passing it to the
    template, so that it's immediately clear what we're passing to the template and in what format. This tag
    makes this possible.

    For example, suppose we have a template that expects a list of two unequal columns, the first containing a
    photo and the second containing associated post info. Instead of building this list within the view for each
    post, we can build it directly within the template as follows:

    .. code-block::django
        {% for post in posts %}
            {% list 'col_html_list' append %}
                <tr><td class="photo"><img src="{{ post.image.url }}"></td></tr>
            {% append %}
                <tr><td class="title">{{ post.title }}</td></tr>
                <tr><td class="body">{{ post.body }}</td></tr>
            {% endlist %}
            {% include 'newsletters/layouts/columns_variable_width.html' column_trs=col_html_list column_widths='180,380' %}
        {% endfor %}

    This will result in "col_html_list" being created, filled, and passed into the column template all within a
    few lines of easily understandable code.

    Note that once a list exists within a scope, items will continue to be appended to the existing list unless
    a "clear" keyword is added to the initial tag. For example, suppose we have the following:

    .. code-block::django
        {% list 'test' append %}One{% append %}Two{% append %}Three{% endlist %}
        {% list 'test' clear append %}Four{% append %}Five{% endlist %}
        Result: {{ test }}

    The resulting value of "test" will be ['Four', 'Five'] because the list ['One', 'Two', 'Three'] is cleared
    just prior to appending these final two values.

    Finally, if only a particular index needs to be overwritten, we can use "set INDEX" in place of "append". Say,
    for example, we have an existing list of five items and only want to alter the third and fourth items. We could
    use the following:

    .. code-block::django
        {% list 'test' set 2 %}
            Item #3 at index #2
        {% set 3 %}
            Item #4 at index #3
        {% endlist %}

    This will overwrite the items at indices 2 and 3 with the rendered content of each subsequent block.

    Note that only the operation specified in the initial tag may be performed on each subsequent block. If
    "append" is used in the initial tag, "set" cannot be used thereafter, and vice-versa.
    """
    _append, _clear = _op = _set, clear = error = i = name = False
    bits = token.split_contents()[1:]
    if len(bits) == 2:
        name, _op = bits  # append
    elif len(bits) == 3:
        if bits[1] == 'clear':
            name, _clear, _op = bits  # append
        else:
            name, _op, i = bits  # set
    elif len(bits) == 4:
        name, _clear, _op, i = bits  # set
    else:
        error = True
    if error or (_clear and _clear != 'clear') or (_op == 'append' and i) or (_op == 'set' and (not i or not i.isnumeric())):
        raise TemplateSyntaxError('Opening "list" tags take the form {%% list LIST_NAME [clear] append %%} or'
                                  ' {%% list LIST_NAME [clear] set INDEX %%}; you entered {%% %s %%}' % token.contents)

    if _clear == 'clear':
        clear = True




    else:
        error = True
    if _append != 'append' or _clear != 'clear':
        error = True
    if error:
        raise TemplateSyntaxError('Opening "list" tags take the form {%% list LIST_NAME [clear] append %%} or'
                                  ' {%% list LIST_NAME [clear] set INDEX %%}; you entered {%% %s %%}' % token.contents)
    key_nodelists = [(key[1:-1], parser.parse(('set', 'enddict')))]  # a list of (DICT_KEY, NODELIST) tuples
    token = parser.next_token()
    while token.contents.startswith('set'):
        bits = token.split_contents()
        if len(bits) != 2:
            raise TemplateSyntaxError('Post-opening "list" tags take the form {%% append %%} or {%% set INDEX %%};'
                                      ' you entered {%% %s %%}' % token.contents)
        key_nodelists.append((bits[1][1:-1], parser.parse(('set', 'enddict'))))
        token = parser.next_token()
    return ListNode(name[1:-1], key_nodelists, clear)



class DictNode(template.Node):
    def __init__(self, name, key_nodelists, clear):
        self.name = name
        self.key_nodelists = key_nodelists  # takes the form (KEY, NODELIST)
        self.clear = clear

    def render(self, context):
        dct = context.setdefault(self.name, {})
        if self.clear and dct:  # clear prior to making new assignments
            dct.clear()
        for key, nodelist in self.key_nodelists:
            dct[key] = nodelist.render(context)
        return ''

@register.tag('dict')
def do_dict(parser, token):
    """
    The rationale behind this tag is identical to that of the ``list tag``, but rather than allowing us to
    create and append to a list directly within a template, this tag allows us to create and add to a dict in
    the same manner.

    For example, suppose we have a template "my_post_format.html" that expects an object and that looks
    something like the following:

    .. code-block::django
        <table><tr>
            <td>
                <div class="title">{{ obj.title|safe }}</div>
                <div class="body">{{ obj.body|safe }}</div>
            </td>
            <td>
                <div class="photo">{{ obj.image|safe }}</div>
            </td>
        </tr></table>

    We might then use the following to render it:

    .. code-block::django
        {% for post in posts %}
            {% dict 'html_dict' set 'title' %}
                <b>{{ post.title|upper }}</b>
            {% set 'body' %}
                <div class="author">{{ post.author.get_full_name() }}</div>
                {{ post.body|safe }}
            {% set 'image' %}
                <img src="{{ post.image.url }}">
            {% endset %}
            {% include 'my_post_format.html' obj=html_dict %}
        {% endfor %}

    Each ``set`` will set the associated key in "html_dict" to the value of the block that follows it, allowing
    us to create a dict suitable to an existing template inline with the template rather than having to create it
    within the view and pass it in context.

    As with ``list``, adding a "clear" keyword prior to the ``set`` keyword of the initial tag will clear any dict
    with this name currently in context, if it exists, prior to adding any further contents. For example, assuming
    "html_dict" already exists and has values, the following will clear it prior to adding any further contents:

    .. code-block::django
        {% dict 'html_dict' clear set 'one' %}
            HTML One
        {% set 'two' %}
            HTML TWO
        {% endset %}

    Note that the dict name and all keys must be string literals. Variable dict names and keys are not permitted.
    """
    _clear, _set = 'clear', 'set'
    clear = error = key = name = False
    bits = token.split_contents()[1:]
    if len(bits) == 3:
        name, _set, key = bits
    elif len(bits) == 4:
        name, _clear, _set, key = bits
        if _clear == 'clear':
            clear = True
    else:
        error = True
    if _set != 'set' or _clear != 'clear':
        error = True
    if error:
        raise TemplateSyntaxError('Opening "dict" tags take the form {%% dict DICT_NAME [clear] set KEY %%};'
                                  ' you entered {%% %s %%}' % token.contents)
    key_nodelists = [(key[1:-1], parser.parse(('set', 'enddict')))]  # a list of (DICT_KEY, NODELIST) tuples
    token = parser.next_token()
    while token.contents.startswith('set'):
        bits = token.split_contents()
        if len(bits) != 2:
            raise TemplateSyntaxError('Post-opening "dict" tags take the form {%% set KEY %%}; you entered'
                                      ' {%% %s %%}' % token.contents)
        key_nodelists.append((bits[1][1:-1], parser.parse(('set', 'enddict'))))
        token = parser.next_token()
    return DictNode(name[1:-1], key_nodelists, clear)



@register.tag
def usercache(parser, token):
    """Create a `CacheFrag`_ record for the current user, if needed, and return cached content.

    This tag works the same as the `cache tag`_ but automatically accounts for the unique id of the current user
    without it having to be entered as an argument. The following two blocks, for example, would be functionally
    identical for display purposes, but the latter will record the current user in the ``user`` field instead of
    as an argument.

    ..  code-block:: django

        {% cache 12345 FRAG_NAME USER %}
            User-specific content
        {% endcache %}

        {% usercache 12345 FRAG_NAME %}
            User-specific content
        {% endusercache %}
    """
    return _get_cache_frag_node(parser, token, 'usercache', True)



@register.tag
def sitecache(parser, token):
    """Create a `CacheFrag`_ record for the current site, if needed, and return cached content.

    This tag works the same as the `cache tag`_ but automatically accounts for the unique id of the current site
    without it having to be entered as an argument. The following two blocks, for example, would be functionally
    identical for display purposes, but the latter will record the id of the current site in the ``site_id`` field
    instead of as an argument.

    ..  code-block:: django

        {% cache 12345 FRAG_NAME SITE_ID %}
            Site-specific content
        {% endcache %}

        {% sitecache 12345 FRAG_NAME %}
            Site-specific content
        {% endsitecache %}

    Note that this tag requires Django's Sites framework to be installed, as we'll look to ``settings.SITE_ID`` to
    retrieve the id of the current site. The tag will error if no site id can be retrieved.
    """
    return _get_cache_frag_node(parser, token, 'sitecache', False, True)



@register.tag
def usersitecache(parser, token):
    """Create a `CacheFrag`_ record for the current site and user, if needed, and return cached content.

    This tag works the same as the `cache tag`_ but automatically accounts for the unique id of the current user
    and site without their having to be entered as arguments. The following two blocks, for example, would be
    functionally identical for display purposes, but the latter will record the current user and site in the
    ``user`` and ``site_id`` fields respectively instead of as arguments.

    ..  code-block:: django

        {% cache 12345 FRAG_NAME USER SITE %}
            User/Site-specific content
        {% endcache %}

        {% usersitecache 12345 FRAG_NAME %}
            User/Site-specific content
        {% endusersitecache %}

    Note that the same error conditions that apply to the ``usercache`` and ``sitecache`` tags also apply to this
    tag.
    """
    return _get_cache_frag_node(parser, token, 'usersitecache', True, True)
