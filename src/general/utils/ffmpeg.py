import json
import subprocess


def get_resolution(video):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of',
         'json', video], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    width = json.loads(result.stdout)['streams'][0]['width']
    height = json.loads(result.stdout)['streams'][0]['height']

    return width, height


def get_duration(video):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
         video], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration = round(float(result.stdout))
    return duration
