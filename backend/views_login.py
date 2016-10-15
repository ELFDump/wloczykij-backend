import base64
import hashlib
import logging

from allaccess.views import OAuthRedirect, OAuthCallback
from django.contrib.auth.models import User
from django.utils.encoding import smart_bytes, force_text


# Google:
# auth url: https://accounts.google.com/o/oauth2/auth
# token url: https://accounts.google.com/o/oauth2/token
# profile url: https://www.googleapis.com/oauth2/v1/userinfo

# Facebook:
# auth url: https://www.facebook.com/dialog/oauth
# token url: https://graph.facebook.com/oauth/access_token
# profile url: https://graph.facebook.com/me?fields=email,first_name,last_name

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

# Google:
# {u'family_name': u'Ha\u0142adyn', u'name': u'Krzysztof Ha\u0142adyn', u'picture': u'https://lh3.googleusercontent.com/-vBG8xvLPkPQ/AAAAAAAAAAI/AAAAAAAAAEE/osblFFzGaxM/photo.jpg', u'locale': u'pl', u'gender': u'male', u'email': u'krzysztofhaladyn@gmail.com', u'link': u'https://plus.google.com/116882462515300726917', u'given_name': u'Krzysztof', u'id': u'116882462515300726917', u'verified_email': True}
# Facebook:
# {u'id': u'1138192516246618', u'first_name': u'Krzysztof', u'last_name': u'Ha\u0142adyn', u'name': u'Krzysztof Ha\u0142adyn', u'email': u'krzys_h@interia.pl'}
