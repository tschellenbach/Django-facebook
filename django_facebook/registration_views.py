from django.shortcuts import render
from django_facebook.utils import get_registration_backend
from django_facebook.connect import CONNECT_ACTIONS


def register(request):
    """
    A very simplistic register view
    """
    backend = get_registration_backend()
    form_class = backend.get_form_class(request)
    template_name = backend.get_registration_template()

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = backend.register(request,
                                        form=form, **form.cleaned_data)
            # keep the post behaviour exactly the same as django facebook's
            # connect flow
            response = backend.post_connect(
                request, new_user, CONNECT_ACTIONS.REGISTER)
            return response
    else:
        form = form_class()

    context = {'form': form}
    response = render(request, template_name, context)

    return response
