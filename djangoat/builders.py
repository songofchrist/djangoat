import base64
import json
import requests

from djangoat.utils import get_json_file_contents




class Newsletter(object):
    """Aids in constructing basic section-based newsletters that will look as expected in a variety of clients.

    The steps to newsletter creation are as follows:
    1. Define types of sections, providing a default section context object to be used will all sections of that type
    2. Add sections, providing a context object unique to each
    3. Build the newsletter section by section:
        a. Process the section context, substituting in and limiting any querysets passed in
        b. Render the section according to its designated template and store it in the section list
    4. Join sections together to form the newsletter body
    5. Render the body and styles into the final newsletter html

    Read the comments on the method below for more.
    """
    name = ''           # a string identifier for this newsletter
    html = ''           # the full newsletter HTML, including both HEAD (with styles) and BODY tags
    html_body = ''      # the HTML for the BODY tag (includes inlined styles but no STYLE tags)
    html_head = ''      # the HTML for the HEAD tag, excluding the STYLE tag
    html_style = ''     # the CSS for the STYLE tag included in the HEAD
    subject = ''        # the subject line of the email
    text = ''           # a textual version of the email

    def __init__(self, *args, **kwargs):
        """
        ``base_querysets`` is where we define any querysets that we'll be using in the creation of the
        newsletter. For example, we might set this to the following:

        ..  code-block:: python

            {
                'recent_events': Event.objects.filter(start_date__range=(30_DAYS_AGO, NOW)),
                'near_events': Event.objects.filter(start_date__range=(NOW, 30_DAYS_FROM_NOW)),
                'far_events': Event.objects.filter(start_date__gt=30_DAYS_FROM_NOW),
            }

        Note that we've not limited these querysets to only X items, since we may reuse them from one section to
        the next and may want varying numbers of items in each. These are BASE QUERYSETS meant to be filtered and
        limited as we add each section. For example, when adding a section, we might add the following to that
        section's ``context``:

        .. code-block:: python

            {
                'querysets': [
                    {
                        'key': 'far_events',
                        'filter': {
                            'is_for_kids': 1
                        },
                        'limit': 2
                        'as': 'far_kid_events'
                    },
                    {
                        'key': 'far_events',
                        'exclude': {
                            'is_for_kids': 1
                        },
                        'limit': 1
                    }
                ]
            }

        When we find "querysets" in section context, we'll remove it from context and inject whatever querysets
        its contents require. Both of the above will start with the "far_events" queryset and build off of that.
        This first will result in a context variable of "far_kids_events", containing at most 2 event instances,
        and the second in a context variable of "far_events" (since no "as" was specified), containing at most
        1 event instance. These will then be marked as used and made available for use in the template.

        See the ``add_section`` method for more on special context keys like "querysets" and limitations on the
        use of "filter", "exclude", and "limit" for each.
        """
        self.base_querysets = {}
        """
        If I'm populating multiple different sections using the same base queryset, I want to be certain that I
        don't get duplicates of previous sections in later sections. This dict tracks used primary keys by queryset
        type. For example:

        {
            'books': set(),
            'events': set(),
            'posts': set()
        }

        When we pass a queryset keyed to "books" into a section's context, any of these that are rendered in
        that section will have their primary keys added to the "books" set, so that they can be excluded from
        subsequent sections.
        """
        self.used_item_pks_by_model_class = {}
        """
        This works similarly to ``used_item_pks_by_class``, but it tracks items on a per-section basis. For
        example:
        
        {
            SECTION_1_KEY : {
                'ALL': [],
                'books': set(),
                'posts': set()
            }
            SECTION_2_KEY : {
                'ALL': [],
                'events': set(),
                'posts': set()
            }
        }
        
        Seeing the above, we'd expect section one to reference one or more books and posts and section two to
        reference one or more events and posts. This breakdown may be useful for recording exactly what content
        content appeared in a given newsletter, so that it can be used to determine the content of future
        sends.
        """
        self.used_items_by_section_key = {}

    def add_section(self, context):
        """Register a new section to the newsletter builder.

        If this sections is of a particular type, calculate the final section context by combining that type's
        context with the ``context`` provided and return the result.

        :param context: context or string type
        :return: the context of the section added
        """

    def build(self, preview=False):
        """Generate newsletter html and other related values.

        When building a newsletter, we'll remove any STYLE tags intermingled with content in newsletter
        templates and assemble the CSS therein into a single STYLE tag placed in the HEAD. The content of this
        tag will be stored in ``html_style``, which will be added to ``html_head``, while the html content of
        the newsletter will be stored in ``html_body``. These will all then be assembled into ``html``.

        For a newsletter preview, this final ``html`` is all we should need to display a preview of the final
        newsletter. However, because no inlining of styles is done for previews, it will be unsuitable for
        a final send.

        When ``preview`` is False, we'll do the following:
        1. Extract qny media queries that we find in the STYLE tag and save them into ``html_style``
        2. Inline styles and store the result in ``html_body``
        3. Overwrite ``html`` with the new inlined BODY and STYLE

        Note that we keep ``html_head``, ``html_style`` and ``html_body`` separate here, because there may
        be some newsletter APIs that require that these things be passed over separately. For most, ``html``,
        which contains the full web HTML, should suffice.



        // Matches @media queries and their block content
        const regex = /@media[^{]+\{([\s\S]+?\})\s*\}/g;

        /@media[^{]+\{([\s\S]+?})\s*}/g


        Email clients (like Gmail, Outlook, and Apple Mail) only support standard, flat CSS. Email code never uses
        nested CSS rules (like Sass or modern CSS nesting), which makes Python's standard re module perfectly reliable
        for this task.

        import re

        # The Regex Pattern
        media_query_pattern = r'(@media[^{]+\{(?:[^{}]+|\{[^{}]*\})*\})'

        Why this specific regex works for emailsHandles single-level brackets:
        The (?:[^{}]+|\{[^{}]*\})* section safely matches everything inside the media query, including the standard internal CSS brackets (.class { property: value; }).
        Ignores regular CSS: It won't accidentally grab your standard, non-responsive email styles (like .button { color: blue; }).
        Captures the entire block: It returns the @media header, the condition, and all the responsive style rules wrapped inside it.

        :param preview: when False, we'll execute the ``inline_styles`` method as we generate the final html
            for this newsletter; when True, we'll skip inlining
        """

    def define_section_type(self, type, context):
        """Define a type of section for future reference.

        A type definition is simply a context dict of the same form as one might provide to the ``add_sections``
        method below. By attaching this dict to the specified ``type``, it becomes reusable making, it the base
        context dict for all sections of that type.

        For example, suppose we define a section as follows:

        ..  code-block:: python

            builder.define_section_type('numbers_to_ten', {
                'class': 'numbers',
                'numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            })

        We could then add two different numbers sections in a row via the following:

        ..  code-block:: python

            builder.add_section('numbers_to_ten')  # a section that receives only default context for this type
            builder.add_section({  # a section that merges it's context into the default context for this type
                'type': 'numbers_to_ten',
                'class': 'more-numbers',
                'quote': 'Count the numbers. Don\'t let them count you.'
            })

        The resulting context dict for the latter section will be:

        ..  code-block:: python

            {
                'type': 'numbers_to_ten',
                'class': 'more-numbers',
                'numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'quote': 'Count the numbers. Don\'t let them count you.'
            }

        There's one exception to this merging. Anything specified in the "items" key of the context dict is
        assumed to be a queryset, a list of instances, or a string referencing a member of the DATA dict which
        will result in one of these two things. If we want a section of type X to have one additional set of
        items to work with, we don't want to have to redeclare the items already defined for that type of
        section. So rather than overwriting "items", we'll save the items from the type definition, merge in
        the section items dict, merge the context dicts, and then reassign "items" to the one we saved.

        For example, if a dict of type X is:

        ..  code-block:: python

            {
                'name:': 'Companies',
                'items': {
                    'companies': Company.object.all()
                }
            }

        And we add a section of type X like the following:

        ..  code-block:: python

            {
                'name:': 'Companies With Posts',
                'items': {
                    'posts': Post.object.all()
                }
            }

        The final context dict will be:

        ..  code-block:: python

            {
                'name:': 'Companies With Posts',
                'items': {
                    'companies': Company.object.all()
                    'posts': Post.object.all()
                }
            }

        But why not just define these querysets in the main dict? We define these separately in "items" because
        querysets defined under this key have their primary keys automatically recorded in "used_items" dict
        and excluded




        NEW IDEA

        Instead of having a special "items" dict with unusual behavior pass in querysets as normal. Have builder methods
        that do excluding / marking instead

        exclude_used method, expects sliced queryset, adds exclude clause, any pks that have been marked as used
        previously for this querysets meta type will be excluded; i.e. .exclude(pk__in=USED_OF_THIS_META_TYPE)

        mark_used method, expects either queryset or iterable, for each item in iterable take the pk (if it has one)
        and add it to the list of used items for that meta type. Mark used also keeps a list of per section items
        used when the current section has a primary key; i.e. [(SECTION_ID, POST_INSTANCE), (SECTION_ID, POST_INSTANCE), ....];
        returns the queryset

        This approach gives maximum freedom of approach. One approach is to pass already sliced queryset when adding
        sections, in which case you would call these methods directly when preparing each section's context. Alternatively,
        since the builder object is passed in context, you can call the methods as they're used in templates; this is
        a little messier in one sense; but in another allows greater freedom for using type definitions











        ..  code-block:: python

            {
                'type': 'numbers_to_ten',
                'class': 'more-numbers',
                'numbers': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'quote': 'Count the numbers. Don\'t let them count you.'
            }



        Sections defined by this method can be referenced by the key "type" within the context provided to
        ``add_sections``. When the value of this key corresponds to a predefined section type, we'll derive the
        context of the section being added by using the type context as a base and merging in the context of
        the just added section, thus simplifying the creation of new sections of the given type.

        Note that section type definitions provided via this method will be available solely to the current
        newsletter builder instance. To declare

        :param type: a string key by which to identify this type of section
        :param context: the default context for all sections of this type
        """

    def exclude_used(self, queryset):
        """Exclude previously used items from this queryset's model.

        When items are passed to ``mark_as_used``, we'll add their primary keys to a per-model-name dict of
        lists, each of whose members contains keys previously marked as used for that model. We'll then use
        that dict in this method to exclude those items from the current queryset, thus avoiding duplicates
        from one section to the next, even when the same queryset is used.

        :param queryset: a queryset from which to exclude previously used items of the same model
        :return: the filtered queryset
        """
        used_pks = self.used_pks_by_class.get(queryset.model.__name__)
        return queryset.exclude(pk__in=used_pks) if used_pks else queryset

    def mark_as_used(self, items):
        """Mark all items with a ``pk`` attribute as used, each according to its model name.

        TODO also add to the current section

        :param items: a queryset, list, tuple, or other iterable containing instances we want to mark as used
        :return: the ``items`` passed
        """
        for item in items:
            if hasattr(item, 'pk'):  # assume this is a model instance
                self.used_pks_by_class.setdefault(item.__class__.__name__, []).append(item.pk)
        return items

    def inline_styles(self):
        """Inlines newsletter styles and returns the resulting HTML.

        Note that prior to calling this method, we'll extract and preserve any media queries (which cannot
        be inlined and which most inliners will strip out). After inlining is complete, we'll then inject
        these media queries back into the HEAD, so that they are available for any clients that recognize
        them.

        NOTE: by default, this method returns newsletter HTML as-is. Make sure to implement it with your
        preferred inliner when subclassing Newsletter.

        :return: the resulting inlined HTML
        """
        return self.html




