from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"

    def ready(self):
        from django.contrib.auth.signals import user_login_failed

        from . import ratelimit

        user_login_failed.connect(
            ratelimit.record_login_failure,
            dispatch_uid="core_record_login_failure",
        )
