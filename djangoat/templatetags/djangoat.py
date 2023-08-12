import math

from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.cache import InvalidCacheBackendError, caches
from django.core.cache.utils import make_template_fragment_key
from django.template import Library, Node, TemplateSyntaxError, VariableDoesNotExist

from ..models import CacheFrag

from .. import DJANGOAT_DATA

register = Library()





# The following cache tags are based upon the original Django cache tag, located at the address below:
# https://github.com/django/django/blob/b9cf764be62e77b4777b3a75ec256f6209a57671/django/templatetags/cache.py
class MyCacheNode(Node):
    def __init__(self, nodelist, expire_time_var, fragment_name, vary_on, cache_name, site=None, user=False):
        self.nodelist = nodelist
        self.expire_time_var = expire_time_var
        self.fragment_name = fragment_name
        self.vary_on = vary_on
        self.cache_name = cache_name
        self.site = site
        self.user = user

    def render(self, context):
        try:
            expire_time = self.expire_time_var.resolve(context)
        except VariableDoesNotExist:
            raise TemplateSyntaxError('"cache" tag got an unknown variable: %r' % self.expire_time_var.var)
        if expire_time is not None:
            try:
                expire_time = int(expire_time)
            except (ValueError, TypeError):
                raise TemplateSyntaxError('"cache" tag got a non-integer timeout value: %r' % expire_time)
        if self.cache_name:
            try:
                cache_name = self.cache_name.resolve(context)
            except VariableDoesNotExist:
                raise TemplateSyntaxError('"cache" tag got an unknown variable: %r' % self.cache_name.var)
            try:
                fragment_cache = caches[cache_name]
            except InvalidCacheBackendError:
                raise TemplateSyntaxError('Invalid cache name specified for cache tag: %r' % cache_name)
        else:
            try:
                fragment_cache = caches['template_fragments']
            except InvalidCacheBackendError:
                fragment_cache = caches['default']
        vary_on = [var.resolve(context) for var in self.vary_on]  # get the actual vary_on values here

        # Custom code to interact with CacheFragment
        if self.site:
            vary_on.append(self.site)
        if self.user:
            self.user = vary_on.pop(0)
            vary_on.append(self.user)
        vary_on_str = str(vary_on)[1:-1] if vary_on else ''
        str_key = self.fragment_name + '|' + vary_on_str
        cache_key = settings.MY_CACHE_KEYS.get(str_key, None)
        if not cache_key:  # make sure this is in the db, but store in keys to prevent unnecessary calls
            cf, created = CacheFragment.objects.get_or_create(key=make_template_fragment_key(self.fragment_name, vary_on))
            if created:
                cf.name = self.fragment_name
                if vary_on:
                    cf.extra = vary_on_str
                if self.site:
                    cf.site_id = self.site
                if self.user:
                    cf.user_id = self.user
                cf.save()
            settings.MY_CACHE_KEYS[str_key] = cache_key = cf.key
        if settings.DEBUG:
            print('CACHE FRAG %s (expiry %ds)'% (str_key, expire_time))

        # Resume original code
        value = fragment_cache.get(cache_key)
        if value is None:
            value = self.nodelist.render(context)
            fragment_cache.set(cache_key, value, expire_time)
        return str(value)



def original(parser, token, endcache, site=None, user=False):
    nodelist = parser.parse((endcache,))
    parser.delete_first_token()
    tokens = token.split_contents()
    if len(tokens) < 3:
        raise TemplateSyntaxError("'%r' tag requires at least 2 arguments." % tokens[0])
    if len(tokens) > 3 and tokens[-1].startswith('using='):
        cache_name = parser.compile_filter(tokens[-1][len('using='):])
        tokens = tokens[:-1]
    else:
        cache_name = None
    return [
        nodelist,
        parser.compile_filter(tokens[1]),  # expiry
        tokens[2],  # fragment_name
        [parser.compile_filter(t) for t in tokens[3:]],  # vary on
        cache_name,
        site,
        user
    ]





