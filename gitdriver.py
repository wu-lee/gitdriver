#!/usr/bin/python

import logging
import os
import pprint
import sys
import argparse
import mimetypes
import subprocess
import yaml

from drive import GoogleDrive, DRIVE_RW_SCOPE

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--config', '-f', default='gd.conf')
    p.add_argument('--text', '-T', action='append_const', const='text/plain',
            dest='mime_type')
    p.add_argument('--html', '-H', action='append_const', const='text/html',
            dest='mime_type')
    p.add_argument('--mime-type', action='append', dest='mime_types', default=[])
    p.add_argument('--all-types', action='store_true',
            help='Export all available mime types')
    p.add_argument('--exclude-type', action='append', dest='exclude_types', default=[])
    p.add_argument('--raw', '-R', action='store_true',
            help='Download original document if possible.')
    p.add_argument('docid')

    return p.parse_args()

# override text/plain as otherwise it returns .ksh
MIME_TYPE_SUFFIXES = {
    'application/x-vnd.oasis.opendocument.spreadsheet': '.ods',
    'application/epub+zip': '.epub',
    'text/plain': '.txt',
}

def commit_revision(gd, opts, rev, md):
    # Prepare environment variables to change commit time
    env = os.environ.copy()
    date = rev['modifiedDate']
    basename = md.get('title', 'content')
    owner_users = [owner.get('displayName', None) for owner in md.get('owners', [])]
    owner_emails = [owner.get('emailAddress', None) for owner in md.get('owners', [])]
    user = rev.get('lastModifyingUserName', None)
    email = rev.get('lastModifyingUser', {}).get('emailAddress', None)
    if (user is None and not owner_users) or (email is None and not owner_emails):
        logging.warning("Could not determine user from revision info:\n%s", pprint.pformat(rev))
    env['GIT_COMMITTER_DATE'] = env['GIT_AUTHOR_DATE'] = date
    env['GIT_COMMITTER_NAME'] = env['GIT_AUTHOR_NAME'] = user or ' '.join(owner_users) or 'Unknown User'
    env['GIT_COMMITTER_EMAIL'] = env['GIT_AUTHOR_EMAIL'] = email or ' '.join(owner_emails) or 'unknown'

    mime_types = rev['exportLinks'].keys() if opts.all_types else opts.mime_types
    for mime_type in mime_types:
        if mime_type in opts.exclude_types:
            continue
        filename_suffix = MIME_TYPE_SUFFIXES.get(mime_type, mimetypes.guess_extension(mime_type, False))
        if not filename_suffix:
            logging.warning("Could not determine extension for mime_type %s", mime_type)
            filename_suffix = ".%s" % mime_type.replace('/', '_')
        filename = '%s%s' % (basename, filename_suffix)
        with open(filename, 'w') as fd:
            if 'exportLinks' in rev and not opts.raw:
                # If the file provides an 'exportLinks' dictionary,
                # download the requested MIME type.
                r = gd.session.get(rev['exportLinks'][mime_type])
            elif 'downloadUrl' in rev:
                # Otherwise, if there is a downloadUrl, use that.
                r = gd.session.get(rev['downloadUrl'])
            else:
                raise KeyError('unable to download revision')

            # Write file content into local file.
            for chunk in r.iter_content():
                fd.write(chunk)

        # Commit changes to repository.
        subprocess.call(['git', 'add', filename])
    subprocess.call(['git', 'commit', '-m', 'revision from %s' % date], env=env)


def main():
    opts = parse_args()
    if not opts.mime_types and not opts.all_types:
		print "At least one mime-type must be given!"
		exit(1)
    cfg = yaml.load(open(opts.config))
    gd = GoogleDrive(
            client_id=cfg['googledrive']['client id'],
            client_secret=cfg['googledrive']['client secret'],
            scopes=[DRIVE_RW_SCOPE],
            )

    # Establish our credentials.
    gd.authenticate()

    # Get information about the specified file.  This will throw
    # an exception if the file does not exist.
    md = gd.get_file_metadata(opts.docid)

    if os.path.isdir(md['title']):
        # Find revision matching last commit and process only following revisions
        os.chdir(md['title'])
        print 'Update repository "%(title)s"' % md
        last_commit_message = subprocess.check_output('git log -n 1 --format=%B', shell=True)
        print 'Last commit: ' + last_commit_message + 'Iterating Google Drive revisions:'
        revision_matched = False
        for rev in gd.revisions(opts.docid):            
            if revision_matched:
                print "New revision: " + rev['modifiedDate']
                commit_revision(gd, opts, rev, md)
            if rev['modifedDate'] in last_commit_message:
                print "Found matching revision: " + rev['modifiedDate']
                revision_matched = True
        print "Repository is up to date."
    else:
        # Initialize the git repository.
        print 'Create repository "%(title)s"' % md
        subprocess.call(['git','init',md['title']])
        os.chdir(md['title'])

        # Iterate over the revisions (from oldest to newest).
        for rev in gd.revisions(opts.docid):
            commit_revision(gd, opts, rev, md)
if __name__ == '__main__':
    main()

