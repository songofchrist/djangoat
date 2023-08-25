from django.contrib import admin
from django.contrib import messages
from django.core.cache import cache

from .utils import get_csv_file, get_csv_rows_from_queryset




# FUNCTIONS
def clear_cache_frags(modeladmin, request, queryset):
    for cf in queryset:
        cache.delete(cf.key)  # clear cache contents, so it can repopulate on next access
clear_cache_frags.short_description = 'Clear selected fragments'



def csv_export_action(fields, filename, description='Export selected items to a CSV file', filter=None, callback=None, derived_fields=None, dynamic_columns=None, prettify_headers=True, agg_delimiter=', '):
    """
    Returns an export action for use in the Django admin.

    This function is designed to create an action that hands off the queryset from an admin list page to
    `get_csv_rows_from_queryset`_ and yields a CSV download file containing the details in ``fields``. This allows
    us to create and modify various kinds of reports very quickly.

    The function uses `get_csv_rows_from_queryset`_ to translate the queryset into CSV rows, and its ``fields``,
    ``derived_fields``, ``dynamic_columns``, ``prettify_headers``, and ``agg_delimiter`` arguments all  take the
    same form as the like-named arguments do in that function. Studying that function will help to inform us of
    the variety of options available to this one.

    The ``filter`` argument is a function that takes a queryset, the request object, and modeladmin, and returns a
    queryset. This allows us to modify the queryset on its way to `get_csv_rows_from_queryset`_, filtering out certain
    items, adding annotations, etc. It can also be used to translate one kind of queryset into another. For example,
    if we want to export a list of tasks for users selected on the user list page, we might pass in a filter function
    like the following:

    ..  code-block:: python

        def users_to_tasks(queryset, request, modeladmin):
            return Task.objects.filter(user__in=[user.pk for user in queryset])

    When we use ``filter`` to translate from one model to another, all ``fields`` should be given with reference to
    the resultant queryset.

    The ``callback`` argument, when provided, will receive the export filename and all the arguments that would
    otherwise be passed to `get_csv_rows_from_queryset`_ and should return a success message that indicates what the
    user should expect. This will generally be useful when report generation is expected to be long-running and when
    processing needs to be handed off to a task.

    An example use of this function would be something like the following:

    ..  code-block:: python

        user_task_export = csv_export_action(
            (
                "user__first_name",
                "user__last_name",
                ("name", "Task"),
                "due_date",
                "completed",
            ),
            "UserTasks",
            "Export selected user's tasks to a CSV file",
            lambda qs, r, ma: Task.objects.filter(user__in=[user.pk for user in qs])
        )

        class UserAdmin(admin.ModelAdmin):
            actions = user_task_export,
            . . .

    Because we transform the queryset received by ``filter`` into a ``Task`` queryset, all members of ``fields``
    relate to this model, which relates to the user and has a name, due date, and completed field. We will then be
    able to generate this report by selecting the newly created action and clicking "Go".

    :param fields: fields to include in the export; see the like-named argument from `get_csv_rows_from_queryset`_
        for more
    :param filename: the name of the CSV file without the ".csv" extension
    :param description: the text for the actions dropdown
    :param filter: a function that accepts the queryset, request, and modeladmin object and returns a queryset; it may
        be used to translate from one model to another when needed
    :param callback: a function to which the filtered queryset should be handed off for processing and which returns
        a success messaging indicating what the user should expect
    :param derived_fields: a function that yields data for derived fields; see the like-named argument from
        `get_csv_rows_from_queryset`_ for more
    :param dynamic_columns: a function that yields headers and data for dynamic columns; see the like-named argument
        from `get_csv_rows_from_queryset`_ for more
    :param prettify_headers: whether or not to prettify headers; see the like-named argument
        from `get_csv_rows_from_queryset`_ for more
    :param agg_delimiter: the delimiter on which to join many-to-many values; see the like-named argument
        from `get_csv_rows_from_queryset`_ for more
    :return: the dynamically created export action
    """
    def export_action(modeladmin, request, queryset):
        if filter:
            queryset = filter(queryset, request, modeladmin)
        if callback:
            messages.success(request, callback(filename + '.csv', queryset, fields, derived_fields, dynamic_columns, prettify_headers, agg_delimiter) or 'Your request has been processed.')
        else:  # return a CSV file download response
            return get_csv_file(filename, get_csv_rows_from_queryset(queryset, fields, derived_fields, dynamic_columns, prettify_headers, agg_delimiter))
    export_action.short_description = description
    export_action.__name__ = filename
    return export_action




# ADMINS
class CacheFragAdmin(admin.ModelAdmin):
    actions = clear_cache_frags,
    list_display = 'name', 'site_id', 'user', 'tokens'
    list_filter = 'name', 'site_id'
    search_fields = 'user__email', 'user__first_name', 'user__last_name', 'tokens'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
