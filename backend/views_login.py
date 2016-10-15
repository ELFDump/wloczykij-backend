from allaccess.views import OAuthRedirect, OAuthCallback


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
    pass
