#!/usr/bin/python

import os
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
    p.add_argument('--mime-type', action='append', dest='mime_type', default=[])
    p.add_argument('--all-types', action='store_true',
            help='Export all available mime types')
    p.add_argument('--raw', '-R', action='store_true',
            help='Download original document if possible.')
    p.add_argument('docid')

    return p.parse_args()

# override text/plain as otherwise it returns .ksh
MIME_TYPE_SUFFIXES = {
    'text/plain': '.txt',
}

def commit_revision(gd, opts, rev, basename='content'):
    # Prepare environment variables to change commit time
    env = os.environ.copy()
    env['GIT_COMMITTER_DATE'] = rev['modifiedDate']
    env['GIT_AUTHOR_DATE'] = rev['modifiedDate']
    env['GIT_COMMITTER_NAME'] = rev['lastModifyingUserName']
    env['GIT_AUTHOR_NAME'] = rev['lastModifyingUserName']
    env['GIT_COMMITTER_EMAIL'] = rev['lastModifyingUser']['emailAddress']
    env['GIT_AUTHOR_EMAIL'] = rev['lastModifyingUser']['emailAddress']

    mime_types = rev['exportLinks'].keys() if opts.all_types else opts.mime_type
    for mime_type in mime_types:
        filename_suffix = MIME_TYPE_SUFFIXES.get(mime_type, mimetypes.guess_extension(mime_type, False))
        filename_suffix = filename_suffix or ".%s" % mime_type.replace('/', '_')
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
    subprocess.call(['git', 'commit', '-m', 'revision from %s' % rev['modifiedDate']], env=env)


def main():
    opts = parse_args()
    if not opts.mime_type and not opts.all_types:
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
                commit_revision(gd, opts, rev, md['title'])
            if rev['modifiedDate'] in last_commit_message:
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
            commit_revision(gd, opts, rev, md['title'])
if __name__ == '__main__':
    main()