# FILTERS
@register.filter
def dataf(key, arg=None):
    """Retrieves the value of ``DJANGOAT_DATA[key]`` or, if the value is a callable, the result of the callable.

    The logic behind this filter is the same as that for the ``data`` tag. The only difference is that, because this
    is a filter, it is limited to at most one argument. But also because it is a filter, it can be included directly
    in for loops or chained directly to other filters, which may prove more convenient in certain cases. See the
    `data <#djangoat.templatetags.djangoat.data>`__ tag for more on the theory behind this filter.

    :param key: a key in ``DJANGOAT_DATA``
    :type key: str
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
    :type dictionary: dict
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

    For example, if we have ``items = range(10)``, this tag will divide the list up into the following list of lists:
    ``[[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]``. We may then loop through these as follows to form our columns.

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




# SIMPLE TAGS
@register.simple_tag
def call_function(func, *args):
    """Calls a function that takes arguments.

    Assuming ``func`` has been included in template context, we can pass it arguments as follows:

    ..  code-block:: django

        {% call_function my_func arg1 arg2 arg3 %}

    Alternatively, if we want a function to be available globally, we may instead consider storing a function in
    ``DJANGOAT_DATA`` and calling it via the `data <#djangoat.templatetags.djangoat.data>`__ tag.

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

    This template tag solves all of these issues by consolidating all such querysets into a single dict,
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

    ..  code-block:: django

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

    ..  code-block:: django

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
    may also use the `dataf <#djangoat.templatetags.djangoat.dataf>`__  filter below, which operates on the same
    principle but uses filter syntax.

    As for how various querysets and functions make their way into the ``DJANGOAT_DATA``, this is a matter of
    preference. Adding them at the bottom of an app's ``models.py`` file saves importing models but may result in
    circular imports in certain instances. You may instead consider making a ``data.py`` file for each app or a single
    file placed in the project root.

    In summary, this tag represents a way of thinking that results in a particular process. If this process agrees with
    you, the tag may save you a good deal of hassle.

    :param context: the template context
    :type context: dict
    :param key: a key in ``DJANGOAT_DATA``; if ``key`` ends in ">", then we'll inject the corresponding value into
        ``context`` under the name of this key
    :type key: str
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
          plus_or_minus=getattr(settings, 'DJANGOAT_PAGER_SHOW_PLUS_OR_MINUS', 3)):
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

    We would then display out book records and the paging widget. A list page template might look something like the
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

    The following may be added to Django's settings to alter this tag's default behavior:

    - ``DJANGOAT_PAGER_ITEMS_PER_PAGE`` (defaults to 20)
    - ``DJANGOAT_PAGER_NEXT_PAGE_TEXT`` (defaults to "Next »")
    - ``DJANGOAT_PAGER_PREVIOUS_PAGE_TEXT`` (defaults to "« Prev")
    - ``DJANGOAT_PAGER_QUERY`` (defaults to "page")
    - ``DJANGOAT_PAGER_SHOW_PLUS_OR_MINUS`` (defaults to 3)

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
    q = getattr(settings, 'DJANGOAT_PAGER_QUERY', 'page')
    try:
        p = int(context['request'].GET.get(q, 1))
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
        w.append(f'<a href="?{q}={p - 1}">{getattr(settings, "DJANGOAT_PAGER_PREVIOUS_PAGE_TEXT", "« Prev")}</a>')
    rl = p - plus_or_minus
    ru = p + plus_or_minus
    if rl > 1:
        w.append(f'<a href="?{q}=1">1</a>')
        if rl > 2:
            w.append(' ... ')
    for i in range(1 if rl < 0 else rl, (pt if ru > pt else ru) + 1):
        w.append('<a href="javascript:void(0)" class="active">%d</a>' % p if i == p else f'<a href="?{q}={i}">{i}</a>')
    if ru < pt - 1:
        w.append(' ... ')
    if ru < pt:
        w.append(f'<a href="?{q}={pt}">{pt}</a>')
    if pt and p != pt:
        w.append(f'<a href="?{q}={p + 1}">{getattr(settings, "DJANGOAT_PAGER_NEXT_PAGE_TEXT", "Next »")}</a>')
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




