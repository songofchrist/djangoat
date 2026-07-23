from django.shortcuts import render

from djangoat.builders import Newsletter




class NewsletterBuilder(Newsletter):
    pass



def newsletter_preview(request):
    builder = NewsletterBuilder({
        'padding_top': 8,
        'padding_sides': 16,
        'padding_bottom': 8
    })
    builder.add_section({
        'padding_top': 0,
        'padding_sides': 0,
        'padding_bottom': 0,
        'template': 'newsletters/shared/header.html',
    })
    builder.build(True)
    return render(request,'newsletters/preview.html', {
        'builder': builder
    })