# -*- coding: utf-8 -*-
import calendar
import csv
import datetime
import difflib
import json
import random
# import requests
# import time
import types
#
# # from easy_thumbnails.files import get_thumbnailer
# from functools import update_wrapper
from io import BytesIO, StringIO
# # from PIL import Image, ImageOps
# from tempfile import NamedTemporaryFile
#
from django.apps import apps
# from django.conf import settings
# from django.core.mail import EmailMultiAlternatives
# from django.core.files import File
# from django.contrib import admin
# from django.contrib.redirects.models import Redirect
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import F
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

        get(response, "books", 0, "awards", 0)

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
    :param rows: see `get_csv_content`_ for acceptable formats
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



def get_csv_rows_from_queryset(queryset, fields, derived_fields=None, dynamic_columns=None, prettify_headers=True, agg_delimiter=', '):
    """Returns a list of lists suitable for building a CSV file or spreadsheet.

    **BASIC USAGE**

    ``fields`` is used to populate CSV columns from ``queryset`` and may take one of the following forms:

    ..  code-block:: python

        (
            "field",
            "method",
            "choice_field",
            "rep__user__name"
            "_annotated__avg",
            "_derived",
            ("field", "Field With Custom Title"),
            ("method", "Method With Custom Title")
            ("choice_field", "Choice Field", {V1: TEXT1, V2: TEXT2 . . .}),
            ("rep__user__name", "Auto Annotated User Name"),
            ("_annotated__avg", "Annotated Average"),
            ("_derived", "Programmatically Derived")
        )

    In general, all fields are specified in one of two ways:

    1. Provide only the field name, which doubles as the column header
    2. Provide a tuple of the form :python:`("field_name", "Column Header")`

    The field name in this scheme may be any one of the following:

    - A field or method on a queryset instance
    - A field on a related model, specified using standard join notation
    - An annotated field
    - A derived field

    When ``field`` is a standard field or method, simply specify the field or method, and the resultant value for
    each record in the queryset will be used to populate the associated column. For choice fields, when the value
    retrieved is not display-worthy (e.g. an integer), a per-value display dict may be passed as the third member of
    a tuple. This will be used to map field values to the display values with which we want to populate the associated
    column.

    By default, fields that contain a "__" in them will automatically be retrieved via annotation. For example,
    "rep__user__name" would result in the following annotation:

    ..  code-block:: python

        queryset = queryset.annotate(rep__user__name=F("rep__user__name"))

    Thus, we can represent any foreign key field in our output. If the join contains a many-to-many relationship, we
    can indicate this by appending a "+" sign. For example, "rep__tasks__title+" (all tasks assigned to a rep) would
    result in the following annotation:

    ..  code-block:: python

        queryset = queryset.annotate(
            rep__tasks__title=StringAgg("rep__tasks__title", AGG_DELIMITER, distinct=True)
        )

    When auto-annotation proves insufficient, we may reference manual annotations by prepending "_" to a field name.
    For example, we could define and reference a "_tasks" field as follows:

    ..  code-block:: python

        get_csv_rows_from_queryset(
            queryset.annotate(_tasks=StringAgg("rep__tasks__title", ", ", distinct=True)),
            ["_tasks", . . .]
            . . .
        )

    This would produce results identical to passing "rep__tasks__title+" in ``fields``.

    **ADVANCED USAGE**

    In some instances, the values we want to include will either be difficult or impossible to derive via annotation.
    In these cases, we can use ``derived_fields`` to supply the data for these fields. For example, suppose we track
    user visits to our sites in a way that makes them difficult to annotate. We might use the following to add this
    data to the CSV:

    ..  code-block:: python

        def get_derived_fields(queryset):
            . . .
            RETURN_VALUE = {
                "_cool": {USER_1_PK: 5, USER_2_PK: 3 . . .},
                "_awesome": {USER_1_PK: 1, USER_2_PK: 30 . . .},
                "_rockin": {USER_2_PK: 8 . . .}
            }
            return RETURN_VALUE

        get_csv_rows_from_queryset(
            user_queryset,
            [
                "first_name",
                "last_name",
                ("_cool", "CoolSite Visits"),
                ("_awesome", "AwesomeSite Visits"),
                ("_rockin", "RockinSite Visits")
            ],
            derived_fields=get_derived_fields,
            . . .
        )

    We see here that ``derived_fields`` takes a function that returns a dict whose keys correspond to a field in
    ``fields``. Each key then references another dict, which in this case contains user primary key / user visit pairs.
    For each row in :python:`user_queryset`, we expect to find the visits for field ``SITE_FIELD`` in
    :python:`RETURN_VALUE[SITE_FIELD][USER_PK]` and will use that data to populate the associated row.

    In other instances, we may need to dynamically add columns to the CSV, some of which may need to appear in
    different orders or not at all, depending on the records in ``queryset``. In these cases, instead of using
    ``derived_fields``, which is suited for static columns, we would pass a function of the following form in
    ``dynamic_columns``:

    ..  code-block:: python

        def get_dynamic_columns(queryset):
            . . .
            RETURN_VALUE = (
                [
                    "Header 1",
                    "Header 2",
                    . . .
                ],
                {
                    RECORD_1_PK: ["Record 1, Value 1", "Record 1, Value 2", . . .],
                    RECORD_2_PK: ["Record 2, Value 1", "Record 2, Value 2", . . .],
                    RECORD_3_PK: ["Record 3, Value 1", "Record 3, Value 2", . . .],
                    . . .
                }
            )
            return RETURN_VALUE

    Values associated with each record id should occur in the same order as the headers in the first member of the
    return tuple and should have the same number of members. Both headers and record data will be appended to the end
    of each row.

    If all of these methods prove insufficient, we may try one final approach. ``fields`` may also be a tuple of
    a function and a list of headers. We might do something like the following, for example:

    ..  code-block:: python

        get_csv_rows_from_queryset(
            user_queryset,
            (
                lambda user: [user.first_name, user.last_name, user.age, user.sex]
                ["First Name", "Last Name", "Age", "Sex"]
            ),
            . . .
        )

    The function should take a record from the queryset and return the row for that queryset. This approach is both
    the most straightforward and versatile, but it is also the least efficient, especially when each function call
    requires numerous queries. Generally, it should be used only as a last resort.

    :param queryset: the queryset from which to retrieve ``values``
    :param fields: a tuple or list of fields or pseudo-fields with whose values to populate columns
    :param derived_fields: a function that takes `queryset` and returns a dictionary of derived field results
    :param dynamic_columns: a function that takes `queryset` and returns a tuple of headers and a dict of data lists
        keyed to queryset primary keys; the data list should be the same length and order as the headers to which
        they correspond
    :param prettify_headers: when a header is not explicitly provided, set this to True to split the field by "__",
        title case the last string, and replace any underscores therein with spaces, and return the result as a header
    :param agg_delimiter: the delimiter to use when aggregating many-to-many values into a string
    :return: a list of lists, ready to be fed into `get_csv_content`_ or anything that makes use of it
    """
    if not queryset:
        return []
    if dynamic_columns:
        dch, dcr = dynamic_columns(queryset)  # dynamic header list / per-primary-key value lists
    else:
        dch, dcr = [], {}
    f = fields[0]
    if isinstance(f, types.FunctionType):  # for (FUNCTION, HEADERS), use the passed function to derive each row
        headers, rows = fields[1], [f(d) + dcr.get(d.pk, []) for d in queryset]
    else:
        df = derived_fields(queryset) if derived_fields else {}
        headers = []
        maps = {}
        aafields = {}
        for i, f in enumerate(fields):  # derive headers
            if isinstance(f, str):
                headers.append(f.split('__')[-1].replace('_', ' ').title().lstrip() if prettify_headers else f)
            else:
                fields[i] = f[0]
                headers.append(f[1])
                if len(f) > 2:  # mapping was included for this field
                    maps[f[0]] = dict(f[2])
        for i, f in enumerate(fields):  # check for fields needing annotation
            if f[0] != '_' and '__' in f:
                if f[-1] == '+':  # many-to-many annotation
                    f = f[:-1]
                    fields[i] = f
                    aafields[f] = StringAgg(f, agg_delimiter, distinct=True),
                else:  # foreign key annotation
                    aafields[f] = F(f)
        if aafields:  # add auto-annotations
            queryset = queryset.annotate(**aafields)
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
                            m = df.get(f, None)  # get the derived id / value dict for this field, if one exists
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



