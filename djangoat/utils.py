# -*- coding: utf-8 -*-
import csv
# import datetime
# import difflib
import json
# import random
# # import openpyxl
# import os
# import requests
# import time
# import types
# # import xlwt
#
# # from easy_thumbnails.files import get_thumbnailer
# from functools import update_wrapper
from io import BytesIO, StringIO
# # from PIL import Image, ImageOps
# from tempfile import NamedTemporaryFile
#
# from django.apps import apps
# from django.conf import settings
# from django.core.mail import EmailMultiAlternatives
# from django.core.files import File
# from django.contrib import admin
# from django.contrib.redirects.models import Redirect
# from django.db.models import F
# from django.db.models.fields.files import ImageFieldFile
from django.http.response import HttpResponse
# from django.template import loader
# from django.utils.html import strip_tags
# from django.utils.safestring import mark_safe
# from django.urls import path, resolve
# from django.urls.resolvers import URLPattern




def get(obj, *keys):
    """Returns the targeted value or None.

    Suppose the following JSON object is returned by an API:

    ..  code-block:: python

        response = {
            "books": [
                {
                    "title": "Awesome Book",
                    "author": "Mister Author",
                    "awards": [
                        "Cool Beans Award",
                        "Kiddie Favorite Award",
                        . . .
                    ]
                },
                . . .
            ],
            "charges": 123,
            . . .
        }

    Now suppose we want to get the first award of the first book in the "books" list. Normally, we'd do lots of looping
    and testing to get this. But with this method, we can target this value by the following:

    ..  code-block:: python

        get(response, 'books', 0, "awards", 0)

    If at any point the value we're targeting doesn't exist, we'll return ``None``. Otherwise, we'll return the desired
    value. This method is especially useful in targeting elements in unpredictable or variable structures.

    :param obj: a dict, list, tuple or any other object whose values can be accessed by a key or index
    :param keys: the keys or indices that target the value to be returned
    :return: the value in ``obj`` targeted by ``keys``
    """
    try:
        r = obj
        for k in keys:
            r = r[k]
        return r
    except:
        return None



def get_csv_content(rows, dialect=csv.excel, keys=None, add_headers=True):
    """Returns the data in ``rows`` as bytes, ready to be used in a CSV file download or email attachment.

    ``rows`` here may take one of the following forms:

    ..  code-block:: python

        list_of_lists = [
            ['H1', 'H2', 'H3' . . . ],
            ['data_1a', 'data_1b', 'data_1c' . . . ],
            ['data_2a', 'data_2b', 'data_2c' . . . ]
        ]

        list_of_dicts = [
            {'H1': 'data_1a', 'H2': 'data_1b', 'H3': 'data_1c' . . . }
            {'H1': 'data_2a', 'H2': 'data_2b', 'H3': 'data_2c' . . . }
        ]

    For ``list_of_lists``, headers, if desired, should be included as the first row and data rows thereafter.
    For ``list_of_dicts``, headers can be derived from the keys of the first entry or from ``keys``. Note that
    column order is not guaranteed when when they are derived from a standard dict.

    :param rows: a list of lists or list of dicts
    :param dialect: the dialect in which to write the CSV
    :param keys: when ``rows`` is a list of dicts or OrderedDicts, use these keys to derive values; if none are
        provided, derive ``keys`` from the first entry in ``rows``
    :param add_headers: if True, when ``rows`` is a list of dicts or OrderedDicts, add a header row using dict keys
    :return: bytes, ready for writing to a file
    """
    f = StringIO()
    if rows:
        if not isinstance(rows[0], (list, tuple)):  # transform a list of dicts into a list of lists
            rows = get_rows_from_dicts(rows, keys, add_headers)
        csv.writer(f, dialect).writerows(rows)
        f.seek(0)
    return f.read()



def get_csv_file(filename, rows, dialect=csv.excel, keys=None, add_headers=True):
    """Returns a CSV file download response.

    :param filename: the name of the CSV file, without the ".csv" extension
    :param rows: see the `get_csv_content tag`_ for acceptable formats
    :param dialect: the dialect in which to write the CSV
    :param keys: when ``rows`` is a list of dicts or OrderedDicts, the keys of the values to include in the output
    :param add_headers: if True, when ``rows`` is a list of dicts or OrderedDicts, add a header row using dict keys
    :return: a CSV file download
    """
    return HttpResponse(
        get_csv_content(rows, dialect, keys, add_headers),
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}.csv"'}
    )



def get_json_file(filename, rows, keys=None, add_headers=True):
    """Returns a JSON file download response.

    :param filename: the name of the JSON file, without the ".json" extension
    :param rows: see the `get_csv_content tag`_ for acceptable formats
    :param keys: when ``rows`` is a list of dicts or OrderedDicts, the keys of the values to include in the output
    :param add_headers: if True, when ``rows`` is a list of dicts or OrderedDicts, add a header row using dict keys
    :return: a JSON file download
    """
    return HttpResponse(
        json.dumps(
            get_rows_from_dicts(rows, keys, add_headers) if rows and not isinstance(rows[0], (list, tuple)) else rows,
            sort_keys=True,
            indent=2
        ),
        content_type='text/json',
        headers={'Content-Disposition': f'attachment; filename="{filename}.json"'}
    )



