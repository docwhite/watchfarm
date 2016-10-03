import os
import time

import pysftp

def get_abs_form_rel(rel_rem_dir, username):
    return os.path.join(
        '/',
        os.path.join(
            'home',
            username,
            *rel_rem_dir.split('/')
        )
    )

class FarmWatcher:
    extensions = ['.png', '.exr', '.jpg', '.jpeg', '.txt']
    def __init__(self, username, password, rel_rem_dir, rel_loc_dir, host='tete'):
        self.__host = host
        self.__username = username
        self.__password = password

        sanitized_paths = [get_abs_form_rel(x, self.__username) for x in [rel_rem_dir, rel_loc_dir]]

        self.__abs_rem_dir = sanitized_paths[0]
        self.__abs_loc_dir = sanitized_paths[1]

        self.__processed = []
        print "Renderfarm path -->", self.__abs_rem_dir
        print "Destination path  -->", self.__abs_loc_dir

    def run(self, delay_seconds):
        with pysftp.Connection(
            self.__host,
            self.__username,
            password=self.__password
        ) as sftp:
            sftp.chdir(self.__abs_rem_dir)
            while True:
                current_dir = sftp.pwd
                listed_stuff = sftp.listdir()
                for item in listed_stuff:
                    if item not in self.__processed and os.path.splitext(item)[1] in self.extensions:
                        print "New item dropped: ", item

                        remote_absolute_path = os.path.join(sftp.pwd, item)
                        local_absolute_path = os.path.join(self.__abs_loc_dir, item)

                        sftp.get(remote_absolute_path, local_absolute_path)
                        sftp.remove(remote_absolute_path)

                        self.__processed.append(item)

                time.sleep(delay_seconds)

        sftp.close()