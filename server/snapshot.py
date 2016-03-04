import hashlib
import os.path
join = os.path.join
import shutil

from config import config

STORAGE_DIR = config.get('STORAGE_DIR') or config['SIM_STORAGE_DIR']

# where the actual files are stored. name = sha1("H" + file content), contents = file content
DB_DIR = join(STORAGE_DIR, "files_by_sha1", '')

# where the snapshots are stored as hardlink trees
SNAP_DIR = join(STORAGE_DIR, "sim_snapshots", '')


from util import mkdirp, makehardlink

mkdirp(DB_DIR)
mkdirp(SNAP_DIR)



def raise_wat(p):
    raise Exception('What kind of thing are you?: ' + p)


def dedupe_cp(src, dest):
    """
    both src and dest should be absolute paths
    src must exist
    dest must not exist
    """
    if os.path.isfile(src):
        h = hashlib.sha1()
        with open(src, 'rb') as f:
            # assumes the file is relatively small for now.
            data = f.read()
        h.update(data)
        dry_file_path = join(DB_DIR, h.hexdigest())

        if not os.path.exists(dry_file_path):
            # can replace this with shutil copyfile if files get really large.
            with open(dry_file_path, 'wb') as f:
                f.write(data)

        if os.path.isdir(dest):
            dest = join(dest, os.path.basename(src))

        makehardlink(dry_file_path, dest)

    elif os.path.isdir(src):
        os.mkdir(dest)
        for fname in os.listdir(src):
            dedupe_cp(join(src, fname), join(dest, fname))
    else:
        raise_wat(src)

def snapshot(source_path, snap_name):
  # store entire directory in the object DB
  # then recreates file tree in the snapdir with links to the files in object DB.
  dedupe_cp(source_path, join(SNAP_DIR, snap_name))

def del_snapshot(snap_name):
    shutil.rmtree(join(SNAP_DIR, snap_name))

def clean_snapshots(keep_set):
    # TODO also clean files which no longer have links to them
    snaps_on_fs = os.listdir(SNAP_DIR)
    for snap_name in snaps_on_fs:
        if snap_name not in keep_set:
            del_snapshot(snap_name)
