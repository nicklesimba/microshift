#!/usr/bin/env python3

"""Tool for bringing a ticket into the current sprint and updating its status.

Ticket ID
---------

The default ticket ID discovered by parsing the current branch name,
looking for the pattern

  <project-id>-<ticket-num>[-<description>]

For example

  USHIFT-1069-jira-manage-ticket

produces a ticket ID of

  USHIFT-1069

Set a ticket ID explicitly using the `--ticket-id` option.

Sprint
------

The ticket is added to the current active sprint by looking at the
sprints visible through the MicroShift Scrum Board
(https://issues.redhat.com/secure/RapidBoard.jspa?rapidView=14885) and
finding the active sprint beginning with "uShift". Disable this
behavior using the `--no-sprint` flag.

Target Version
--------------

The `--target-version` flag can be used to set a target version if one
is not set already.

Status
------

Use the `--in-progress` or `--review` options to control the
status. The default is `--review`.

Authentication
--------------

The script requires a Jira token passed via the `JIRA_API_TOKEN`
environment variable. See README.md for details of creating the token.

"""

import argparse
import os
import subprocess

import jira

SERVER_URL = 'https://issues.redhat.com/'
SCRUM_BOARD = 14885


def custom_field_manager(server):
    """Return callables for working with custom fields.

    Custom fields are stored on the ticket in ticket.fields with names
    like "customfield_12319940". The information about those fields
    can be queried from the Jira API to map the user-visible names
    (like "Target Version") to the less helpful custom field attribute
    name. This function looks up the mappings and then creates two
    closures that can get and set values from a ticket using the
    understandable names.

    The getter takes a ticket and custom field name and returns the
    value of the field for that ticket.

    The setter takes a ticket, custom field name, and new value and
    updates the ticket to set that field to the new value.

    """
    field_info = server.fields()
    fields_by_name = {
        f['name']: f
        for f in field_info
    }

    def get_field_value(ticket, name):
        field_details = fields_by_name[name]
        return getattr(ticket.fields, field_details['id'])

    def set_field_value(ticket, name, value):
        field_details = fields_by_name[name]
        return ticket.update(fields={
            field_details['id']: value,
        })

    return get_field_value, set_field_value


def get_active_sprint(server, project_id):
    """Return the active sprint for the USHIFT project."""
    valid_sprints = server.sprints(SCRUM_BOARD, state='active')
    for s in valid_sprints:
        if not s.name.lower().startswith(project_id.lower()):
            continue
        return s
    return None


def get_project_id_from_ticket_id(ticket_id):
    """Parse a ticket ID and return the project portion.

    "USHIFT-662" -> "USHIFT"

    """
    return ticket_id.partition('-')[0]


def guess_ticket_id():
    """Try to determine the ticket ID from the git branch."""
    # git branch --show-current
    completed = subprocess.run(
        ['git', 'branch', '--show-current'],
        stdout=subprocess.PIPE,
        check=False,  # no exception when we cannot find the branch
    )
    if completed.returncode != 0:
        return None
    branch_name = completed.stdout.decode('UTF-8').strip()
    parts = branch_name.split('-')
    if len(parts) < 2:
        print(f'Unable to determine ticket ID from "{branch_name}"')
        return None
    return parts[0] + '-' + parts[1]


def main():
    """The main program."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--ticket-id',
        default=guess_ticket_id(),
        help='the ticket id, defaults to the prefix of the branch name (%(default)s)',
    )
    parser.add_argument(
        '--target-version',
        help='the target version',
    )
    parser.add_argument(
        '--no-sprint',
        dest='sprint',
        default=True,
        action='store_false',
        help='set the sprint to the active sprint',
    )
    parser.add_argument(
        '--review',
        dest='status',
        default='Code Review',
        action='store_const',
        const='Code Review',
        help='mark the ticket as ready for code review',
    )
    parser.add_argument(
        '--in-progress',
        dest='status',
        action='store_const',
        const='In Progress',
        help='mark the ticket as having been started',
    )
    args = parser.parse_args()

    actual_project_id = get_project_id_from_ticket_id(args.ticket_id)
    sprint_project_id = actual_project_id
    if sprint_project_id == 'OCPBUGS':
        sprint_project_id = 'USHIFT'

    server = jira.JIRA(
        server=SERVER_URL,
        token_auth=os.environ.get('JIRA_API_TOKEN'),
    )
    _, setter = custom_field_manager(server)

    print(f'finding ticket {args.ticket_id}')
    ticket = server.issue(args.ticket_id)
    print(f'found: "{ticket.fields.summary}"')

    jira_id = server.myself()['key']
    print(f'...updating assignment to "{jira_id}"')
    server.assign_issue(ticket, jira_id)

    if args.target_version:
        # Validate the version
        for v in server.project(actual_project_id).versions:
            if args.target_version == v.name:
                break
        else:
            raise ValueError('Unknown version')
        print(f'...setting the target version to "{args.target_version}"')
        setter(ticket, 'Target Version', [{'name': args.target_version}])

    if args.sprint:
        active_sprint = get_active_sprint(server, sprint_project_id)
        if not active_sprint:
            raise ValueError('No active sprint found')
        print(f'...setting the sprint to "{active_sprint}"')
        server.add_issues_to_sprint(active_sprint.id, [ticket.key])

    if actual_project_id == 'OCPBUGS':
        print('...ticket status is managed automatically')
    else:
        print(f'...setting ticket status to "{args.status}"')
        server.transition_issue(
            issue=ticket,
            transition=args.status,
        )


if __name__ == '__main__':
    try:
        main()
    except Exception as err:  # pylint: disable=broad-except
        print(f'ERROR: {err}')