def get_rows_from_dicts(rows, keys=None, key_headers=True):
    """Transforms a list of dicts / OrderedDicts into a list of lists

    :param rows: a list of dicts / OrderedDicts
    :param keys: the keys whose values to include in the resulting lists; if unspecified, these will be derived from
        the first entry in ``rows``
    :param key_headers: if True, add a ``keys`` header to resultant rows
    :return: a list of lists, suitable for output as a CSV
    """
    if not keys:
        keys = list(rows[0].keys())
    return ([keys] if key_headers else []) + [[r[n] for n in keys] for r in rows]



def get_xls_file(filename, rows, keys=None, add_headers=True):
    """Returns a simple XLS file download response.

    Note that this function requires the following package:
    `https://pypi.org/project/xlwt/ <https://pypi.org/project/xlwt/>`__

    :param filename: the name of the XLS file, without the ".xls" extension
    :param rows: see the `get_csv_content tag`_ for acceptable formats
    :param keys: when ``rows`` is a list of dicts or OrderedDicts, the keys of the values to include in the output
    :param add_headers: if True, when ``rows`` is a list of dicts or OrderedDicts, add a header row using dict keys
    :return: an XLS file download
    """
    import xlwt
    if rows and not isinstance(rows[0], (list, tuple)):  # transform a list of dicts into a list of lists
        rows = get_rows_from_dicts(rows, keys, add_headers),
    wb = xlwt.Workbook(encoding='utf-8')
    s = wb.add_sheet('Sheet1')
    for r, row in enumerate(rows):
        for c in range(len(row)):
            s.write(r, c, row[c])
    r = HttpResponse(
        content_type='application/ms-excel',
        headers={'Content-Disposition': f'attachment; filename="{filename}.xls"'}
    )
    wb.save(r)
    return r



def get_xlsx_file(filename, rows, keys=None, add_headers=True):
    """Returns a simple XLSX file download response.

    Note that this function requires the following package:
    `https://pypi.org/project/openpyxl/ <https://pypi.org/project/openpyxl/>`__

    :param filename: the name of the XLSX file, without the ".xlsx" extension
    :param rows: see the `get_csv_content tag`_ for acceptable formats
    :param keys: when ``rows`` is a list of dicts or OrderedDicts, the keys of the values to include in the output
    :param add_headers: if True, when ``rows`` is a list of dicts or OrderedDicts, add a header row using dict keys
    :return: an XLSX file download
    """
    import openpyxl
    if rows and not isinstance(rows[0], (list, tuple)):  # transform a list of dicts into a list of lists
        rows = get_rows_from_dicts(rows, keys, add_headers),
    wb = openpyxl.Workbook()
    s = wb.active
    s.title = 'Sheet1'
    for r in rows:
        s.append(r)
    r = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}.xlsx"'}
    )
    wb.save(r)
    return r




