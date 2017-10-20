#!/usr/bin/env python

from gitdriver import *
import json

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--config', '-f', default='gd.conf')
    p.add_argument('--text', '-T', action='append_const', const='text/plain', dest='mime_type')
    p.add_argument('--html', '-H', action='append_const', const='text/html', dest='mime_type')
    p.add_argument('--mime-type', action='append', dest='mime_types', default=[])
    p.add_argument('--all-types', action='store_true', default=True, help='Export all available mime types')
    p.add_argument('--exclude-type', action='append', dest='exclude_types', default=[])
    p.add_argument('--raw', '-R', action='store_true', help='Download original document if possible.')
    p.add_argument('gdrive_sync_src_folder')
    p.add_argument('target_folder')
    return p.parse_args()

GDRIVE_EXTS = {'gdoc', 'gmap', 'gsheet', 'gslides'}

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
    for src_folder, dirnames, filenames in os.walk(opts.gdrive_sync_src_folder):
        rel_folder = os.path.relpath(src_folder, opts.gdrive_sync_src_folder)
        target_folder = os.path.join(opts.target_folder, rel_folder)
        if not os.path.exists(target_folder):
            os.mkdir(target_folder)
        gdrive_files = [f for f in filenames if os.path.splitext(f)[1][1:] in GDRIVE_EXTS]
        extensions_present = {}
        for filename in gdrive_files:
            name, extension = os.path.splitext(filename)
            extensions_present.setdefault(name, []).append(extension[1:])
        other_files = [f for f in filenames if f not in gdrive_files]
        for filename in gdrive_files:
            name, extension = os.path.splitext(filename)
            type_suffix = extension if len(extensions_present[name]) > 1 else ''
            print("Exporting %s/%s" % (rel_folder, filename))
            export_gdrive_file(gd, os.path.join(src_folder, filename), target_folder, opts, type_suffix)

def get_target_filenames(basename, rev, opts):
    mime_types = rev['exportLinks'].keys() if opts.all_types else opts.mime_types
    for mime_type in mime_types:
        if mime_type in opts.exclude_types:
            continue
        filename_suffix = MIME_TYPE_SUFFIXES.get(mime_type, mimetypes.guess_extension(mime_type, False))
        if not filename_suffix:
            logging.warning("Could not determine extension for mime_type %s", mime_type)
            filename_suffix = ".%s" % mime_type.replace('/', '_')
        filename = '%s%s' % (basename, filename_suffix)
        yield filename

def export_gdrive_file(gd, src_file, target_folder, opts, type_suffix=''):
    with open(src_file) as s:
        md = json.load(s)
    docid = md['doc_id']
    # get full metadata from server
    md = gd.get_file_metadata(docid)
    basename = md['title'].replace('/', '_') + type_suffix
    revisions = list(gd.revisions(docid))
    print 'Update document "%s" - %d revisions' % (md['title'] + type_suffix, len(revisions))
    target_files = [os.path.join(target_folder, f) for f in get_target_filenames(basename, revisions[-1], opts)]
    if type_suffix:
        untyped_files = [os.path.join(target_folder, f) for f in get_target_filenames(basename[:-len(type_suffix)], revisions[-1], opts) if f.replace(basename, '').count('.') == 1]
        untyped_files = [f for f in untyped_files if os.path.exists(f)]
        if len(untyped_files) > 1:
            raise ValueError("Document %s in %s requires a type suffix but existing revisions didn't have it; fix manually" % (basename, target_folder))
    if True in [os.path.exists(f) for f in target_files]:
        last_commit_message = subprocess.check_output(['git', 'log', '-n', '1', '--format=%B'] + target_files)
        print 'Last commit: ' + last_commit_message + 'Iterating Google Drive revisions:'
        revision_matched = False
    else:
        revision_matched = True
    for n, rev in enumerate(revisions):
        if revision_matched:
            print "New revision: " + rev['modifiedDate'] + " (%d/%d)" % (n+1, len(revisions))
            commit_revision(gd, opts, rev, md, target_folder, type_suffix)
        elif rev['modifiedDate'] in last_commit_message:
            print "Found matching revision: " + rev['modifiedDate']
            revision_matched = True
    print "Repository is up to date."

if __name__ == '__main__':
    main()


