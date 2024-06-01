import datetime
import json
from collections import OrderedDict

from django.apps.registry import apps
from django.contrib import admin, messages
from django.contrib.admin import AdminSite
from django.contrib.admin.options import IncorrectLookupParameters
from django.template import Context
from django.urls import NoReverseMatch, resolve, reverse
from django.utils import translation
from django.utils.encoding import force_str, smart_str
from django.utils.functional import Promise
from django.utils.text import capfirst, slugify
from django.utils.translation import gettext_lazy as _

from jet import settings
from jet.models import PinnedApplication


def get_app_list(context, order=True):
    admin_site = get_admin_site(context)
    request = context["request"]

    app_dict = {}
    for model, model_admin in admin_site._registry.items():
        app_label = model._meta.app_label
        has_module_perms = model_admin.has_module_permission(request)

        if has_module_perms:
            perms = model_admin.get_model_perms(request)

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True in perms.values():
                info = (app_label, model._meta.model_name)
                model_dict = {
                    "name": capfirst(model._meta.verbose_name_plural),
                    "object_name": model._meta.object_name,
                    "perms": perms,
                    "model_name": model._meta.model_name,
                }
                if perms.get("change", False):
                    try:
                        model_dict["admin_url"] = reverse("admin:%s_%s_changelist" % info, current_app=admin_site.name)
                    except NoReverseMatch:
                        pass
                if perms.get("add", False):
                    try:
                        model_dict["add_url"] = reverse("admin:%s_%s_add" % info, current_app=admin_site.name)
                    except NoReverseMatch:
                        pass
                if app_label in app_dict:
                    app_dict[app_label]["models"].append(model_dict)
                else:
                    try:
                        name = apps.get_app_config(app_label).verbose_name
                    except NameError:
                        name = app_label.title()

                    app_dict[app_label] = {
                        "name": name,
                        "app_label": app_label,
                        "app_url": reverse(
                            "admin:app_list",
                            kwargs={"app_label": app_label},
                            current_app=admin_site.name,
                        ),
                        "has_module_perms": has_module_perms,
                        "models": [model_dict],
                    }

    # Sort the apps alphabetically.
    app_list = list(app_dict.values())

    if order:
        app_list.sort(key=lambda x: x["name"].lower())

        # Sort the models alphabetically within each app.
        for app in app_list:
            app["models"].sort(key=lambda x: x["name"])

    return app_list


def get_admin_site(context):
    try:
        current_resolver = resolve(context.get("request").path)
        index_resolver = resolve(reverse("%s:index" % current_resolver.namespaces[0]))

        if hasattr(index_resolver.func, "admin_site"):
            return index_resolver.func.admin_site

        for func_closure in index_resolver.func.__closure__:
            if isinstance(func_closure.cell_contents, AdminSite):
                return func_closure.cell_contents
    except Exception:
        pass

    return admin.site


def get_admin_site_name(context):
    return get_admin_site(context).name


class LazyDateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, Promise):
            return force_str(obj)
        return self.encode(obj)


def get_model_instance_label(instance):
    if getattr(instance, "related_label", None):
        return instance.related_label()
    return smart_str(instance)


class SuccessMessageMixin:
    """
    Adds a success message on successful form submission.
    """

    success_message = ""

    def form_valid(self, form):
        response = super(SuccessMessageMixin, self).form_valid(form)
        success_message = self.get_success_message(form.cleaned_data)
        if success_message:
            messages.success(self.request, success_message)
        return response

    def get_success_message(self, cleaned_data):
        return self.success_message % cleaned_data