def get_csv_rows_from_queryset(queryset, values, prettify_headers=False, derived_fields=None, dynamic_columns=None):
    """Returns a list of lists suitable for building a CSV file or spreadsheet.

    :param queryset: the queryset from which to retrieve ``values``
    :param values: a tuple or list of the following form:

        ..  code-block:: python

            (
                'field',
                'choice_field',
                'method',
                'rep__user__name'
                '_annotated__avg',
                '_derived',
                ('field', 'Field With Custom Title'),
                ('choice_field', 'Choice Field', {V1: TEXT1, V2: TEXT2 . . .}),
                ('method', 'Method With Custom Title')
                ('rep__user__name', 'Auto Annotated User Name'),
                ('_annotated__avg', 'Annotated Average'),
                ('_derived', 'Programmatically Derived')
            )


        Field names in this scheme may be any one of the following:

        - A field or method on a queryset instance
        - A field on a related model
        - An annotated field
        - A derived field

        table to retrieve via "annotate", or a custom annotation. Whenever "__" appears in a field, an annotation by
        this field name will automatically be added to the queryset. For example, for "rep__user__name", we would do
        the following:

            queryset = queryset.annotate(rep__user__name=F('rep__user__name'))

        Thus any ForeignKey field can be represented in the output. ManyToMany fields will likely require a custom
        annotation that joins resultant values together (i.e. via StringAgg). Custom annotations containing "__" must
        begin with an underscore, as in "_annotated__avg", so that they are not inadvertently auto annotated.
        Alternatively, for more complex operations, the "values" argument may take the form (FUNCTION, HEADERS), where
        FUNCTION returns a row of data and HEADERS the header row. For example, you might use something like this:

            (lambda o: [o.name, o.company.name, o.company.sites()], ['User', 'Company', 'Company Sites'])

        Make sure to use a "select_related" on the queryset when referencing related models to increase efficiency.
        Also note the dict provided above as the third value in the "choice_field" tuple. When provided, this will be
        used to map the result value, which may be a number or textual key, to a more readable display value. For
        dynamic displays, use "derived_fields".
    :param prettify_headers: when a header is not explicitly provided, set this to True to title case the field, split
        the field by "__" and take the last string, and replace any remaining underscores with spaces.
    :param derived_fields: a function that takes "queryset" and returns a dictionary of derived field results for use
        in the report. Suppose I have a complex operation that needs doing and want to represent this as a field on
        the report, though it is not a real field. I could do this by adding a bound field on the model and calling it
        once per record, but this may prove slow and inefficient. Alternatively, I could provide a function that will
        perform the calculations all at once and return results in per-primary key dictionary which will then be pulled
        in for the pseudo-field. The function should return something like the following:

            {
                '_field_1: {
                    QUERYSET_PRIMARY_KEY_1: VALUE_1,
                    QUERYSET_PRIMARY_KEY_2: VALUE_2,
                    . . .
                },
                '_field_2: {. . .}
            }

        "_field_1" and "_field_2" in "values" will be filled with the corresponding data from the primary key dict.
    :param dynamic_columns: a function that takes "queryset" and returns a tuple of dynamic headers and corresponding
        row data that will be appended to headers / rows generated from "values". The tuple should looks something
        like the following:

            (
                [HEADER_1, HEADER_2 . . .],
                {
                    QUERYSET_PRIMARY_KEY_1: [VALUE_1, VALUE_2 . . .],
                    QUERYSET_PRIMARY_KEY_2: [VALUE_1, VALUE_2 . . .],
                    . . .
                }
            )

        This is primarily intended as a means for including dynamic columns that may differ from one queryset to the
        next.
    :return: a list of lists, ready to be fed into "get_csv_content" or anything that makes use of it
    """
    if not queryset:
        return []
    if dynamic_columns:
        dch, dcr = dynamic_columns(queryset)  # dynamic header list / per-primary-key value lists
    else:
        dch, dcr = [], {}
    f = values[0]
    if isinstance(f, types.FunctionType):  # for (FUNCTION, HEADERS), use the passed function to derive each row
        headers, rows = values[1], [f(d) + dcr.get(d.pk, []) for d in queryset]
    else:
        df = derived_fields(queryset) if derived_fields else {}
        fields = []
        headers = []
        maps = {}
        for v in values:
            if isinstance(v, str):
                fields.append(v)
                headers.append(v.split('__')[-1].replace('_', ' ').title().lstrip() if prettify_headers else v)
            else:
                fields.append(v[0])
                headers.append(v[1])
                if len(v) > 2:  # mapping was included for this field
                    maps[v[0]] = dict(v[2])
        queryset = queryset.annotate(**{f: F(f) for f in fields if f[0] != '_' and '__' in f})
        rows = []
        qs = list(queryset)  # need a list to quickly test for dict / instance below
        if isinstance(qs[0], dict):  # results are in dict form as with "values" / "annotate"
            if df:
                for d in qs:
                    row = []
                    for f in fields:
                        v = d.get(f, None)
                        if v is None:
                            m = df.get(f, None)  # get the derived id / value map for this field, if one exists
                            if m:
                                v = m.get(d.pk, None)
                        m = maps.get(f, None)
                        row.append('' if v is None else (m.get(v, v) if m else v))
                    rows.append(row + dcr.get(d.pk, []))
            else:
                for d in qs:
                    row = []
                    for f in fields:
                        v = d.get(f, None)
                        m = maps.get(f, None)
                        row.append('' if v is None else (m.get(v, v) if m else v))
                    rows.append(row + dcr.get(d.pk, []))
        else:
            if df:
                for d in qs:
                    row = []
                    for f in fields:
                        v = getattr(d, f, None)
                        if v is None:
                            m = df.get(f, None)  # get the derived id / value map for this field, if one exists
                            if m:
                                v = m.get(d.pk, None)
                        elif callable(v):  # get the value of bound methods
                            v = v()
                        m = maps.get(f, None)
                        row.append('' if v is None else (m.get(v, v) if m else v))
                    rows.append(row + dcr.get(d.pk, []))
            else:
                for d in qs:
                    row = []
                    for f in fields:
                        v = getattr(d, f, None)
                        if callable(v):  # get the value of bound methods
                            v = v()
                        m = maps.get(f, None)
                        row.append('' if v is None else (m.get(v, v) if m else v))
                    rows.append(row + dcr.get(d.pk, []))
    return [headers + dch] + rows



