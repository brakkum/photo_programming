from photo import Photo
from PIL import Image
import math
import exifread
import rawpy
import os

class Timelapse:
    def __init__(self, directory):
        self.path = directory.dir_path
        self.files = directory.files
        self.photos = self.make_photos()
        self.change_points = self.find_changes()
        self.ev_changes = self.make_ev_array()
        self.update_photo_objects()
        self.save_photos()

    def save_photos(self):
        for photo in self.photos:
            raw = rawpy.imread(photo.data)
            # TODO auto white balance option
            rgb = raw.postprocess(
                exp_shift=photo.shift,
                use_auto_wb=True,
                no_auto_bright=True)
            raw.close()
            img = Image.fromarray(rgb)  # Pillow image
            img.save('{}/new_photos/{}.tiff'.format(photo.path, photo.name))

    def update_photo_objects(self):
        for i in range(len(self.ev_changes)):
            self.photos[i].update_ev(self.ev_changes[i])

    def get_val(self, i, val):
        if val == 'shut':
            return self.photos[i].shut
        elif val == 'iso':
            return self.photos[i].iso
        elif val == 'fNum':
            return self.photos[i].fNum
        else:
            return

    def get_increments(self, ev_change, steps):
        return ev_change / steps

    def get_ev_change(self, start, stop):
        return -(math.log2(start) - math.log2(stop))

    def make_ev_array(self):
        change_array = []
        # TODO Refactor all this junk
        # TODO add ev changes for images after final change?
        for i in range(len(self.change_points) - 1):
            start_index = self.change_points[i]['index']
            next_start = self.change_points[i + 1]['index']
            being_changed = self.change_points[i + 1]['change']
            start_val = self.get_val(start_index, being_changed)
            end_val = self.get_val(next_start, being_changed)
            ev_change = self.get_ev_change(start_val, end_val)
            increments = self.get_increments(ev_change, next_start - start_index)
            for j in range(0, next_start - start_index):
                change_array.append(round((increments * j), 3))
        return change_array

    def find_changes(self):
        diff_array = [{'index': 0}]
        for i in range(0, len(self.photos)):
            if i != len(self.photos) - 1:
                if self.photos[i].shut != self.photos[i + 1].shut:
                    change = self.photos[i + 1].shut
                    diff_array.append({
                        'index': i + 1,
                        'change': 'shut'})
                elif self.photos[i].iso != self.photos[i + 1].iso:
                    change = self.photos[i + 1].iso
                    diff_array.append({
                        'index': i + 1,
                        'change': 'iso'})
                elif self.photos[i].fNum != self.photos[i + 1].fNum:
                    change = self.photos[i + 1].fNum
                    diff_array.append({
                        'index': i + 1,
                        'change': 'fNum'})
        # TODO Add option to adjust start and stop here?
        return diff_array

    def get_exif(self, photo):
        tags = exifread.process_file(open(photo, 'rb'))
        return tags

    def make_photo(self, photo):
        data = open('{}/{}'.format(self.path, photo), 'rb')
        exif = self.get_exif('{}/{}'.format(self.path, photo))
        return Photo(data, exif, photo, self.path)

    def make_photos(self):
        photos = []
        for photo in self.files:
            photos.append(self.make_photo(photo))
        return photos