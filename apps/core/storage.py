import os

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage


class VersionedStaticFilesStorage(StaticFilesStorage):
    """
    Development only: adds the file's modification time to static URLs
    (site.css?v=1730000000), so the browser loads the new CSS and JavaScript
    as soon as they change instead of reusing an old cached copy.

    Production uses ManifestStaticFilesStorage, which puts a content hash in
    the file name instead (see STORAGES in settings).
    """

    def url(self, name):
        url = super().url(name)
        path = finders.find(name)
        if not path:
            return url
        if isinstance(path, (list, tuple)):
            path = path[0]
        return f"{url}?v={int(os.path.getmtime(path))}"
