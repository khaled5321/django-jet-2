import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = "!DJANGO_JET_TESTS!"

DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_PROPAGATE_EXCEPTIONS = True

ROOT_URLCONF = "jet.tests.urls"

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = (
    "jet.dashboard",
    "jet",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "jet.tests",
)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
)


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": (
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            )
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-US"
USE_I18N = True
USE_L10N = True
USE_TZ = True
SITE_ID = 1
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

MEDIA_ROOT = ""
MEDIA_URL = ""

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

JET_INDEX_DASHBOARD = "jet.tests.dashboard.TestIndexDashboard"
JET_APP_INDEX_DASHBOARD = "jet.tests.dashboard.TestAppIndexDashboard"

JET_THEMES = [
    {
        "theme": "default",  # theme folder name
        "color": "#47bac1",  # color of the theme's button in user menu
        "title": "Default",  # theme title
    },
    {"theme": "green", "color": "#44b78b", "title": "Green"},
    {"theme": "light-green", "color": "#2faa60", "title": "Light Green"},
    {"theme": "light-violet", "color": "#a464c4", "title": "Light Violet"},
    {"theme": "light-blue", "color": "#5EADDE", "title": "Light Blue"},
    {"theme": "light-gray", "color": "#222", "title": "Light Gray"},
]
