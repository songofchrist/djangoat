from django import template
from django.db import models
from django.template.base import TemplateSyntaxError

from djangoat.builders import NewsletterBuilderError

register = template.Library()




@register.filter
def record(items, limit=None):
    """Record any items received on the builder for later reference.

    The primary purpose of this filter is to mark any model instances passed in as having been used, so that
    later sections do not duplicate current section content. In addition, because we may want to track what
    items appeared in a particular issue (i.e. to allow for rotating content between issues), we'll also
    record which items appeared in this section on a per-model basis.

    Used items will have their primary keys added to ``builder.used_item_pks_by_model_class`` on a per model
    basis. Before recording and returning queryset results for this call, we'll automatically exclude any used
    primary keys for this queryset's model. Or, if we've already retrieved certain content for later sections
    and have registered those via ``builder.record_items``, those items' primary keys will already exist in this
    dict and will therefore be excluded.

    Items will also be registered to ``builder.used_items_by_section_key``, a dict wherein we'll keep a
    per-section record of what items we've used in the newsletter. Each section will be a dict whose "ALL"
    key contains all recorded instances and whose other keys will indicate per-model instances.

    We might use this tag as follows:

    ..  code-block:: django
        {% for post in posts_qs|record %} . . . {% endfor %}            # assumes an already-sliced queryset
        {% for post in posts_qs|record:3 %} . . . {% endfor %}          # records and returns 3 unused posts
        {% for post in posts_list|record %} . . . {% endfor %}          # records and returns all posts in the list
        {{ post_instance|record }}                                      # records and returns a single instance

    NOTE: We only exclude used primary keys from querysets. If a single instance or a list of instances is
    provided, this will be recorded and returned as-is and may result in duplicates. That said, if we
    intentionally mean to include one or more items in multiple places, using single instances or lists of
    instances is how we would accomplish this.

    :param items: a model instance, queryset, or list of instances to record
    :param limit: a maximum number of records to return from a queryset (ignored for lists)
    :return: a model instance or list of model instances (depending on ``items``)
    """
    return items.dg_record['builder'].record_items(items, limit, items.dg_record['section_key'])



class RecordNode(template.Node):
    """
    TODO write a filter version of this
    The only reason I went ith the tag version is to make context available, so everything can be recorded on
    the builder.

    INSTEAD

    Add attribute "dg_newsletters" dict whenever an object / queryset is retrieved. This is a dict of the following
    form:

    {
        "builder": BUILDER,
        "section_key": KEY,
        "limit": LIMIT,
        . . .
    }

    In this way everything that a record filter will need to work will be included in the object passed in.

    instance|record (record instance)
    item_list|record (record all instances in list)
    queryset|record (record all instances in queryset)
    queryset|record:3 (record first 3 instances in queryset)

    NOTE: to make this work with lists, we'll need to create a list subclass as follows:

    class NewsletterBuilderList(list):
        def __init__(self, *args, description=None):
            super().__init__(*args)
            self.dg_newsletters = {}

    For everything in our imports, if we get back a list (or tuple) we'll transform it into an instance of the
    above. This will allow us to attach the necessary dict data, so that when it is passed in to the record filter
    The filter has what it needs from the object itself to register everything and retrieve the correct number of
    items.
    """
    def __init__(self, objs, limit):
        self.objs = objs
        self.limit = limit

    def render(self, context):
        builder = context['builder']  # a reference to our newsletter builder instance
        objs = self.objs.resolve(context)
        if isinstance(objs, QuerySet):
            objs = objs.all()  # ensure any prior slices / cached records are removed
            used_pks = builder.used_item_pks_by_model_class.get(objs.model.__name__, None)
            if used_pks:  # exclude previously used instances
                objs = objs.exclude(pk__in=used_pks)
            limit = (self.limit.resolve(context) if self.limit else None) or objs.dg_builder_limit
            objs = list(objs[:limit])  # retrieve X unused instances from this queryset
        if not isinstance(objs, (list, tuple)):  # assume we have a single instance
            objs = [objs]
        for obj in objs:
            model = obj.__class__.__name__
            builder.used_item_pks_by_model_class.setdefault(model, set()).add(obj.pk)
            section_records = builder.used_items_by_section_key.setdefault(context['section_key'], {
                'ALL': []
            })
            section_records['ALL'].append(obj)  # tracks all instances in the order they were added
            section_records.setdefault(model, set()).add(obj)  # tracks by instance model
        context['recorded_' + self.objs] = objs  # make recorded items available in context
        return ''