class RestClient(object):
    """A bare-bones REST client on which service-specific REST clients can be built.

    Ever been tasked with interfacing with a service and not known where to begin? Ever encountered
    a service whose pre-built python client is either massively overcomplicated or which finds ways to make
    even the simplest of tasks complex? I have, and that is the reason this class exists.

    This class is intended as a base for constructing REST clients, so that you can get them up and running quickly.
    It will help alleviate the complexity often involved in managing tokens and setting authorization headers, so
    that you can quickly build and customize your own methods for a service rather than relying upon the gargantuan
    pre-built clients provided by certain companies. It is made to handle three different authentication scenarios:

    1. A static access token
    2. An access token that must be regularly refreshed via the client id and client secret
    3. An access token that requires a refresh token to refresh

    In all cases, once the access token has been acquired, requests may be built and called from an instance of the
    new client in the same fashion.

    Suppose we want to create a client whose access token never changes. We might do something like the following:

    ..  code-block:: python

        from djangoat.builders import RestClient

        class CoolServiceClient(RestClient):
            access_token = COOL_SERVICE_ACCESS_TOKEN
            url = 'https://api.coolservice.com/v3/'

            def get_my_contact(self, id):  # a service-specific method
                # Results in a GET request to "https://api.coolservice.com/v3/contact/{id}/"
                return self.get(f'contact/{id}/')

        cool_service_client = CoolServiceClient()
        print(cool_service_client.get_my_contact(54321))

    When ``access_token`` is set, we assume that it is a static token that will not expire. This token will be passed
    to the `get_headers`_ method to form the request headers that will be sent with the request. We will only attempt
    the request once and throw an error if it fails. Otherwise, we'll return the request results as JSON.
    If your service requires different headers from those yielded by `get_headers`_, simply override this method to
    produce the appropriate ones. You should now be ready to begin creating methods using the supplied `get`_ and
    `post`_ methods as shown above.

    When a service requires us to regularly retrieve new access tokens using a client id and client secret but does
    not use refresh tokens, we might do something like the following:

    ..  code-block:: python

        from djangoat.builders import RestClient

        class CoolerServiceClient(RestClient):
            auth_url = 'https://auth.coolerservice.com/tokens/'
            client_id = '12345'
            client_secret = 'blahblahblahblahblahblah'
            url = 'https://api.coolerservice.com/v3/'

            def get_my_contact(self, id):
                return self.get(f'/contact/{id}/')

        cooler_service_client = CoolerServiceClient()
        print(cooler_service_client.get_my_contact(54321))

    The call to the method above would result in the following series of events within the `request`_ method:

    1. Populate headers via `refresh_headers`_, if needed (or use previously populated headers)
        a. Call `get_auth_response`_, which retrieves a fresh access token from ``auth_url``
        b. Call `get_access_token`_ to extract the access token from the authorization response
        c. Call `get_headers`_ to generate fresh request headers from the access token
    2. Perform the request
    3. If the `request_unauthorized`_ method indicates that our access token has expired . . .
        a. Refresh headers as outlined above
        b. Attempt the request again
    4. If the `request_failed`_ method indicates that the request has failed, throw an error
    5. Return the response as json

    If your service uses basic authorization via the client id and client secret and standard naming conventions,
    the above should work out-of-the-box. Otherwise, simply override any non-conforming methods to bring them back
    into line.

    Lastly, if a service uses refresh tokens to refresh expired access tokens, we might do the following:

    ..  code-block:: python

        from djangoat.builders import RestClient

        class CoolestServiceClient(RestClient):
            auth_url = 'https://auth.coolestservice.com/tokens/'
            client_id = '12345'
            client_secret = 'blahblahblahblahblahblah'
            credentials_file = '/path/to/the/file.txt'  # OR set refresh_token
            refresh_token = '8675309eeeiiinne'  # OR set credentials_file
            url = 'https://api.coolestservice.com/v3/'

            def generate_initial_credentials(self):
                # Some services will require something like this to get initial credentials
                print(requests.post(self.auth_url, data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': input('Enter "code" from the Coolest Service to get credentials: '),
                    'grant_type': 'authorization_code',
                }).json())

            def get_my_contact(self, id):
                return self.get(f'/contact/{id}/')

        coolest_service_client = CoolestServiceClient()
        print(coolest_service_client.get_my_contact(54321))

    Some services provide a refresh token that never expires and that must be used to fetch new access tokens. In these
    cases, we may simply assign this token to ``refresh_token`` and leave ``credentials_file`` blank, and the same
    refresh token will be used to retrieve new access tokens in all authorization requests. In other cases, the
    refresh token itself will be updated, either periodically or with every new access token. In these cases, we'll
    want to store it in a ``credentials_file``, so that we can retrieve it for new authorization requests. Aside from
    this extra step, the flow of events for each request is basically the same as the previous example.

    Whatever your use case, this class it built so that you can override only that part that needs adjustment and
    begin actually interacting with a service's API as soon as possible. Thus, it is worth studying the flow that
    it uses to authenticate and get results for faster development in future projects.
    """
    access_token = None
    access_token_key = 'access_token'  # alter this if a service uses a non-standard key
    api_url = None  # the url for api requests
    auth_url = None  # the url for authorization requests
    client_id = None
    client_secret = None
    credentials_file = None  # an optional file where credentials should be stored (i.e. a refresh token)
    headers = None  # headers passed with each request and kept fresh via "refresh_headers"
    refresh_token = None  # a token for refreshing the access token in "get_auth_response"
    refresh_token_key = 'refresh_token'  # alter this if a service uses a non-standard key

    def __init__(self):
        self.name = self.__class__.__name__

    def __str__(self):
        return f'{self.name} API Wrapper (url: {self.api_url}, headers: {self.headers})'

    def delete(self, url, **kwargs):
        """Returns the results of a DELETE request.

        See ``requests.delete`` in the `requests api`_ for possible values for ``kwargs``.

        :param url: the endpoint of the request, excluding the ``api_url``
        :return: the results of the request
        """
        return self.request(requests.delete, url, **kwargs)

    def error(self, msg, response):
        """Generates a standard error with a set format.

        :param msg: a message to display
        :param response: the response received
        """
        raise Exception(f'{msg} {self.name} responded: {response.text}')

    def get(self, url, params=None, **kwargs):
        """Returns the results of a GET request.

        See ``requests.get`` in the `requests api`_ for possible values for ``kwargs``.

        :param url: the endpoint of the request, excluding the ``api_url``
        :param params: the like-named argument of ``requests.get``
        :return: the results of the request
        """
        return self.request(requests.get, url, params=params, **kwargs)

    def get_access_token(self, response):
        """Retrieves the access token returned in "get_auth_response".

        When request headers need refreshing due to an expired access token, we'll call `get_auth_response`_ from
        within `refresh_headers`_. `get_auth_response`_ should return a response object that at minimum contains an
        access token, which this method is responsible for returning for use in building new headers.

        If a ``credentials_file`` is specified, as will typically need to be the case when the response also contains a
        refresh token for use in acquiring new access tokens after the current one has expired, we'll want to save the
        response to this file and assign the refresh token to ``refresh_token``. We can then use this refresh token
        later in `get_auth_response`_ the next time we need to refresh.

        This method is coded for typical use cases, but will need to be overridden in some instances, based
        on the response returned by `get_auth_response`_.

        :param response: the response received from `get_auth_response`_
        :return: the access token
        """
        r = response.json()
        if self.credentials_file:  # update and save a rotating refresh token
            r[self.refresh_token_key] = self.refresh_token = r.get(self.refresh_token_key, self.refresh_token)
            with open(self.credentials_file, 'w') as f:
                f.write(json.dumps(r))
        return r[self.access_token_key]

    def get_auth_dict(self, refresh_token):
        """Returns a dict of data to pass in an authorization request.

        This is a convenience method that may be overridden to accommodate the varying data services require in
        authorization requests.

        :return: an auth dict
        """
        return {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            self.refresh_token_key: refresh_token
        }

    def get_auth_response(self):
        """Returns an authorization response from a service, prepped for `get_access_token`_.

        When our current access token has expired and we need to generate new headers, we'll need to get a new
        access token from our service. If the service uses refresh tokens, these will typically be stored in
        a ``credentials_file``, whose contents are returned by `get_stored_credentials`_. In this case, we'll pass the
        refresh token to the ``auth_url`` to get new credentials. `get_access_token`_ will be responsible for storing
        those credentials and returning the new access token.

        For services that do not use refresh tokens and thus do not require credential storage, such as one that
        provides a new access token solely on the basis of the client id and client secret, this method should
        simply return the response of the authorization request.

        As with `get_access_token`_, this method is coded for typical use cases, but may be overridden when services
        decide to get creative with their requirements.

        :return: an auth response with an authorization token to be used in future requests
        """
        if self.credentials_file:  # get the token via a rotating refresh token
            rt = self.refresh_token = self.refresh_token or self.get_stored_credentials().get(self.refresh_token_key, None)
            if rt:
                return requests.post(self.auth_url, data=self.get_auth_dict(rt))
            raise Exception(f'No refresh token was found at "{self.credentials_file}" with which to request a new access token.')
        elif self.refresh_token:  # get the token via a static refresh token
            return requests.post(self.auth_url, data=self.get_auth_dict(self.refresh_token))
        return requests.post(self.auth_url, headers={  # get the token via basic authorization
            'Authorization': 'Basic ' + self.get_basic_auth_token()
        })

    def get_basic_auth_token(self):
        """Returns a basic authorization token built from the client id and client secret.

        :return: a basic authorization token
        """
        return base64.b64encode(bytes(f'{self.client_id}:{self.client_secret}', 'utf8')).decode()

    def get_headers(self, token):
        """Returns request headers as a dict, using the provided token.

        :param token: the access token returned by "get_auth_response"
        :return: the headers for future requests
        """
        return {'Authorization': 'Bearer ' + token}

    def get_stored_credentials(self):
        """Returns previously stored credentials, typically containing a refresh token for use in access token retrieval.

        If you are storing credentials somewhere besides a file, override this method to accommodate your use case
        and return the required credentials dict.

        :return: a credentials dict
        """
        return get_json_file_contents(self.credentials_file)

    def head(self, url, **kwargs):
        """Returns the results of a HEAD request.

        See ``requests.head`` in the `requests api`_ for possible values for ``kwargs``.

        :param url: the endpoint of the request, excluding the ``api_url``
        :return: the results of the request
        """
        return self.request(requests.head, url, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """Returns the results of a PUT request.

        See ``requests.patch`` in the `requests api`_ for possible values for ``kwargs``.

        :param url: the endpoint of the request, excluding the ``api_url``
        :param data: the like-named argument of ``requests.patch``
        :return: the results of the request
        """
        return self.request(requests.put, url, data=data, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """Returns the results of a POST request.

        See ``requests.post`` in the `requests api`_ for possible values for ``kwargs``.

        :param url: the endpoint of the request, excluding the ``api_url``
        :param data: the like-named argument of requests.post
        :param json: the like-named argument of requests.post
        :return: the results of the request
        """
        return self.request(requests.post, url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        """Returns the results of a PUT request.

        See ``requests.put`` in the `requests api`_ for possible values for ``kwargs``.

        :param url: the endpoint of the request, excluding the ``api_url``
        :param data: the like-named argument of ``requests.put``
        :return: the results of the request
        """
        return self.request(requests.put, url, data=data, **kwargs)

    def refresh_headers(self):
        """Refreshes headers to include an up-to-date access token.

        We begin by calling `get_auth_response`_, which should contact our service with whatever credentials are
        necessary to retrieve a new access token (i.e. a refresh token or just a basic auth token). If the request
        succeeds, we'll pass it to `get_access_token`_, whose responsibility it will be to return the access token
        we've received and store credentials as necessary for future requests. Finally, we'll pass the returned
        access token to `get_headers`_ to build the new headers, so that we can reattempt the request with our
        new credentials.
        """
        r = self.get_auth_response()
        if r.status_code != 200:
            self.error(f'Authorization response failed ({r.status_code}).', r)
        t = self.get_access_token(r)
        if not t:
            self.error(f'Failed to retrieve access token ({r.status_code}).', r)
        self.headers = self.get_headers(t)
        return self.headers

    def request(self, method, url, **kwargs):
        """Performs a request using ``method``.

        If have no headers yet, we'll begin by refreshing our headers with a new access token and then attempt our
        request, which we'd expect to succeed. If we do have headers, but they're stale, the request will fail, in
        which case we'll refresh headers to include a newly generated new access token. Then we'll reattempt our
        request. Finally, we'll test for failure by calling the `request_failed`_ method. Assuming the request passes
        we'll return request results in json format.

        :param method: the requests library method to call for the request
        :param url: the endpoint of the request
        :return: the json results of the request
        """
        url = self.api_url + url
        if not getattr(self, 'headers', None):
            if self.access_token:  # static access token
                self.headers = self.get_headers(self.access_token)
            else:  # regularly expiring access token
                self.refresh_headers()
        kwargs['headers'] = self.headers
        r = method(url, **kwargs)
        if not self.access_token and self.request_unauthorized(r):
            kwargs['headers'] = self.refresh_headers()
            r = method(url, **kwargs)
        if self.request_failed(r):
            self.error(f'Request failed ({r.status_code}).', r)
        return r.json()

    def request_failed(self, response):
        """Returns True if the request has failed.

        Called after a maximum of two request attempts, this method returns True if we've failed to get a success
        response from our service.

        :param response: the request response
        :return: True if the request failed, False otherwise
        """
        return response.status_code not in (200, 201)

    def request_unauthorized(self, response):
        """Returns True if a request, made using current headers, comes back as unauthorized.

        When headers are set, we will attempt a request. If the response comes back as unauthorized, we'll want to
        refresh headers using a new access token and try again. This method determines whether or not we'll make a
        second attempt.

        :param response: the request response
        :return: True if the request was unauthorized, False otherwise
        """
        return response.status_code == 401
