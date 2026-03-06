from django.shortcuts import render
from django.utils.safestring import mark_safe

from djangoat.utils import get_seconds_from_duration_string



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
          ''.join([f'<tr><td><pre><code class="language-python">{c}</code></pre></td><td class="hljs hljs-number">{r}</tr><td>' for c, r in calls]) +
        '</table>'
    )



# VIEWS
def template_tags(request):
    return render(request, 'template_tags.html')



def utils(request):
    ctx = {}
    add_example_table(ctx, get_seconds_from_duration_string, '2d4h6m', '6m4h2d', '2d;4h;6m', '2d, 4h, 6m', '2 dy, 4 hr, 6 min', '2 days, 4 hours, 6 minutes')
    return render(request, 'utils.html', ctx)
