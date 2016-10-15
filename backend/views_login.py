import base64
import hashlib
import json
import logging

from allaccess.models import Provider, AccountAccess
from allaccess.views import OAuthRedirect, OAuthCallback
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http.response import Http404
from django.utils.encoding import smart_bytes, force_text


# Google:
# auth url: https://accounts.google.com/o/oauth2/auth
# token url: https://accounts.google.com/o/oauth2/token
# profile url: https://www.googleapis.com/oauth2/v1/userinfo

# Facebook:
# auth url: https://www.facebook.com/dialog/oauth
# token url: https://graph.facebook.com/oauth/access_token
# profile url: https://graph.facebook.com/me?fields=email,first_name,last_name
from requests import RequestException
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

logger = logging.getLogger(__name__)


class LoginRedirect(OAuthRedirect):
    def get_additional_parameters(self, provider):
        if provider.name == 'facebook':
            # Request permission to see user's email
            return {'scope': 'email'}
        if provider.name == 'google':
            # Request permission to see user's profile and email
            perms = ['userinfo.email', 'userinfo.profile']
            scope = ' '.join(['https://www.googleapis.com/auth/' + p for p in perms])
            return {'scope': scope}
        return super(LoginRedirect, self).get_additional_parameters(provider)


class LoginCallback(OAuthCallback):
    def get_or_create_user(self, provider, access, info):
        logger.info(info)

        username = ''
        if 'email' in info:
            username = info['email']

        digest = hashlib.sha1(smart_bytes(access)).digest()
        digest = force_text(base64.urlsafe_b64encode(digest)).replace('=', '')
        username = username + '-' + digest[-7:]

        kwargs = {
            User.USERNAME_FIELD: username,
            'email': '',
            'password': None
        }

        if 'email' in info:
            kwargs['email'] = info['email']

        # Facebook
        if 'first_name' in info:
            kwargs['first_name'] = info['first_name']
        if 'last_name' in info:
            kwargs['last_name'] = info['last_name']

        # Google
        if 'given_name' in info:
            kwargs['first_name'] = info['given_name']
        if 'family_name' in info:
            kwargs['last_name'] = info['family_name']

        return User.objects.create_user(**kwargs)


class LoginToken(LoginCallback, ViewSet):
    """
    This endpoint is used to get token used to authenticate requests made by the app and serves as an entry point
    for google/facebook login.

    ---

    When using google login, use the **/token/google/?token=&lt;your ID token&gt;** endpoint.

    When using facebook login, use the **/token/facebook/?token=&lt;your auth token&gt;** endpoint.

    If you are already logged in via other means (e.g. browser session in interactive docs), you can just
    use **/token/** with no parameters to get your access token.

    ---

    The returned token value should be included in every following request in the Authorization header, like so:

        Authorization: Token <token value here>
    """

    def list(self, request):
        return self.handle_token_response(request.user)

    def retrieve(self, request, pk=None):
        try:
            provider = Provider.objects.get(name=pk)
        except Provider.DoesNotExist:
            raise Http404('Unknown OAuth provider.')
        else:
            if not provider.enabled():
                raise Http404('Provider %s is not enabled.' % provider.name)

            raw_token = None
            identifier = None
            info = None
            client = self.get_client(provider)
            if provider.name == 'facebook':
                # Fetch access token
                if not 'token' in request.GET:
                    return self.handle_login_failure(provider, "Could not retrieve token.")
                raw_token = request.GET['token']
                # Fetch profile info
                info = client.get_profile_info(raw_token)
                if info is None:
                    return self.handle_login_failure(provider, "Could not retrieve profile.")
                identifier = self.get_user_id(provider, info)
                if identifier is None:
                    return self.handle_login_failure(provider, "Could not determine id.")
            elif provider.name == 'google':
                if not 'token' in request.GET:
                    return self.handle_login_failure(provider, "Could not retrieve token.")
                id_token = request.GET['token']
                try:
                    response = client.request('get', 'https://www.googleapis.com/oauth2/v3/tokeninfo', params={'id_token': id_token})
                    response.raise_for_status()
                except RequestException as e:
                    logger.error('Unable to validate access token: {0}'.format(e))
                    return self.handle_login_failure(provider, "Could not validate token.")
                else:
                    info = json.loads(response.text)
                if info['aud'] != provider.consumer_key:
                    return self.handle_login_failure(provider, "This token is not meant for this app. %s != %s" % (info['aud'], provider.consumer_key))
                identifier = info['id'] = info['sub']
                del info['sub']
            else:
                self.handle_login_failure(provider, "Unsupported provider type %s" % provider.name)

            # Get or create access record
            defaults = {
                'access_token': raw_token,
            }
            access, created = AccountAccess.objects.get_or_create(
                provider=provider, identifier=identifier, defaults=defaults
            )
            if not created:
                access.access_token = raw_token
                AccountAccess.objects.filter(pk=access.pk).update(**defaults)
            user = authenticate(provider=provider, identifier=identifier)
            if user is None:
                return self.handle_new_user(provider, access, info)
            else:
                return self.handle_existing_user(provider, user, access, info)

    def handle_existing_user(self, provider, user, access, info):
        super(LoginToken, self).handle_existing_user(provider, user, access, info)
        return self.handle_token_response(access.user)

    def handle_new_user(self, provider, access, info):
        super(LoginToken, self).handle_new_user(provider, access, info)
        return self.handle_token_response(access.user)

    def handle_login_failure(self, provider, reason):
        raise AuthenticationFailed(detail=reason)

    def handle_token_response(self, user):
        if not user.is_authenticated():
            raise NotAuthenticated()
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})

# Google:
# {u'family_name': u'Ha\u0142adyn', u'name': u'Krzysztof Ha\u0142adyn', u'picture': u'https://lh3.googleusercontent.com/-vBG8xvLPkPQ/AAAAAAAAAAI/AAAAAAAAAEE/osblFFzGaxM/photo.jpg', u'locale': u'pl', u'gender': u'male', u'email': u'krzysztofhaladyn@gmail.com', u'link': u'https://plus.google.com/116882462515300726917', u'given_name': u'Krzysztof', u'id': u'116882462515300726917', u'verified_email': True}
# Facebook:
# {u'id': u'1138192516246618', u'first_name': u'Krzysztof', u'last_name': u'Ha\u0142adyn', u'name': u'Krzysztof Ha\u0142adyn', u'email': u'krzys_h@interia.pl'}
