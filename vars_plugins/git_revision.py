#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.plugins.vars import BaseVarsPlugin
from git import Repo

class VarsModule(BaseVarsPlugin):
    def get_vars(self, loader, path, entities):
        try:
            repository = Repo(path, search_parent_directories = True)
        except Exception:
            # RA code directory is not versioned
            return dict(
                ra_is_git = False
            )

        return dict(
            ra_git_commit = repository.head.reference.commit,
            ra_git_is_dirty = repository.is_dirty(untracked_files = True),
            ra_is_git = True
        )
