from django.db import models

from djangoat.db.fields import MonoTextarea, PrettyJSONField




class _SectionControlMixin(models.Model):
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

    # If column content width is set, then we'll insert the items for this section into columns.
    column_content_width = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel width of column content containers (including left and right padding); enter a single'
                  ' number to indicate the width of equal width columns (we\'ll calculate columns per row via'
                  ' the newsletter width) or enter "X|Y|Z" to indicate both the number of columns and their'
                  ' respective widths')
    column_content_height = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text='Pixel height of column content containers (including top and bottom padding); leave blank to'
                  ' omit height constraints')

    # All fields above will be merged into this context object before being passed on to the builder.
    # The builder will then use it to construct the section.
    context = PrettyJSONField(null=True, blank=True,
        help_text='A JSON dict of context values for this section, as well as certain special values, such as'
                  ' "querysets"; section field values will be automatically included in context under their'
                  ' field names')

    class Meta:
        abstract = True



class Newsletter(_SectionControlMixin):
    styles = MonoTextarea(null=True, blank=True,
        help_text='When filled, this template will be used in place of the "styles" template specified in'
                  ' the <b>context</b> field. Note that this is meant primarily for live fixes. Long-term'
                  ' style updates should ideally live in a styles template in the template directory.')



class NewsletterSectionType(_SectionControlMixin):
    template = MonoTextarea(null=True, blank=True,
        help_text='When filled, this template will be used for all sections of this type instead of the'
                  ' "template" specified in the <b>context</b> field. Note that this is meant primarily'
                  ' for live fixes. Long-term templates should ideally live in the template directory.')



class NewsletterSection(_SectionControlMixin):
    type = models.ForeignKey(NewsletterSectionType, null=True, blank=True, on_delete=models.SET_NULL)
    template = MonoTextarea(null=True, blank=True,
        help_text='When filled, this template will be used in place of the "template" specified in the'
                  ' <b>context</b> field. Note that this is meant primarily for live fixes. Long-term'
                  ' templates should ideally live in the template directory.')