def get_json_file(filename, rows, keys=None, add_headers=True):
    """Returns a JSON file download response.

    :param filename: the name of the JSON file, without the ".json" extension
    :param rows: see `get_csv_content`_ for acceptable formats
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



def get_json_file_contents(path):
    """Returns a dict with the contents of the file at ``path``.

    If the specified file does not exist or is poorly formatted, an empty dict will be returned instead.

    :param path: the path to a json file
    :return: a dict of file contents
    """
    try:
        with open(path, 'r') as f:
            c = f.read()
            if c:
                return json.loads(c)
    except:
        pass
    return {}



def get_masked_text(text, show=4, start=False, char='*'):
    """Returns a masked string.

    ..  code-block:: python

        text = "MyPassword123"
        get_masked_text(text)  # "MyPa*********"
        get_masked_text(text, 7)  # "MyPassw******"
        get_masked_text(text, start=True)  # "*********d123"
        get_masked_text(text, char="-")  # "MyPa---------"

    :param text: the text to mask
    :param show: the number of characters to reveal
    :param start: if True, mask characters from the start of the text, otherwise from the end
    :param char: the character with which to mask ``text``
    :return: the masked text
    """
    hide = char * (len(text) - show)
    return hide + text[-show:] if start else text[:show] + hide



def get_n_digit_string(n):
    """Returns a string of ``n`` digits, including leading zeros.

    For example, for an ``n`` of 6, we would get a string of characters between "000000" and "999999" inclusive.

    :param n: how many digits the string should be
    :return: the string
    """
    s = 10 ** int(n)
    return str(random.randrange(s, s * 2))[1:]



def get_offset_date(date, months=1, day=1):
    """Returns a date offset from ``date`` by ``months`` and set to ``day``.

    Occasionally, we want to create a date range offset from a particular date. This is easy enough using a delta of
    days, but when we want to jump forward or back by X months, calculations require a bit more attention, given the
    variable number of days in each month. This function removes that complexity. Consider the examples below:

    ..  code-block:: python

        date = datetime.date(2021, 10, 4)
        get_offset_date(date)  # 2021-11-01
        get_offset_date(date, -1)  # 2021-09-01
        get_offset_date(date, 5, 15)  # 2022-03-15
        get_offset_date(date, -5, 15)  # 2021-05-15
        get_offset_date(date, -10)  # 2020-12-01
        get_offset_date(date, -22)  # 2019-12-01
        get_offset_date(date, 22)  # 2023-08-01
        get_offset_date(date, 22, None)  # 2023-08-31

    :param date: the reference date
    :param months: months forward (positive) or back (negative)
    :param day: an integer day or ``None`` to get the last day of the given month
    :return: a new date
    """
    y = date.year
    m = date.month + months
    if months:
        if m < 1:
            y += int(m / 12) - 1
            m = 12 + (m % 12)
        elif m > 12:
            y += int(m / 12)
            m = m % 12
    return datetime.date(y, m, day or calendar.monthrange(y, m))



def get_queryset_by_keys(keys, model, field=None):
    """Returns a RawQuerySet joined on ``keys``.

    When we pass a long-running process to a task, we'll often have to reconstitute a queryset using the primary
    keys of its members. Doing this with an ``IN`` clause can be inefficient. A faster alternative is to join the
    table on these keys using a ``VALUES`` clause. This function, derived from a
    `solution on Stack Overflow <https://stackoverflow.com/questions/24647503/performance-issue-in-update-query>`__,
    simplifies this process.

    :param keys: the primary keys to join on
    :param model: a model or string suitable for ``apps.get_model``
    :param field: the field to join on; if unspecified, it will default to the primary key of ``model``
    :return: a RawQuerySet
    """
    if isinstance(model, str):
        model = apps.get_model(model)
    app = model._meta.app_label
    model = model._meta.model_name
    if not field:
        field = str(model._meta.pk).split('.')[-1]
    values = ','.join(f'({v})' for v in keys)
    return model.objects.raw(f'SELECT * FROM {app}_{model} INNER JOIN (VALUES {values}) vals(v) ON ({field} = v);')



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



def get_text_diff(original, revised, p_tag='p'):
    """Returns text with tags indicating the difference between the ``original`` and ``revised`` text.

    Suppose an editor asks a friend or ChatGPT to proofread an article he's written. The friend edits and returns it.
    The editor now needs to be able to see what changes were made at a glance, so he can decide which changes to
    accept and which to reject. This function accepts both the editor's ``original`` text and the ``revised`` text
    and returns text that includes tags that can be styled and displayed to quickly indicate where changes were made.

    By default, changes are computed per paragraph, indicated by new lines. This assumes that both versions of a text
    have the same number of paragraphs. If they don't, we'll ignore paragraph divisions and simply computer the
    difference on the text as a whole.

    :param original: the original text, where new lines indicate new paragraphs
    :param revised: the revised text, where new lines indicate new paragraphs
    :param p_tag: the tag to use to separate paragraphs, indicated by line breaks; set to None to
        ignore paragraphs
    :return: the text with diff tags
    """
    add_tags = lambda r, a: '<span class="change">' + (f'<span class="delete">{" ".join(r)}</span>' if r else '') + (f'<span class="add">{" ".join(a)}</span>' if a else '') + '</span>'
    ps = []
    op = original.split('\n') if p_tag else [original]
    rp = revised.split('\n') if p_tag else [revised]
    if len(op) != len(rp):  # ignore paragrpahs, adding <br> tags for display purposes
        op = [op.join('<br>\n')]
        rp = [rp.join('<br>\n')]
    for i, p in enumerate(op):
        if p:
            changed = False
            np = []
            add = []
            rm = []
            for d in difflib.ndiff(p.split(' '), rp[i].split(' ')):
                if d[0] == '?':
                    continue
                t = d[2:]
                if d[0] == ' ':
                    if add or rm:  # insert the change string before the next word
                        np.append(add_tags(rm, add))
                        add = []
                        rm = []
                    np.append(t)
                    continue
                if d[0] == '-':
                    changed = True
                    rm.append(t)
                else:
                    changed = True
                    add.append(t)
            if add or rm:  # insert the change string before ending the paragraph
                np.append(add_tags(rm, add))
            ps.append(f'<{p_tag} class="{"changed" if changed else "unchanged"}">{" ".join(np)}</{p_tag}>' if p_tag else ' '.join(np))
    return '\n'.join(ps)



def get_days_in_range(start, end):
    """Returns a tuple of weekday and non-weekday dates between ``start`` and ``end``.

    :param start: a start date
    :param end: an end date
    :return: a tuple of weekday dates and non-weekday dates, inclusive of ``start`` and ``end``
    """
    wd = []
    we = []
    d1 = datetime.timedelta(days=1)
    while start <= end:
        if start.weekday() < 5:  # weekdays
            wd.append(start)
        else:  # weekends
            we.append(start)
        start += d1
    return wd, we



def get_xls_file(filename, rows, keys=None, add_headers=True):
    """Returns a simple XLS file download response.

    Note that this function requires the `xlwt package <https://pypi.org/project/xlwt/>`__.

    :param filename: the name of the XLS file, without the ".xls" extension
    :param rows: see `get_csv_content`_ for acceptable formats
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

    Note that this function requires the `openpyxl package <https://pypi.org/project/openpyxl/>`__.

    :param filename: the name of the XLSX file, without the ".xlsx" extension
    :param rows: see `get_csv_content`_ for acceptable formats
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






#
#
#

#
#
#
#
#
#

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

#
#
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
