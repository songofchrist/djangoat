from django import template
from django.db.models.query import QuerySet
from django.template.base import TemplateSyntaxError

register = template.Library()




class RecordNode(template.Node):
    def __init__(self, objs, limit):
        self.objs = objs
        self.limit = limit

    def render(self, context):
        is_queryset = False
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
def record(parser, token):
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