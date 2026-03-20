from django.shortcuts import render
from django.utils import timezone
from django.utils.safestring import mark_safe

from djangoat.utils import get_seconds_from_duration_string

from djangoat import DATA



# FUNCTIONS
def add_example_table(ctx, func, *args):
    """
    Add a table with example calls and respective results to template context.

    :param ctx: template context
    :param func: the function to call
    :param args: a list of argument lists to use in each example call
    """
    calls = []
    for eas in args:
        if not isinstance(eas, (list, tuple)):
            eas = [eas]
        calls.append((func.__name__ + '(' + ', '.join([f'"{ea}"' if isinstance(ea, str) else str(ea) for ea in eas]) + ')', func(*eas)))
    ctx[func.__name__] = mark_safe(
        '<table class="examples">' +
          ''.join([f'<tr><td><pre><code class="language-python">{c}</code></pre></td><td class="hljs hljs-{"string" if isinstance(r, str) else "number"}">{r}</tr><td>' for c, r in calls]) +
        '</table>'
    )



# VIEWS
def template_tags(request):
    DATA.update({
        'cube_func': lambda x: x ** 3,
        'power_func': lambda x, y: x ** y,
        'range_func': lambda x: range(x)
    })


    return render(request, 'template_tags.html', {
        'DATE_FORMAT': 'F jS, Y',
        'TIME_FORMAT': 'F jS, Y g:i a',
        'NUM_DICT': {
            'one': 1,
            'two': 2,
            'three': 3,
        },
        'now': timezone.now(),
    })



def utils(request):
    ctx = {}
    add_example_table(ctx, get_seconds_from_duration_string, '2d4h6m', '6m4h2d', '2d;4h;6m', '2d, 4h, 6m', '2 dy, 4 hr, 6 min', '2 days, 4 hours, 6 minutes')
    return render(request, 'utils.html', ctx)
