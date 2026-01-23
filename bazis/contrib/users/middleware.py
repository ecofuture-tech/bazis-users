from .models_abstract import UserMixin


class UserRequestMiddleware:
    """
    Middleware that attaches the current authenticated user to the context for the
    duration of the request.
    """

    def __init__(self, get_response):
        """
        Initializes the middleware with the given response handler.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Processes the incoming request, setting the user in the context if the user is
        authenticated, and then passes the request to the next middleware or view.
        """
        if request.user and getattr(request.user, 'is_anonymous', None) is False:
            UserMixin.CTX_USER_REQUEST.set(request.user)
        return self.get_response(request)
