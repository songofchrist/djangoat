import base64
import json
import requests

from djangoat.utils import get_json_file_contents




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
