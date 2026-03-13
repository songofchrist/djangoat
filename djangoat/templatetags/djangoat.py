import math

from django.conf import settings
from django.core.cache import InvalidCacheBackendError, caches
from django.core.cache.utils import make_template_fragment_key
from django.db.models.fields.files import ImageFieldFile
from django.template import Library, Node, TemplateSyntaxError, VariableDoesNotExist
from django.utils import timezone
from django.utils.safestring import mark_safe

from .. import (DATA, DJANGOAT_PAGER, DJANGOAT_THUMB_GET_URL, DJANGOAT_THUMB_TYPE_HTML,
                DJANGOAT_THUMB_TYPE_URLS)

from ..models import CACHE_FRAG_KEYS, CacheFrag
from ..utils import get_data, get_seconds_from_duration_string

register = Library()



# FILTERS
@register.filter
def data(key, arg=None):
    """Retrieves the output of `get_data`_ for ``djangoat.DATA[key]``

    The logic behind this filter is the same as that for the ``data`` tag. The only difference is that, because this
    is a filter, it's limited to at most one argument. But also because it's a filter, it can be included directly
    in for loops or chained directly to other filters, which may prove more convenient in certain cases. See the
    `data tag`_ for more on the theory behind this filter.

    :param key: a key in ``djangoat.DATA``
    :param arg: an argument to pass to the function referenced by ``djangoat.DATA[key]`` (otherwise, it's ignored)
    :return: the output of `get_data`_ for ``djangoat.DATA[key]``
    """
    return get_data(key, *([arg] if arg else []))



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
def mod(a, b):
    """Returns the result of ``a % b``.

    :param a: the number to be divided
    :type a: int, float
    :param b: the number to divide by
    :type b: int, float
    :return: the remainder of the division
    """
    try:
        return a % b
    except:
        return ''



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

    If an API gives us the duration of something in seconds, we'll likely want to display this in a form that will be
    more meaningful to the user. This tag divides seconds into its component parts as shown below:

    ..  code-block:: python

        {
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0
        }

    :param seconds: total seconds to break into different units
    :type s: int
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
def thumb(file, key):
    """Return html that represents a thumbnail for ``file`` based on ``key``.

    This filter works identically to the `thumb_url tag`_, but yields html instead of a url. It also allows us
    to associated html with a particular type of file via ``DJANGOAT_THUMB_TYPE_HTML``. If no url is returned by
    the ``DJANGOAT_THUMB_GET_URL`` function, then we'll first attempt to get html from this dict prior to trying
    for a static url from ``DJANGOAT_THUMB_TYPE_URLS``. This first dict allows us to associate vector icons, such as
    those in Font Awesome, with a particular extension rather an image. Or we may simply use styled text as the
    thumbnail for certain kinds of files.

    Note that the ``DJANGOAT_THUMB_TYPE_HTML`` will take priority. If we find a match for a particular file type in
    this dict, we will use it and ignore entries in ``DJANGOAT_THUMB_TYPE_URLS``.

    :param file: any file field
    :param key: a key to pass to ``DJANGOAT_THUMB_GET_URL`` to indicate the kind of thumbnail to return
    :return: thumbnail html
    """
    if file:
        if DJANGOAT_THUMB_GET_URL:
            url = DJANGOAT_THUMB_GET_URL(file, key, file.__class__ == ImageFieldFile)
            if url:
                return mark_safe(f'<img class="thumb" src="{url}">')
        ext = file.name.split('.')[-1].lower()
        html = DJANGOAT_THUMB_TYPE_HTML.get(ext, None)
        if html:
            return mark_safe(html)
        url = DJANGOAT_THUMB_TYPE_URLS.get(ext, DJANGOAT_THUMB_TYPE_URLS['DEFAULT'])
    else:
        url = DJANGOAT_THUMB_TYPE_URLS['MISSING']
    return mark_safe(f'<img class="thumb" src="{settings.STATIC_URL}{url}">')



@register.filter
def thumb_url(file, key):
    """Return a thumbnail url for ``file`` based on ``key``.

    This filter takes a FileField or ImageFileField and returns the url for the thumbnail of ``file``. The big idea
    for this filter is to always return some kind of image, regardless of the kind of file passed in. We'll first
    attempt to derive a thumbnail url using the custom ``DJANGOAT_THUMB_GET_URL`` function, which will receive ``file``
    and ``key`` along with a third argument indicating whether  ``file`` is an ImageField. If this returns a url, we're
    done. If not, we'll look in ``DJANGOAT_THUMB_TYPE_URLS`` for a static image whose extension matches that of
    ``file``. If none is exists, we'll get the "DEFAULT" url. If ``file`` is itself empty, we'll return the
    "MISSING" url. Regardless, we should end up with a url to some kind of image.

    To change the static image per type, simply update the ``DJANGOAT_THUMB_TYPE_URLS`` dict, keying the path to a
    static image with the associated lowercase file extension, not including the static url. To update the "DEFAULT"
    or "MISSING" images, update the values of associated with these keys.

    Note that ``DJANGOAT_THUMB_GET_URL`` must be defined before it can be expected to return results. You may define
    it as follows:

    ..  code-block:: python

        import djangoat

        def my_thumb_func(file, key, is_image):
            . . .
            return my_thumb_url

        djangoat.DJANGOAT_THUMB_GET_URL = my_thumb_func

    Also note that you needn't define this function at all unless you want individualized thumbnails for each ``file``.
    If you only want generalized icons for different types of files, you may forgo this definition.

    :param file: any file field
    :param key: a key to pass to ``DJANGOAT_THUMB_GET_URL`` to indicate the kind of thumbnail to return
    :return: the url of the thumbnail
    """
    if file:
        if DJANGOAT_THUMB_GET_URL:
            url = DJANGOAT_THUMB_GET_URL(file, key, file.__class__ == ImageFieldFile)
            if url:
                return url
        url = DJANGOAT_THUMB_TYPE_URLS.get(file.name.split('.')[-1].lower(), DJANGOAT_THUMB_TYPE_URLS['DEFAULT'])
    else:
        url = DJANGOAT_THUMB_TYPE_URLS['MISSING']
    return settings.STATIC_URL + url




