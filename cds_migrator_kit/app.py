# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# cds-migrator-kit is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CDS Migrator Development instance entrypoint."""

from flask import Flask
from flask_babel import Babel

from cds_migrator_kit import CdsMigratorKit
from cds_migrator_kit.reports.views import blueprint

# Create Flask application
app = Flask(__name__)
Babel(app)
CdsMigratorKit(app)
app.register_blueprint(blueprint)
