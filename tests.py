import unittest
import os
import shutil

from gifing_bot_tasks import (
    video_to_frames,
    save_video,
    frames_to_gif,
)


class ConversionTests(unittest.TestCase):

    """
    Test all of the video/gif conversion
    functions.
    """

    def test_save_video(self):
        video_name = save_video(
            'https://raw.githubusercontent.com/' +
            'jeremylow/TheGIFingBot/master/data/CPwOtkpWUAEZnqm.mp4'
        )
        self.assertTrue(os.path.isfile(video_name))
        self.addCleanup(os.remove, video_name)

    def test_video_to_frames(self):
        temp_folder = video_to_frames('data/test_video.mp4')
        files = os.listdir(temp_folder)
        self.assertEqual(len(files), 5)
        self.addCleanup(
            shutil.rmtree,
            temp_folder
        )

    def test_conversion_to_gif(self):
        gif_file = frames_to_gif('data/test_frames')
        self.assertTrue(os.path.isfile(gif_file))


if __name__ == '__main__':
    unittest.main()