# TAGS
@register.tag
def cachefrag(parser, token):
    """Create a ``CacheFrag`` record, if needed, and return cached content.

    Functionally, this tag is no different from the built-in Django `template cache tag <https://docs.djangoproject.com/en/dev/topics/cache/#template-fragment-caching>`__.
    Its first two arguments are the seconds to expiration and fragment name, and everything thereafter distinguishes
    one fragment of a particular name from the next.

    Unlike the built-in cache tag, this tag records each unique fragment, along with its unique key, in the database,
    so that it can be accessed and cleared on demand. For example, if the nav bar on a particular site needs updating,
    rather than clearing the entire cache, we can use the ``CacheFrag`` admin to clear only that one fragment.

    Also, because the fragment name and other distinguishing arguments are recorded in the database, we can query on
    them to clear or delete all fragments having a particular name or containing a particular argument. This is
    especially helpful when certain objects are updated in the database which affect cached content.

    For example, suppose the links in the nav bar are updatable within the admin. If a user decides to change the title
    or url of a link or the order in which the links appear, we'll want to update the nav bar ASAP. Rather than
    waiting for the nav bar cache to expire, we can query the associated fragment within the ``save_model`` admin
    method and clear it immediately, so that it can be repopulated with the up-to-date links.

    The following demonstrates how this code might be used:

    ..  code-block:: django

        {% cachefrag 12345 FRAG_NAME "token1" "token2" "token3" %}
            Cached content
        {% endcachefrag %}

    For this call, a ``CacheFrag`` record will be created with the ``name`` FRAG_NAME and a ``tokens`` value of
    :code:`["token1", "token2", "tokens3"]`. The tokens will be stored in a ``tokens``
    `JSONField <https://docs.djangoproject.com/en/dev/topics/db/queries/#querying-jsonfield>`__, so that it can
    easily be queried.

    Also worth noting is that the values of the Djangoat's TIMES dict are automatically available in the seconds slot
    of this tag. We do not immediately know how many seconds are in 6 minutes or 6 hours or 6 days, so rather than
    having to do the math each time we want to use one of these in the tag and then forgetting what the number means
    next time we encounter it, we can simply pass in "6m" or "6h" or "6d" instead. Consider the following:

    ..  code-block:: django

        {% cachefrag "173d" FRAG_NAME "token1" "token2" "token3" %}
            I will expire in 173 days.
        {% endcachefrag %}

    If you need a value that is not available by default, simply update the TIMES dict, and your custom time
    will become available for use with this tag.
    """
    return CacheFragNode(*original(parser, token, 'endcachefrag'))



@register.tag
def sitecachefrag(parser, token):
    """Create a ``CacheFrag`` record for the current site, if needed, and return cached content.

    This works the same as the `cachefrag tag <#djangoat.templatetags.djangoat.cachefrag>`__ but automatically
    accounts for the unique id of the current site without it having to be entered as a token. The following two
    blocks, for example, would be functionally identical.

    ..  code-block:: django

        {% cachefrag 12345 FRAG_NAME SITE_ID %}
            Site-specific content
        {% endcachefrag %}

        {% sitecachefrag 12345 FRAG_NAME %}
            Site-specific content
        {% endsitecachefrag %}
    """
    return CacheFragNode(*original(parser, token, 'endsitecachefrag', settings.SITE_ID))



@register.tag
def siteusercachefrag(parser, token):
    """Create a ``CacheFrag`` record for the current site and user, if needed, and return cached content.

    This works the same as the `cachefrag tag <#djangoat.templatetags.djangoat.cachefrag>`__ but automatically
    accounts for the unique ids of both the current site and user without either having to be entered as a token.
    The following two blocks, for example, would be functionally identical.

    ..  code-block:: django

        {% cachefrag 12345 FRAG_NAME SITE_ID USER_ID %}
            Site-specific, user-specific content
        {% endcachefrag %}

        {% siteusercachefrag 12345 FRAG_NAME %}
            Site-specific, user-specific content
        {% endsiteusercachefrag %}

    Note that this tag requires a ``request`` context variable containing the request object in order to capture the
    user.
    """
    return CacheFragNode(*original(parser, token, 'endsiteusercachefrag', settings.SITE_ID, True))



@register.tag
def usercachefrag(parser, token):
    """Create a ``CacheFrag`` record for the current user, if needed, and return cached content.

    This works the same as the `cachefrag tag <#djangoat.templatetags.djangoat.cachefrag>`__ but automatically
    accounts for the unique id of the current user without it having to be entered as a token. The following two
    blocks, for example, would be functionally identical.

    ..  code-block:: django

        {% cachefrag 12345 FRAG_NAME USER_ID %}
            User-specific content
        {% endcachefrag %}

        {% usercachefrag 12345 FRAG_NAME %}
            User-specific content
        {% endsiteusercachefrag %}

    Note that this tag requires a ``request`` context variable containing the request object in order to capture the
    user.
    """
    return CacheFragNode(*original(parser, token, 'endusercachefrag', None, True))