@register.tag
def old_record(parser, token):
    """
    This tag will take one of the following formats:

    ..  code-block:: django
        {% record INSTANCE %}
        {% record INSTANCE_LIST %}
        {% record QUERYSET MAX_DISPLAY %}

    When recording a model instance, we'll do the following:
    - Add the primary key of the instance to ``builder.used_item_pks_by_model_class`` to mark it as having been used
      and thereby prevent it from being included in subsequent querysets for that model.
    - Add the instance to ``builder.used_items_by_section_key`` to associated it with the current section, giving us
      a record of exactly where it appeared in the current newsletter.

    When recording an instance list, we'll go through each instance in the list as if it had been passed individually,
    populating ``builder.used_item_pks_by_model_class`` and ``builder.used_items_by_section_key`` as we go. Note the
    following in regard to lists:
    - The instances in INSTANCE_LIST do not have to be from the same model.
    - All instances in the list will be marked as having been displayed in the newsletter. If the section template
      contains logic that might prevent one from being displayed, then this tag should be used on individual
      instances rather than the whole list.

    When recording and retrieving a queryset, we'll perform some additional steps that ensure we end up with
    unique material for each section. These are as follows:
    - Exclude any previously used instances of this queryset's model from the resulting queryset.
    - Limit the resulting queryset to MAX_DISPLAY instances (defaults to the "limit" set when importing or 10).
    - Record instances in the resulting queryset as described above.
    - Inject the resulting queryset into context as "recorded_QUERYSET_NAME", so that the queryset can be reused.

    A single queryset might be reused within a section as follows:

    ..  code-block:: django
        {% record my_posts 2 %}  # retrieve 2 items from the "my_posts" queryset
        {% for post in recorded_my_posts %}  # display these 2 posts
            <div class="title">{{ post.title }}</div>
        {% endfor %}
        <div>INTERVENING AD BANNER</div>
        {% record my_posts 3 %}  # retrieve 3 DIFFERENT posts from the "my_posts" queryset (previous are excluded)
        {% for post in recorded_my_posts %}  # display these 3 posts
            <div class="title">{{ post.title }}</div>
        {% endfor %}

    Because the first call to the record tag registers the first two posts in the queryset as used, even though
    we pass in the same queryset on the second call, those first two posts will be automatically excluded. This
    allows us to reuse this queryset as many times as we want, while getting unique results with each new call.
    Note that we use "recorded_my_posts" when rendering our display, as "my_posts" is still the original
    queryset.

    As with instance lists, because all items returned in the resulting queryset are marked as used, any logic that
    might cause one or more to not be displayed should be executed PRIOR to using this tag to ensure that records
    match rendered content.

    Note that if we intentionally want to insert a previously used instance further down in the newsletter, we'll
    want to use one of the first two methods (INSTANCE / ISNTANCE_LIST), as these are rendered as-is and do not
    account for previously used items.
    """
    #queryset.query.high_mark = None until sliced, use to determine if limit has been applied; if not, apply a default limit of 10.
    bits = token.split_contents()[1:]
    if len(bits) > 2:
        raise TemplateSyntaxError('This tag should take one of the following forms: {%% record INSTANCE %%},'
                                  ' {%% record INSTANCE_LIST %%}, or {%% record QUERYSET [MAX_DISPLAY] %%};'
                                  ' you entered {%% %s %%}' % token.contents)
    return RecordNode(parser.compile_filter(bits[0]), parser.compile_filter(bits[1]) if len(bits) else None)