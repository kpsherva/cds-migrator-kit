# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# CDS-RDM is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""CDS-RDM transform step module."""

import datetime
import logging

from invenio_rdm_migrator.streams.records.transform import (
    RDMRecordEntry,
    RDMRecordTransform,
)

from cds_migrator_kit.rdm.migration.transform.xml_processing.dumper import CDSRecordDump
from cds_migrator_kit.rdm.migration.transform.xml_processing.errors import \
    LossyConversion
from cds_migrator_kit.records.log import RDMJsonLogger

cli_logger = logging.getLogger("migrator")
logger = RDMJsonLogger()


class CDSToRDMRecordEntry(RDMRecordEntry):
    """Transform Zenodo record to RDM record."""

    def _created(self, json_entry):
        try:
            return json_entry["_created"]
        except KeyError:
            return datetime.date.today().isoformat()

    def _updated(self, record_dump):
        """Returns the creation date of the record."""
        return record_dump.data["record"][0]["modification_datetime"]

    def _version_id(self, entry):
        """Returns the version id of the record."""
        return 1

    def _access(self, entry, record_dump):
        is_file_public = True

        for key, value in record_dump.files.items():
            if value[0]["hidden"]:
                is_file_public = False
        return {
            "record": "public",
            "files": "public" if is_file_public else "restricted",
        }

    def _index(self, record_dump):
        """Returns the version index of the record."""
        return 1  # in legacy we start at 0

    def _recid(self, record_dump):
        """Returns the recid of the record."""
        return str(record_dump.data["recid"])

    def _pids(self, json_entry):
        return {}

    def _bucket_id(self, json_entry):
        return

    def _custom_fields(self, json_entry):
        return {}

    def _id(self, entry):
        return

    def _media_bucket_id(self, entry):
        return

    def _media_files(self, entry):
        return {}

    def _pids(self, json_entry):
        return {}

    def _files(self, record_dump):
        """Transform the files of a record."""
        files = record_dump.prepare_files()
        return {"enabled": True if files else False}

    def _communities(self, json_entry):
        return json_entry["communities"]

    def _metadata(self, json_entry):
        def creators(json):
            try:
                return json["creators"]
            except KeyError:
                return [
                    {
                        "person_or_org": {
                            "identifiers": [
                                {"identifier": "0000-0002-1825-0097",
                                 "scheme": "orcid"}
                            ],
                            "given_name": "unknown",
                            "name": "unknown",
                            "family_name": "unknown",
                            "type": "personal",
                        }
                    }
                ]

        def _resource_type(data):
            t = "publication-technicalnote"
            st = None
            return {"id": f"{t}-{st}"} if st else {"id": t}
        return {
            "creators": creators(json_entry),
            "title": json_entry["title"],
            "resource_type": _resource_type(json_entry),
            "description": json_entry.get("description", ""),
            "publication_date": "2024-07-11",
        }

    def transform(self, entry):
        """Transform a record single entry."""
        record_dump = CDSRecordDump(
            entry,
        )
        try:
            logger.add_recid_to_stats(entry['recid'])
            record_dump.prepare_revisions()
            timestamp, json_data = record_dump.revisions[-1]
            logger.add_record(json_data)
            return {
                "created": self._created(json_data),
                "updated": self._updated(record_dump),
                "version_id": self._version_id(record_dump),
                "index": self._index(record_dump),
                # "communities": self._communities(json_data),
                "json": {
                    "id": self._recid(record_dump),
                    "pids": self._pids(json_data),
                    "files": self._files(record_dump),
                    "metadata": self._metadata(json_data),
                    "access": self._access(json_data, record_dump),
                },
            }
        except LossyConversion as e:
            cli_logger.error('[DATA ERROR]: {0}'.format(e.message))
            logger.add_log(e, output=entry)
        except Exception as e:
            logger.add_log(e, output=entry)
            raise e
        # TODO take only the last


class CDSToRDMRecordTransform(RDMRecordTransform):
    """CDSToRDMRecordTransform."""

    def _community_id(self, entry, record):
        communities = record.get("communities")
        if communities:
            # TODO: handle all slugs
            slug = communities[0]
            if slug:
                return {"ids": [slug], "default": slug}
        return {}

    def _parent(self, entry, record):
        parent = {
            "created": record["created"],  # same as the record
            "updated": record["updated"],  # same as the record
            "version_id": record["version_id"],
            "json": {
                # loader is responsible for creating/updating if the PID exists.
                "id": f'{record["json"]["id"]}-parent',
                "access": {
                    # "owned_by": [{"user": o} for o in entry["json"].get("owners", [])]
                },
                # "communities": self._community_id(entry, record),
            },
        }

        return parent

    def _transform(self, entry):
        """Transform a single entry."""
        # the functions receive the full record/data entry
        # while in most cases the full view is not needed
        # since this is a low level tool used only by users
        # with deep system knowledge providing the flexibility
        # is future proofing and simplifying the interface
        record = self._record(entry)
        return {
            "record": record,
            "draft": self._draft(entry),
            "parent": self._parent(entry, record),
            "record_files": self._record_files(entry, record),
            "draft_files": self._draft_files(entry),
        }

    def _record(self, entry):
        return CDSToRDMRecordEntry().transform(entry)

    def _draft(self, entry):
        return None

    def _draft_files(self, entry):
        return None

    def _record_files(self, entry, record):
        # files = entry["json"].get("_files", [])
        # return [
        #     {
        #         "key": f["key"],
        #         "object_version": {
        #             "file": {
        #                 "size": f["size"],
        #                 "checksum": f["checksum"],
        #             },
        #         },
        #     }
        #     for f in files
        # ]
        return []