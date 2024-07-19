def add_user_to_context(request):
    return {'user': request.user}