# def get_file_from_url(url, save_path=None):
#     """
#     Downloads a file from the given url.
#
#     :param url: the url from which to retrieve the file
#     :param save_path: the path to which the file should be saved
#     :return: on success, return True if a save path is provided or the file if it has not; return False on failure
#     """
#     try:
#         f = requests.get(url).content
#     except:
#         return False
#     if save_path:
#         with open(save_path, 'wb+') as sf:
#             sf.write(f)
#         return True
#     return f
#
#
#
#
#
#
# def get_json_file_contents(path):
#     """
#     :param path: the path to a json file
#     :return: the contents of the file or an empty dict if it does not exist or is empty
#     """
#     if os.path.exists(path):
#         with open(path, 'r') as f:
#             c = f.read()
#             if c:
#                 return json.loads(c)
#     return {}
#
#
#
# def get_n_digit_string(n):
#     """Return a string of N digits, including leading zeros.
#
#     :param n: how many digits the string should be
#     :return: the string
#     """
#     s = 10 ** int(n)
#     return str(random.randrange(s, s * 2))[1:]
#
#
#
# def get_previous_month(date, months_back=1):
#     """
#     Get a tuple containing the year and month of a previous month, referenced from date. For example, if today is
#     1/2/2021, this will return (2020, 12) by default. If we go 3 months back, we'll instead get (2020, 10) and so on.
#     Results may then be used to form new date objects useful in queries.
#
#     :param date: the reference date
#     :param months_back: how many months back to get a result for
#     :return: a tuple of the form (YEAR, MONTH)
#     """
#     y = date.year
#     m = date.month - months_back
#     if m < 1:
#         y = y + int(m / 12) - 1
#         m = 12 - (-m % 12)
#     return y, m
#
#
#
#
#
#
# def get_url_name(request, remove_prefix=None):
#     name = resolve(request.path_info).url_name
#     return name[len(remove_prefix):] if remove_prefix and name.startswith(remove_prefix) else name
#
#
#
# def get_number_display(n):
#     """
#     :param n: a number
#     :return: a integer, if the number is whole, or a decimal
#     """
#     return int(n) if int(n) == n else n
#
#
#
# def get_weekdays_in_range(start, end):
#     """
#     :param start: a start date
#     :param end: an end date
#     :return: a list of dates that are weekdays
#     """
#     wd = []
#     while start <= end:
#         if start.weekday() < 5:  # ignore weekends
#             wd.append(start)
#         start += datetime.timedelta(days=1)
#     return wd
#
#
#
#
#
#
#
# def g_recaptcha_is_valid(token=None):
#     """
#     See the following links for more:
#     https://developers.google.com/recaptcha/docs/invisible
#     https://developers.google.com/recaptcha/docs/verify
#
#     :param token: a token posted via grecaptcha
#     :return: True if the token is valid, otherwise False
#     """
#     return requests.post(
#         'https://www.google.com/recaptcha/api/siteverify',
#         data={
#             'secret': settings.G_RECAPTCHA_SECRET_KEY,
#             'response': token
#         }
#     ).json().get('success', False) if token else False
#
#
#
# def insert_diff_tags(original, revised, p_tag='p', exclude_unchanged=False):
#     """
#     Adds tags to text to indicate the difference between the original and revised text.
#
#     :param original: the original text, where new lines indicate new paragraphs
#     :param revised: the revised text, where new lines indicate new paragraphs
#     :param p_tag: the tag to use to separate paragraphs, indicated by line breaks (defaults to "p").Set to None to
#         ignore paragraphs. If set, the line break count from original to revised should be the same. If they are not,
#         we'll, ignore line breaks
#     :param exclude_unchanged: if True, we'll exclude any unchanged "p_tag" blocks.
#     :return: the text with diff tags
#     """
#     def _add_tags(rm, add):
#         return '<span class="change">' + ('<span class="delete">' + ' '.join(rm) + '</span>' if rm else '') + ('<span class="add">' + ' '.join(add) + '</span>' if add else '') + '</span>'
#     ps = []
#     op = original.split('\n') if p_tag else [original]
#     rp = revised.split('\n') if p_tag else [revised]
#     if len(op) != len(rp):
#         op = [original]
#         rp = [revised]
#     for i, p in enumerate(op):
#         if p:
#             changed = False
#             np = []
#             add = []
#             rm = []
#             for d in difflib.ndiff(p.split(' '), rp[i].split(' ')):
#                 if d[0] == '?':
#                     continue
#                 t = d[2:]
#                 if d[0] == ' ':
#                     if add or rm:  # insert the change string before the next word
#                         np.append(_add_tags(rm, add))
#                         add = []
#                         rm = []
#                     np.append(t)
#                     continue
#                 if d[0] == '-':
#                     changed = True
#                     rm.append(t)
#                 else:
#                     changed = True
#                     add.append(t)
#             if add or rm:  # insert the change string before ending the paragraph
#                 np.append(_add_tags(rm, add))
#             if exclude_unchanged and not changed:
#                 continue
#             ps.append('<' + p_tag + '>' + ' '.join(np) + '</' + p_tag + '>' if p_tag else ' '.join(np))
#     return '\n'.join(ps)
#
#
#
# def mask_text(text, show, end=True, char='*'):
#     """
#
#     :param text: the text to mask
#     :param show: number of characters to reveal
#     :param end: set to True to place the mask characters at the end, False at the start
#     :return: the masked text
#     """
#     hide = char * (len(text) - show)
#     return text[:show] + hide if end else hide + text[-show:]
#
#
#
# def merge_nested_dicts(*dicts):
#     """
#     This method expects two or more dicts, all sharing the same basic form and merges both the main and nested dicts.
#     For example, consider the dicts below:
#
#         {"settings": {"on": False, "email": True}, "next": "return"}
#         {"settings": {"on": True}}
#         {"settings": {"title": "Send Email"}, "next": "save"}
#
#     When provided in this order, these will all merge into the following dict:
#
#         {"settings": {"on": True, "email": True, "title": "Send Email"}, next: "save"}
#
#     All nested dicts will be merged with their counterparts in prior dicts. Non-dict items will overwrite their
#     counterparts as normal.
#
#     NOTE: if for a particular key, we have both dict and non-dict values, we'll throw an error.
#
#     :param dicts: the dicts to be merged
#     :return: the new dict resulting from the merge
#     """
#     r = {}
#     for d in dicts:  # prep results
#         for k in d:
#             if isinstance(d[k], dict):  # set this key to {'_merge': [nested1, nested2 . . .]
#                 if k in r:
#                     if isinstance(r[k], dict):
#                         r[k]['_merge'].append(d[k])
#                     else:
#                         raise Exception('Attempting to merge dict %s with non-dict value "%s" for key "%s"' % (d[k], r[k], k))
#                 else:
#                     r[k] = {'_merge': [d[k]]}
#             elif k in r and isinstance(r[k], dict):
#                 raise Exception('Attempting to merge non-dict value "%s" with dicts %s for key "%s"' % (str(d[k]), r[k]['_merge'], k))
#             else:  # overwrite current value for this key with the latest one
#                 r[k] = d[k]
#     for k in r:  # at this point all dicts in the object should be in merge lists
#         if isinstance(r[k], dict) and '_merge' in r[k]:
#             args = r[k]['_merge']
#             r[k] = args[0] if len(args) == 1 else merge_nested_dicts(*args)
#     return r
#
#
#
# def join_on_values(values, model, app=None, field=None):
#     """
#     Reconstituting a queryset from a long list of ids using an IN clause is inefficient. The method detailed in the
#     link below uses a VALUES clause instead and performs a join. Use this on queries with oversized IN clauses to
#     improve efficiency.
#     https://stackoverflow.com/questions/24647503/performance-issue-in-update-query
#
#     :param values: the values to join on
#     :param model: a model instance or string of the form "APP.MODEL", "APP_MODEL", or "MODEL" (requires "app" argument)
#     :param app: the string app name; if "model" is not a model instance or does not contain the app, this must be provided
#     :param field: the field to join on (defaults to the primary key of "model")
#     :return: a RawQuerySet
#     """
#     if isinstance(model, str):
#         if not app:
#             app, model = model.replace('.', '_').split('_')
#         _model = apps.get_model(app_label=app, model_name=model)
#     else:
#         _model = model
#         app = model._meta.app_label
#         model = model._meta.model_name
#     if not field:
#         field = str(_model._meta.pk).split('.')[-1]
#     values = ','.join('(%d)' % v for v in values)
#     return _model.objects.raw(f'SELECT * FROM {app}_{model} INNER JOIN (VALUES {values}) vals(v) ON ({field} = v);')
#
#
#
# def move_m2m_relation(m2m, move_from, move_to):
#     """
#     Move members of an M2M relation from one object to another. For example, if I need to consolidate one Company into
#     another and need to move the first's sponsored MediaItem records to the next, I would use the following call:
#
#         move_m2m_relation(MediaItem.sponsors, COMPANY_1_ID, COMPANY_2_ID)
#
#     :param m2m: the M2M field (i.e. MediaItem.sponsors of class Company)
#     :param move_from: the object to move away from (i.e. a Company or Company id)
#     :param move_to: the object to move to (i.e. another Company or Company id)
#     """
#     column_name = m2m.rel.model._meta.model_name  # i.e. company
#     related_column_name = m2m.rel.related_model._meta.model_name  # i.e. mediaitem
#
#     objs = m2m.through.objects  # access the through table directly
#     src = objs.filter(**{column_name: move_from})
#     dest = objs.filter(**{column_name: move_to})
#     overlap = set([getattr(t, related_column_name + '_id') for t in src]).intersection( [getattr(t, related_column_name + '_id') for t in dest])
#     src.filter(**{related_column_name + '_id__in': list(
#         overlap)}).delete()  # kill related fields already present in the destination company
#     src.update(**{column_name: move_to})  # update the rest
#
#
#
# def readable_join(items, separator=', ', last='and '):
#     """
#     :param items: a list of items to join
#     :param separator:
#     :param last: the string to include between the last two items, not including the separator
#     :return: a human readable list of joined items (i.e. [1, 2, 3] yields "1, 2, and 3")
#     """
#     if not items:
#         return ''
#     items = list(map(str, items))
#     if len(items) == 2:
#         return items[0] + ' ' + last + items[1]
#     return separator.join(items[:-1]) + separator + last + items[-1] if len(items) > 1 else items[0]
#
#
#
# def register_custom_admin_view(**kwargs):
#     """
#     To register an arbitrary view underneath a particular app, apply this decorator. By default, the view will appear
#     under whatever app it is being registered to and will be named according to the view name.
#
#     :param kwargs: any custom kwargs to use in creating the entry; see register_mock_admin for possible kwargs,
#         noting that the view_func argument will be the decorated view function
#     :return: the decorator function
#     """
#     def decorator(view_func):
#         return register_mock_admin(view_func=view_func, **kwargs)
#     return decorator
#
#
#
# def register_mock_admin(app_label=None, model_name=None, urls=None, view_func=None, **kwargs):
#     """
#     Allows for the registration of arbitrary views under a particular app label / model name. For an even simpler
#     approach use the "register_admin_view" decorator. This function is based on one found in the following app:
#     https://github.com/ionelmc/django-admin-utils
#
#     :param app_label: the app label to which to register this view (defaults to the current app)
#     :param model_name: the model name under which to register this view (defaults to the view name)
#     :param urls: an array of url paths that maps view functions to their corresponding urls; this will be created
#         automatically from "view_func" when provided
#     :param view_func: a view function; when provided, "urls" will be generated automatically
#     :param kwargs: see the "_meta" class of "get_mock_model" for allowable kwargs
#     :return: a MockXModel admin class
#     """
#     def get_mock_model(**kwargs):
#         type_name = 'Mock%sModel' % model_name
#
#         class _meta:
#             abstract = False
#             app_config = kwargs['app_config']
#             app_label = kwargs['app_label']
#             model_name = kwargs['model_name']
#             module_name = kwargs['module_name']
#             object_name = kwargs['object_name']
#             swapped = False
#             verbose_name = kwargs['verbose_name']
#             verbose_name_plural = kwargs['verbose_name_plural']
#
#         return type(type_name, (object,), {'_meta': _meta})
#
#     if view_func:
#         app_label = app_label or view_func.__module__.split('.')[0]
#         model_name = model_name or view_func.__name__
#     if not app_label or not model_name:
#         raise Exception('You must enter an "app_label" and a "model_name" on which to base this admin.')
#     app_label = app_label.lower()
#     readable_name = model_name.replace('_', ' ').capitalize()
#     model_name = model_name.replace('_', '').lower()
#     if view_func:
#         urls = [path('', view_func, name='%s_%s_changelist' % (app_label, model_name))]
#     elif not urls:
#         raise Exception('You must provide a "urls" array with urls paths for the views you\'re adding.')
#     kwargs['app_label'] = app_label
#     kwargs.setdefault('app_config', None)
#     kwargs['model_name'] = model_name
#     kwargs.setdefault('module_name', model_name)
#     kwargs.setdefault('object_name', model_name)
#     kwargs.setdefault('verbose_name', readable_name)
#     kwargs.setdefault('verbose_name_plural', readable_name)
#     site = kwargs.pop('site', admin.site)
#
#     class AdminClass(admin.ModelAdmin):
#         def has_add_permission(*args, **kwargs):
#             return False
#
#         def has_change_permission(*args, **kwargs):
#             return False
#
#         def has_delete_permission(*args, **kwargs):
#             return False
#
#         def has_view_permission(*args, **kwargs):
#             return True
#
#         def get_urls(self):
#             def wrap(view):
#                 def wrapper(*args, **kwargs):
#                     return self.admin_site.admin_view(view)(*args, **kwargs)
#                 wrapper.model_admin = self
#                 return update_wrapper(wrapper, view)
#             return [URLPattern(url.pattern, wrap(url.callback), url.default_args, url.name) for url in urls]
#
#         @classmethod
#         def register(cls):
#             site.register((get_mock_model(**kwargs),), cls)
#
#     AdminClass.register()
#     return AdminClass
#
#
#
# def retrieve_remote_file(url, name=None, process=None):
#     """
#     Temporarily store a remote file, so that we can work with it. For example, we might use this to download
#     a file from a model field and send it as an attachment. To get a file from a file field, we would use the
#     following:
#
#         retrieve_remote_file(instance.file_field.url, 'MyFileName')
#
#     To save this file to another file field, we would would simply use the following:
#
#         instance.file_field = retrieve_remote_file(. . .)
#         instance.save()
#
#     Note that if "name" contains no extension, the extension will be obtained from the url.
#
#     :param url: the url of the remote file or a dict to pass as kwargs to request.get()
#     :param name: the name of the file (defaults to the file name in the url)
#     :param process: a callback that receives the file contents, filename, and file extension and should return the same
#         three parameters in a tuple, performing whatever manipulations are needed in between.
#     :return: the temporary file
#     """
#     if isinstance(url, dict):
#         d = requests.get(**url).content
#         url = url['url']
#     else:
#         d = requests.get(url).content
#     if not name:
#         name = url.split('?', 1)[0].rsplit('/', 1)[-1]
#     if '.' in name:
#         name, ext = name.rsplit('.', 1)
#     else:
#         ext = url.rsplit('.', 1)
#         ext = ext[-1] if len(ext) > 1 else ''
#     f = NamedTemporaryFile(delete=True)
#     if process:
#         d, name, ext = process(d, name, ext)
#     f.write(d)
#     tf = File(f, name=f'{name}.{ext}')
#     tf.file.seek(0)
#     return tf
#
#
#
# def retrieve_remote_image(url, options=None, name=None):
#     """
#     Like "retrieve_remote_file", but has certain common shortcuts for image manipulation via PIL. More advanced
#     manipulations may be done simply via a custom "process" callback of "retrieve_remote_file", modeled on this
#     function.
#
#     :param url: the url of the remote image or a dict to pass as kwargs to request.get()
#     :param options: a dict of options for modifying the image prior to save
#         - alpha: a number from 0-255 to execute "image.putalpha(alpha)" or False to remove the alpha channel
#         - format: the format to which to convert an image (e.g. jpeg, png, tiff, etc.)
#         - max_dims: a tuple with the maximum dimensions for an image, maintaining aspect ratio
#     :param name: the name of the file (defaults to the file name in the url)
#     :return: the temporary file
#     """
#     def process(d, name, ext):
#         NO_ALPHA = ['jpeg']
#         b = BytesIO()
#         i = Image.open(BytesIO(d))
#         f = options.get('format', None)
#         if f:
#             if not ext:
#                 ext = f
#             if f in NO_ALPHA and (i.mode in ('RGBA', 'LA', 'P')):  # kill the alpha channel for formats that don't support it
#                 i = i.convert('RGB')
#         t = options.get('alpha', None)
#         if t is False:  # remove alpha channel
#             i = i.convert('RGB')
#         elif isinstance(t, int):  # set image opacity
#             i.putalpha(t)
#         t = options.get('max_dims', None)
#         if t:  # make sure the image fits within these (W, H) dimensions
#             i = ImageOps.contain(i, t)
#         i.save(b, f)
#         return b.getvalue(), name, ext
#     return retrieve_remote_file(url, name, process if options else None)
#
#
#
# def safe_join(items, delimiter='<br>', wrap=('', '')):
#     """
#     :param items: a list of items to join; if not strings, we will transform them via str()
#     :param divider: the delimiter to join by
#     :param wrap: a two member tuple with the opening / closing tags to wrap results in or one of the following shortcut keywords:
#      - nowrap: wraps items in non-wrapping div
#      - ol: makes an OL of items
#      - ul: makes a UL of items
#     :return: safe html for display
#     """
#     if items:
#         if not isinstance(items[0], str):
#             items = [str(i) for i in items]
#         if isinstance(wrap, str):
#             if wrap == 'nowrap':
#                 wrap = ('<div style="white-space: nowrap">', '</div>')
#             elif wrap == 'ul':
#                 wrap = ('<ul><li>', '</li></ul>')
#                 delimiter = '</li><li>'
#             elif wrap == 'ol':
#                 wrap = ('<ol><li>', '</li></ol>')
#                 delimiter = '</li><li>'
#         return mark_safe(wrap[0] + delimiter.join(items) + wrap[1])
#     return ''
#
#
#
# def safe_link(url, display, attrs=''):
#     """
#     :param url: the link url
#     :param display: the display text for the link
#     :param attrs: any attributes to include in the tag
#     :return:
#     """
#     return mark_safe('<a href="%s" %s>%s</a>' % (url, attrs, display))
#
#
#
# def save_remote_image_to_field(url, image_field, options=None, name=None):
#     """
#     :param url: the url of the remote image or a dict to pass as kwargs to request.get()
#     :param image_field: the image field to which the image should be saved
#     :param options: image options to pass to the "retrieve_remote_image" method
#     :param name: the name to which the file should be written (extension will be gotten from the url)
#     """
#     f = retrieve_remote_image(url, options, name)
#     image_field.save(f.name, f)
#
#
#
# def send_mail(to, subject, html=None, template=None, context=None, files=None, **kwargs):
#     """
#     A wrapper for EmailMultiAlternatives, which is a subclass of EmailMessage.
#     https://docs.djangoproject.com/en/4.1/topics/email/#the-emailmessage-class
#     https://docs.djangoproject.com/en/4.1/_modules/django/core/mail/message/#EmailMessage
#
#     :params to: a list, tuple, or comma-delimited string of recipient addresses
#     :params subject: the subject line of the email
#     :params html: if provided, we'll attach this html version of the email and will ignore "template"
#     :params template: if provided (and "html" is not), we'll use the template at this path to generate the html for
#         the email. The template will automatically receive all "kwargs" and arguments as context, in addition to
#         "settings", which will contain Django settings. Additional context may be included in the "context" dict.
#     :params files: a list of file tuples / files to attach to the email. The most verbose form for each member of the
#         list is (FILENAME, CONTENT, MIMETYPE), corresponding to the arguments for the "attach" method. MIMETYPE will
#         be guessed if not provided. In certain cases where a filename can be derived from the object in CONTENT,
#         this object may be passed in place of the full tuple. For example, to attach the jpg image in an ImageField
#         called "cover_image", simply pass the ImageField itself, and a file called "cover_image.jpg" will be attached.
#
#         Special Cases:
#         - CSV attachment: Pass something of the form ('MyCsvFile.csv', ROWS, FIELDNAMES) where ROWS and FIELDNAMES
#             correspond to the like-named arguments of "get_csv_content". This is simply a shortcut for attaching CSV
#             data as a file without importing this method and is equivalent to passing the following: ('MyCsvFile.csv',
#             get_csv_content(ROWS, keys=FIELDNAMES))
#     :params kwargs: any of the following non-required arguments of the EmailMessage class:
#         body, from_email, bcc, connection, attachments, headers, cc, reply_to.
#     :return: the number of emails sent
#
#     NOTE: if either html or template is provided, we'll use these to derive the html of the email and, assuming no
#         "body" is specified in "kwargs", will strip this html of its tags to create a textual version of the email.
#     """
#     if isinstance(to, str):
#         to = to.split(',')
#     kwargs.update({  # expected arguments for the EmailMessage class, also passed into template context
#         'to': to,
#         'subject': subject,
#         'from_email': kwargs.get('from_email', settings.DEFAULT_FROM_EMAIL),
#         'headers': kwargs.get('headers', {}),
#     })
#     kwargs['headers'].setdefault('Reply-To', kwargs['from_email'])
#     if not html and template:
#         html = loader.get_template(template).render({
#             'settings': settings,
#             'files': files,
#             **(context or {}),
#             **kwargs
#         })
#         if 'body' not in kwargs:
#             kwargs['body'] = strip_tags(html)
#     email = EmailMultiAlternatives(**kwargs)
#     if html:
#         email.attach_alternative(html, 'text/html')
#     if files:
#         for f in files:
#             name = lname = mt = ''
#             if isinstance(f, (list, tuple)):  # (FILENAME, CONTENT, MIMETYPE)
#                 if len(f) > 2:
#                     name, f, mt = f
#                 else:
#                     name, f = f
#             if name:
#                 lname = name.lower()
#             if '.csv' in lname:
#                 if isinstance(f, (list, tuple)):
#                     f = get_csv_content(f, keys=mt)
#                     mt = None
#             elif isinstance(f, File):
#                 if not name:
#                     name = f.name.split('/')[-1]
#                 f = f.read()
#             elif isinstance(f, HttpResponse):
#                 f = f.content
#             if not name:
#                 name = str(int(time.time()))
#             email.attach(name, f, mt)
#
#     # # Attach files
#     # for f in file_objs:
#     #     if isinstance(f, File):
#     #         # For Django file objects
#     #         try:
#     #             contents = f.file.getvalue()
#     #         except:
#     #             contents = f.read()
#     #         email.attach(f.name, contents, mimetypes.guess_type(f.name)[0])
#     #     else:
#     #         # For files that have been opened with the "open" function, or the string path of that file
#     #         if not isinstance(f, str):
#     #             f = f.name
#     #         email.attach_file(f, mimetypes.guess_type(f)[0])
#
#     return email.send()
#
#
#
# def thumb(file, alias='default'):
#     """
#     :param file: any file field
#     :param alias: an easy thumbnails alias
#     :return: the html for this thumbnail
#     """
#     src = thumb_url(file, alias)
#     return mark_safe(f'<img src="{src}">') if src else ''
#
#
#
# def thumb_url(file, alias='default'):
#     """
#     :param file: any file field
#     :param alias: an easy thumbnails alias
#     :return: the url of the image, if this is an ImageFieldFile, or of an icon associated with the file type
#     """
#     if file:
#         if file.__class__ == ImageFieldFile:
#             try:
#                 return get_thumbnailer(file)[alias].url
#             except:  # programmatically the image appears to be there, but thumbnailer couldn't retrieve it
#                 return settings.STATIC_URL + 'my/images/missing.jpg'
#         else:
#             return settings.STATIC_URL + 'my/images/%s.jpg' % ('pdf' if file.name.endswith('.pdf') else 'file')
#     return ''
#
#
#
# def update_redirects(old_path, new_path, sites):
#     """
#     Make updates to Redirect objects based on the urls / sites provided. This will not only add any
#     new redirects, but it will update existing redirects that point to the url being redirected from.
#     For example, if we are redirecting A->B and add another redirect B->C, we will update the first
#     redirect to A->C to forego the need for multiple redirects. Or if we change back to the old path,
#     such that we now have C->A, we will remove any redirects originating at A.
#
#     :param old_path: the url to redirect from
#     :param new_path: the url to redirect to
#     :param sites: a list of Site objects or site ids to consider
#     """
#     if old_path and new_path and sites:
#         redirects = Redirect.objects.filter(site__in=sites)
#         redirects.filter(old_path=new_path).delete()  # remove any redirects pointing away from new_path
#         redirects.filter(new_path=old_path).update(new_path=new_path)  # change any redirects pointed at old_path to new_path
#         for s in sites:  # create redirects for the indicated sites
#             r, _ = Redirect.objects.get_or_create(site=s, old_path=old_path)
#             r.new_path = new_path
#             r.save()
