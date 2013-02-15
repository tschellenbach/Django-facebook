from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django_facebook.utils import get_registration_backend
from django.shortcuts import redirect


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
            new_user = backend.register(request, **form.cleaned_data)
            response = backend.post_registration_redirect(request, new_user)
            #keep the post behaviour exactly the same as django facebook

            return response
    else:
        form = form_class()

    context = RequestContext(request)
    context['form'] = form
    response = render_to_response(template_name, context_instance=context)

    return response
