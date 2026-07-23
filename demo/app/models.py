from django.db import models




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