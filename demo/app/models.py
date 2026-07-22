from django.db import models

from djangoat.builders import Newsletter
from djangoat.db.fields import PrettyJSONField




class Company(models.Model):
    title = models.CharField(max_length=100)
    url = models.URLField(max_length=200, null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='companies', null=True, blank=True)

    class Meta:
        ordering = 'title',
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.title



class NewsletterBaseSection(models.Model):
    # Each newsletter section is its own TD. These determine the padding on that TD.
    padding_top = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel padding at the top of the section container; defaults to 4')
    padding_sides = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel padding on the left and right of the section container; defaults to 6')
    padding_bottom = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel padding at the bottom of the section container; defaults to 4')

    # Within each section TD will be a place for content. This will either be a full width table for
    # single-column content or a responsive "columns" DIV each of whose child DIVs contains a table
    # with its own content. These values will be applied to the content TD of these tables.
    content_padding_top = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel padding at the top of content containers; defaults to the value of "padding bottom"')
    content_padding_sides = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel padding on the left and right of content containers; defaults to the value of "padding'
                  ' sides"')
    content_padding_bottom = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel padding at the bottom of content containers; defaults to the value of "padding top"')
    column_content_width = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel width of column content containers (including left and right padding); enter a single'
                  ' number to indicate the width of equal width columns (we\'ll calculate columns per row via'
                  ' the newsletter width) or enter "X|Y|Z" to indicate both the number of columns and their'
                  ' respective widths')
    column_content_height = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel height of column content containers (including top and bottom padding); leave blank to'
                  ' omit height constraints')
    context = PrettyJSONField(null=True, blank=True,
        help_text='A JSON dict of context values for this section, as well as certain special values, such as'
                  ' "querysets"; section field values will be automatically included in context under their'
                  ' field names')

    class Meta:
        abstract = True

# class Newsletter(models.Model):
#     pass
#
#
#
# class NewsletterSection(models.Model):
#     pass



class NewsletterSectionType(NewsletterBaseSection):
    section_type_only = models.CharField(max_length=100, null=True, blank=True)
    pass



class Post(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey('auth.User', related_name='posts', on_delete=models.CASCADE)
    body = models.TextField(null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    file = models.FileField(null=True, blank=True)
    publish_date = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True, related_name='posts')
    sponsors = models.ManyToManyField(Company, through='PostSponsor', blank=True, related_name='posts')

    class Meta:
        ordering = 'title',

    def __str__(self):
        return self.title

    def get_byline(self, include_date=False, include_time=False):
        name = f'by {self.author.first_name} {self.author.last_name}'
        if include_date:
            name += ' on ' + self.publish_date.strftime("%B %d, %Y")
            if include_time:
                name += ' at ' + self.publish_date.strftime("%I:%M %p")
        return name


class PostSponsor(models.Model):
    order = models.PositiveSmallIntegerField(default=0)
    post = models.ForeignKey(Post, related_name='post_sponsors', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, related_name='post_sponsors', on_delete=models.CASCADE)



class Tag(models.Model):
    title = models.CharField(max_length=100)

    class Meta:
        ordering = 'title',

    def __str__(self):
        return self.title


# TODO make Newsletter, NewsletterSection, NewsletterSectionType models
# TODO build newsletter_preview (basically make a functioning system that can be modeled after)
# TODO at end of preview, show html within textarea, so it can be copied / pasted
# TODO make a ? clickable button for each section; when clicked show the json object used to create the section in one text area and the html for that section in another textarea