def get_model_queryset(admin_site, model, request, preserved_filters=None):
    model_admin = admin_site._registry.get(model)

    if model_admin is None:
        return

    try:
        changelist_url = reverse(
            "%s:%s_%s_changelist" % (admin_site.name, model._meta.app_label, model._meta.model_name)
        )
    except NoReverseMatch:
        return

    changelist_filters = None

    if preserved_filters:
        changelist_filters = preserved_filters.get("_changelist_filters")

    if changelist_filters:
        changelist_url += "?" + changelist_filters

    if model_admin:
        queryset = model_admin.get_queryset(request)
    else:
        queryset = model.objects

    list_display = model_admin.get_list_display(request)
    list_display_links = model_admin.get_list_display_links(request, list_display)
    list_filter = model_admin.get_list_filter(request)
    search_fields = (
        model_admin.get_search_fields(request)
        if hasattr(model_admin, "get_search_fields")
        else model_admin.search_fields
    )
    list_select_related = (
        model_admin.get_list_select_related(request)
        if hasattr(model_admin, "get_list_select_related")
        else model_admin.list_select_related
    )

    actions = model_admin.get_actions(request)
    if actions:
        list_display = ["action_checkbox"] + list(list_display)

    ChangeList = model_admin.get_changelist(request)

    change_list_args = [
        request,
        model,
        list_display,
        list_display_links,
        list_filter,
        model_admin.date_hierarchy,
        search_fields,
        list_select_related,
        model_admin.list_per_page,
        model_admin.list_max_show_all,
        model_admin.list_editable,
        model_admin,
        model_admin.search_help_text,
    ]

    sortable_by = model_admin.get_sortable_by(request)
    change_list_args.append(sortable_by)

    try:
        cl = ChangeList(*change_list_args)
        queryset = cl.get_queryset(request)
    except IncorrectLookupParameters:
        pass

    return queryset


def get_possible_language_codes():
    language_code = translation.get_language()

    language_code = language_code.replace("_", "-").lower()
    language_codes = []

    # making dialect part uppercase
    split = language_code.split("-", 2)
    if len(split) == 2:
        language_code = "%s-%s" % (split[0].lower(), split[1].upper()) if split[0] != split[1] else split[0]

    language_codes.append(language_code)

    # adding language code without dialect part
    if len(split) == 2:
        language_codes.append(split[0].lower())

    return language_codes


def get_original_menu_items(context):
    if context.get("user") and user_is_authenticated(context["user"]):
        pinned_apps = PinnedApplication.objects.filter(user=context["user"].pk).values_list("app_label", flat=True)
    else:
        pinned_apps = []

    original_app_list = get_app_list(context)

    return (
        {
            "app_label": app["app_label"],
            "url": app["app_url"],
            "url_blank": False,
            "label": app.get("name", capfirst(_(app["app_label"]))),
            "has_perms": app.get("has_module_perms", False),
            "models": [
                {
                    "url": model.get("admin_url"),
                    "url_blank": False,
                    "name": model["model_name"],
                    "object_name": model["object_name"],
                    "label": model.get("name", model["object_name"]),
                    "has_perms": any(model.get("perms", {}).values()),
                }
                for model in app["models"]
            ],
            "pinned": app["app_label"] in pinned_apps,
            "custom": False,
        }
        for app in original_app_list
    )


def get_menu_item_url(url, original_app_list):
    if isinstance(url, dict):
        url_type = url.get("type")

        if url_type == "app":
            return original_app_list[url["app_label"]]["url"]
        elif url_type == "model":
            models = {x["name"]: x["url"] for x in original_app_list[url["app_label"]]["models"]}
            return models[url["model"]]
        elif url_type == "reverse":
            return reverse(url["name"], args=url.get("args"), kwargs=url.get("kwargs"))
    elif isinstance(url, str):
        return url


