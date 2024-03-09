# How to convert a Google Doc into a git repository, containing the history of the document.

## Clone gitdriver.

This example clones my branch with corrections,
however the original may now have those and/or other alterations.

    git clone git@github.com:wu-lee/gitdriver.git -b usage-notes
	
The original repo is at https://github.com/MartinoMensio/gitdriver

Note, we're going to be extracting markdown version of documents, for
which gitdriver needs the `pandoc` tool to be installed and on the
path (see gitdrivers' documentation for a bit more info).

## Configure gitdriver

This amounts to creating a file gd.conf containing:

    googledrive:
      client id: <redacted>.apps.googleusercontent.com
      client secret: <redacted>

The `<redacted>` portions were removed - they're API keys! You need to
get these for your case by following the instructions in the README
within gitdriver.

## Get the ID for the GDoc article you want to convert

This is in the URL of the document, the penultimate component:

https://docs.google.com/document/d/1j6Ygv0_this_is_a_fake_document_id_a8Q66mvt4/edit

In this case the ID is `1j6Ygv0_this_is_a_fake_document_id_a8Q66mvt4`

Of course, you need to have access to this document!  gitdriver will
use your credentials, as obtained in the previous step, to access that
using Google Docs' API.

## Run gitdriver

You might want to set up a directory for your new git repositories. To
do this, gitdriver needs to be on your python path:

   cd gitdriver # assuming this is where you checked it out
   export PYTHONPATH="$PWD"
   export GD_CONF="$PWD/tmp/gd.conf" # assuming this is where you put your config

Then create/change to your directory as necessary.

Run gitdriver like this, within the directory you want to create the
git repositories:

    python -m gitdriver --config $GD_CONF -M 1j6Ygv0_this_is_a_fake_document_id_a8Q66mvt4

gitdriver attempts to access the document - you'll get a prompt like this:

> Point your browser at the following URL and then 
> enter the authorization code at the prompt:
>
> https://accounts.google.com/o/oauth2/auth?<parameters redacted>

Follow the instructions - it helps to have signed in already. You'll
get a bunch of warnings about unverified/untrusted applications,
you'll need to confirm and click through these. Make sure on the final
page you check the box to grant access, or gitdriver will die with a
cryptic error:

> gitdriver wants access to your Google Account
>
> Select what gitdriver can access
> - See, edit, create and delete all of your Google Drive files. [ ]

Finally you'll be presented with an authorisation code.  Cut and paste
this into the terminal at the prompt, and hit <enter>.

It should now create the repository.  This can then be published or
otherwise inspected or used in the usual ways.
