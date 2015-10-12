# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from ..base import BaseAPIView
from auto_updater import AutoUpdater, get_git_root


class UpdateView(BaseAPIView):
    def get(self):
        # TODO check auth

        updater = AutoUpdater(
            settings.GIT_BRANCH,
            get_git_root(__file__),
        )
        updater.run()

        # We should never come here because of the restart
        return self.render_json({'status': 'error'})
