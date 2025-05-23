# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# CDS-RDM is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

"""CDS-RDM contributors migration module."""

import re

from dojson.utils import force_list

from cds_migrator_kit.errors import UnexpectedValue
from cds_migrator_kit.transform.xml_processing.quality.parsers import StringValue
from cds_migrator_kit.transform.xml_processing.quality.regex import ALPHANUMERIC_ONLY

# RDM:
# "contributors": {
#   "description": "Contributors in order of importance.",
#   "type": "array",
#   "items": {
#     "type": "object",
#     "additionalProperties": false,
#     "properties": {
#       "person_or_org": {
#          "type": "object",
#           "additionalProperties": false,
#           "properties": {
#           "name": {
#           "type": "string"
#         },
#          "type": {
#               "description": "Type of name.",
#               "type": "string",
#               "enum": ["personal", "organizational"]
#           },
#           "given_name": {
#           "type": "string"
#           },
#           "family_name": {
#               "type": "string"
#           },
#           "identifiers": {
#               "type": "array",
#               "items": {
#                   "description": "Identifiers object with identifier
#                                   value and scheme in separate keys.",
#                   "type": "object",
#                   "additionalProperties": false,
#                   "properties": {
#                       "identifier": {
#                       "description": "An identifier.",
#                       "type": "string"
#                   },
#                   "scheme": {
#                       "description": "A scheme.",
#                       "type": "string" # VOCABULARY ?
#                   }
#           }
#         },
#         "uniqueItems": true
#         }
#       }
#     },
#     "role": {
#       "description": "Role of creator/contributor.",
#       "type": "object"
#       "additionalProperties": false,
#       "properties": {
#       "id": { # ROLES VOCABULARY }
#       }
#     },
#     "affiliations": {
#       "type": "array",
#       "uniqueItems": true,
#       "items": {
#           type": "object",
#           "additionalProperties": false,
#           "properties": {
#           "id": {
#               # AFFILIATIONS VOCABULARY
#           },
#         }
#       },
#       "required": [
#         "name"
#         ]
#       }
#     }
#   }
#  }
# }


def get_contributor_role(subfield, role, raise_unexpected=False):
    """Clean up roles."""
    translations = {
        "author": "OTHER",
        "author.": "OTHER",
        "dir.": "SUPERVISOR",
        "dir": "SUPERVISOR",
        "supervisor": "SUPERVISOR",
        "ed.": "EDITOR",
        "editor": "EDITOR",
        "editor.": "EDITOR",
        "ed": "EDITOR",
        "ill.": "other",
        "ill": "other",
        "ed. et al.": "EDITOR",
    }
    clean_role = None
    if role is None:
        return "other"
    if isinstance(role, str):
        clean_role = role.lower()
    elif isinstance(role, list) and role and role[0]:
        clean_role = role[0].lower()
    elif raise_unexpected:
        raise UnexpectedValue(subfield=subfield, message="unknown author role")

    if clean_role not in translations or clean_role is None:
        return "other"

    return translations[clean_role].lower()


def get_contributor_affiliations(info):
    """Get affiliations of a contributor/creator."""
    u = info.get("u")
    v = info.get("v")
    if not u and not v:
        return
    if not v:
        affiliations = force_list(u)
    else:
        affiliations = force_list(v)
    parsed_affiliations = [
        StringValue(aff).parse(filter_regex=ALPHANUMERIC_ONLY) for aff in affiliations
    ]
    return parsed_affiliations


def extract_json_contributor_ids(info):
    """Extract author IDs from MARC tags."""
    SOURCES = {
        "AUTHOR|(INSPIRE)": "inspire_author",
        "AUTHOR|(CDS)": "lcds",
        "AUTHOR|(SzGeCERN)": "cern",
    }
    regex = re.compile(r"(AUTHOR\|\((INSPIRE|CDS|SzGeCERN)\))(.*)")
    ids = []
    author_ids = force_list(info.get("0", ""))
    for author_id in author_ids:
        match = regex.match(author_id)
        if match:
            identifier = match.group(3)
            ids.append({"identifier": identifier, "scheme": SOURCES[match.group(1)]})

    author_orcid = info.get("k")
    if author_orcid:
        author_orcid = author_orcid.replace("ORCID:", "")
        new_id = {"identifier": author_orcid, "scheme": "orcid"}
        if new_id not in ids:
            ids.append(new_id)

    inspire = info.get("i", "")
    if inspire and inspire.startswith("INSPIRE-"):
        new_id = {"identifier": inspire, "scheme": "inspire_author"}
        if new_id not in ids:
            ids.append(new_id)

    return ids