# SIMPLE TAGS
@register.simple_tag
def call_function(func, *args):
    """Calls a function that takes arguments.

    Assuming ``func`` has been included in template context, we can pass it arguments as follows:

    ..  code-block:: django

        {% call_function my_func arg1 arg2 arg3 %}

    Alternatively, if we want a function to be available globally, we may instead consider storing a function in
    ``djangoat.DATA`` and calling it via the `data tag`_.

    :param func: the function we want to call
    :type func: callable
    :param args: arguments to pass to ``func``
    :return: the return value of the function
    """
    return func(*args)



@register.simple_tag
def call_method(obj, method, *args):
    """Executes an object method that takes arguments.

    :param obj: the object whose ``method`` we want to call
    :param method: the method to call
    :type method: str
    :param args: arguments to pass to ``method``
    :return: the return value of the method
    """
    return getattr(obj, method)(*args)



@register.simple_tag(takes_context=True)
def data(context, key, *args):
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
       queryset on every page load, whether it is used or not, and this adds up when we have hundreds of such queries.
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

    We see here a call to the data tag, whose output we expect to injected into context under the variable name
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
    needed in entries can be imported without danger of circular imports.

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
    :param args: arguments to pass to ``djangoat.DATA[key]`` when its value is callable (otherwise, it's ignored)
    :return: the output of `get_data`_ for ``djangoat.DATA[key]`` or an empty string when a variable is specified
    """
    inject = False
    if key[-1] == '>':
        inject = True
        key = key[:-1]
    v = get_data(key, *args)
    if inject:
        context[key] = v
        return ''
    return v



@register.simple_tag(takes_context=True)
def pager(context,
          queryset,
          items_per_page=DJANGOAT_PAGER['items_per_page'],
          plus_or_minus=DJANGOAT_PAGER['plus_or_minus']):
    """Returns a widget and queryset based on the current page.

    Suppose we have a queryset ``books``. To enable paging on these objects we would begin by invoking this template
    tag somewhere prior to the display of our book records.

    ..  code-block:: django

        {% pager books %}

    The pager will get total records, calculate starting and ending item numbers, create a basic paging widget, and
    and inject the following variables into the template context:

    - ``pager_queryset``: the provided queryset, sliced according to the current page
    - ``pager_start``: the number of the starting record of ``pager_queryset``
    - ``pager_end``: the number of the ending record of ``pager_queryset``
    - ``pager_total``: the total number of records
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

    Widget defaults are available in ``djangoat.DJANGOAT_PAGER`` and may be altered by updating this dict, which
    takes the form below:

    ..  code-block:: python

        DJANGOAT_PAGER = {
            'items_per_page': 20,
            'next_text': 'Next »',
            'param': 'page',
            'plus_or_minus': 3,
            'prev_text': '« Prev',
        }

    Note that this tag relies on the current request object being present in the template context to retrieve the
    current page from the query string, so be sure to include this in context on any pages where pager is used.

    :param context: the template context
    :type context: dict
    :param queryset: the queryset through which to page
    :param items_per_page: items to show per page
    :type items_per_page: int
    :param plus_or_minus: how many links to display on either side of the current page
    :type plus_or_minus: int
    """
    qp = DJANGOAT_PAGER['param']
    g = context['request'].GET
    cqs = '&'.join([f'{k}={g[k]}' for k in g.keys() if k != qp])  # the current query string, excluding the page param
    if cqs:
        cqs += '&'
    try:
        p = int(g.get(qp, 1))
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
        w.append(f'<a href="?{cqs}{qp}={p - 1}">{DJANGOAT_PAGER["prev_text"]}</a>')
    rl = p - plus_or_minus
    ru = p + plus_or_minus
    if rl > 1:
        w.append(f'<a href="?{cqs}{qp}=1">1</a>')
        if rl > 2:
            w.append(' ... ')
    for i in range(1 if rl < 1 else rl, (pt if ru > pt else ru) + 1):
        w.append('<a href="javascript:void(0)" class="active">%d</a>' % p if i == p else f'<a href="?{cqs}{qp}={i}">{i}</a>')
    if ru < pt - 1:
        w.append(' ... ')
    if ru < pt:
        w.append(f'<a href="?{cqs}{qp}={pt}">{pt}</a>')
    if pt and p != pt:
        w.append(f'<a href="?{cqs}{qp}={p + 1}">{DJANGOAT_PAGER["next_text"]}</a>')
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
        except Exception:
            raise KeyError('"%s" tag requires the "request" object to be included in template context' % self.tag)
        if self.user:  # the usercache or usersitecache tag
            user_id = request.user.id
            if not user_id:
                raise Exception('"%s" tag is attempting to cache content for an unauthenticated user' % self.tag)
        if self.site:  # the sitecache or usersitecache tag
            try:
                site_id = settings.SITE_ID
            except Exception:
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
