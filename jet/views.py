from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST

from jet.forms import (
    AddBookmarkForm,
    ModelLookupForm,
    RemoveBookmarkForm,
    ToggleApplicationPinForm,
)
from jet.models import Bookmark


@require_POST
def add_bookmark_view(request):
    result = {"error": False}
    form = AddBookmarkForm(request, request.POST)

    if form.is_valid():
        bookmark = form.save()
        result.update({"id": bookmark.pk, "title": bookmark.title, "url": bookmark.url})
    else:
        result["error"] = True

    return JsonResponse(result)


@require_POST
def remove_bookmark_view(request):
    result = {"error": False}

    try:
        instance = Bookmark.objects.get(pk=request.POST.get("id"))
        form = RemoveBookmarkForm(request, request.POST, instance=instance)

        if form.is_valid():
            form.save()
        else:
            result["error"] = True
    except Bookmark.DoesNotExist:
        result["error"] = True

    return JsonResponse(result)


@require_POST
def toggle_application_pin_view(request):
    result = {"error": False}
    form = ToggleApplicationPinForm(request, request.POST)

    if form.is_valid():
        pinned = form.save()
        result["pinned"] = pinned
    else:
        result["error"] = True

    return JsonResponse(result)


@require_GET
def model_lookup_view(request):
    result = {"error": False}

    form = ModelLookupForm(request, request.GET)

    if form.is_valid():
        items, total = form.lookup()
        result["items"] = items
        result["total"] = total
    else:
        result["error"] = True

    return JsonResponse(result)


@require_GET
def custom_logout(request):
    """
    The reason for the custom logout view is that the default django logout view
    requires a POST request. So instead of making HTML changes, it is easier to
    make custom logout view.
    """
    # log the user out
    logout(request)

    # show logout success message
    messages.add_message(request, messages.SUCCESS, 'Logged out successfully.')

    # redirect to the login page
    return redirect('admin:login')
