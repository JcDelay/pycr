"""This module provides routine to manipulate Gerrit Code Review Change-Ids"""

import re

from libpycr.exceptions import NoSuchChangeError
from libpycr.gerrit.client import Gerrit
from libpycr.http import RequestFactory
from libpycr.utils.system import fail, warn


# A Gerrit Code Review Change-Id
CHANGE_ID = re.compile('^I[0-9a-f]{8,40}$')

# A Gerrit Code Review legacy Change-Id
LEGACY_CHANGE_ID = re.compile('^\\d+$')

# A range of legacy Change-Ids, eg. 345..349
LEGACY_CHANGE_ID_RANGE = re.compile('^(\\d+)\\.\\.(\\d+)$')


def expand_change_range(change):
    """Expand a change range and returns a list of legacy numeric IDs

    :param change_range: the range of change (POSITIVE..POSITIVE)
    :type change_range: str
    :rtype: list[int]
    """

    match = LEGACY_CHANGE_ID_RANGE.match(change)
    assert match is not None

    lower, upper = match.group(1, 2)
    return range(int(lower), int(upper) + 1)


def fetch_change_list(change_list):
    """Convert a list of changes or change ranges into a list of ChangeInfo

    The input list accepts the following string elements:

        - a change number: POSITIVE
        - a range of change numbers: POSITIVE..POSITIVE
        - a change-id: I[0-9a-f]{8,40}

    :param change_list: the list of changes
    :type change_list: list[str]
    :rtype: list[ChangeInfo]
    """

    change_ids = []

    for change in change_list:
        if CHANGE_ID.match(change) or LEGACY_CHANGE_ID.match(change):
            change_ids.append(change)
        elif LEGACY_CHANGE_ID_RANGE.match(change):
            change_ids.extend([str(i) for i in expand_change_range(change)])
        else:
            warn('invalid Change-Id: %s' % change)

    change_infos = []

    for change_id in change_ids:
        try:
            change_infos.append(Gerrit.get_change(change_id))

        except NoSuchChangeError:
            pass

    return change_infos


def fetch_change_list_or_fail(change_list):
    """Same as fetch_change_list, but fail if the final change list is empty

    :param change_list: the list of changes
    :type change_list: list[str]
    :rtype: list[ChangeInfo]
    """

    changes = fetch_change_list(change_list)

    # If no correct changes found
    if not changes:
        message = 'no valid change-id provided'
        if not RequestFactory.require_auth():
            message += ' (missing authentication?)'
        fail(message)

    return changes