def get_menu_items(context):
    pinned_apps = PinnedApplication.objects.filter(user=context["user"].pk).values_list("app_label", flat=True)
    original_app_list = OrderedDict(((app["app_label"], app) for app in get_original_menu_items(context)))
    custom_app_list = settings.JET_SIDE_MENU_ITEMS
    custom_app_list_deprecated = settings.JET_SIDE_MENU_CUSTOM_APPS

    if custom_app_list not in (None, False):
        if isinstance(custom_app_list, dict):
            admin_site = get_admin_site(context)
            custom_app_list = custom_app_list.get(admin_site.name, [])

        app_list = []

        def get_menu_item_app_model(app_label, data):
            item = {"has_perms": True}

            if "name" in data:
                parts = data["name"].split(".", 2)

                if len(parts) > 1:
                    app_label, name = parts
                else:
                    name = data["name"]

                if app_label in original_app_list:
                    models = {x["name"]: x for x in original_app_list[app_label]["models"]}

                    if name in models:
                        item = models[name].copy()

            if "label" in data:
                item["label"] = data["label"]

            if "url" in data:
                item["url"] = get_menu_item_url(data["url"], original_app_list)

            if "url_blank" in data:
                item["url_blank"] = data["url_blank"]

            if "permissions" in data:
                item["has_perms"] = item.get("has_perms", True) and context["user"].has_perms(data["permissions"])

            return item

        def get_menu_item_app(data):
            app_label = data.get("app_label")

            if not app_label:
                if "label" not in data:
                    raise Exception("Custom menu items should at least have 'label' or 'app_label' key")
                app_label = "custom_%s" % slugify(data["label"], allow_unicode=True)

            if app_label in original_app_list:
                item = original_app_list[app_label].copy()
            else:
                item = {"app_label": app_label, "has_perms": True}

            if "label" in data:
                item["label"] = data["label"]

            if "items" in data:
                item["items"] = [get_menu_item_app_model(app_label, x) for x in data["items"]]

            if "url" in data:
                item["url"] = get_menu_item_url(data["url"], original_app_list)

            if "url_blank" in data:
                item["url_blank"] = data["url_blank"]

            if "permissions" in data:
                item["has_perms"] = item.get("has_perms", True) and context["user"].has_perms(data["permissions"])

            item["pinned"] = item["app_label"] in pinned_apps

            return item

        for data in custom_app_list:
            item = get_menu_item_app(data)
            app_list.append(item)
    elif custom_app_list_deprecated not in (None, False):
        app_dict = {}
        models_dict = {}

        for app in original_app_list.values():
            app_label = app["app_label"]
            app_dict[app_label] = app

            for model in app["models"]:
                if app_label not in models_dict:
                    models_dict[app_label] = {}

                models_dict[app_label][model["object_name"]] = model

            app["items"] = []

        app_list = []

        if isinstance(custom_app_list_deprecated, dict):
            admin_site = get_admin_site(context)
            custom_app_list_deprecated = custom_app_list_deprecated.get(admin_site.name, [])

        for item in custom_app_list_deprecated:
            app_label, models = item

            if app_label in app_dict:
                app = app_dict[app_label]

                for model_label in models:
                    if model_label == "__all__":
                        app["items"] = models_dict[app_label].values()
                        break
                    elif model_label in models_dict[app_label]:
                        model = models_dict[app_label][model_label]
                        app["items"].append(model)

                app_list.append(app)
    else:

        def map_item(item):
            item["items"] = item["models"]
            return item

        app_list = list(map(map_item, original_app_list.values()))

    current_found = False

    for app in app_list:
        if not current_found:
            for model in app["items"]:
                if not current_found and model.get("url") and context["request"].path.startswith(model["url"]):
                    model["current"] = True
                    current_found = True
                else:
                    model["current"] = False

            if not current_found and app.get("url") and context["request"].path.startswith(app["url"]):
                app["current"] = True
                current_found = True
            else:
                app["current"] = False

    return app_list


def context_to_dict(context):
    if isinstance(context, Context):
        flat = {}
        for d in context.dicts:
            flat.update(d)
        context = flat

    return context


def user_is_authenticated(user):
    if not hasattr(user.is_authenticated, "__call__"):
        return user.is_authenticated
    else:
        return user.is_authenticated()
