import os, logging, subprocess
from typing import Set

SRC_DIR = 'SRC_DIR_HERE'
MP4_EXTENSION = '.mp4'
VTT_EXTENSION = '.vtt'
SRT_EXTENSION = '.srt'

class Mp4:
    def __init__(self, original_filename: str, temp_filename: str) -> None:
        self.original_filename = original_filename
        self.temp_filename = str(temp_filename) + MP4_EXTENSION
        self._write_temp_filename()

    def _write_temp_filename(self) -> None:
        try:
            os.rename('{}{}'.format(SRC_DIR, self.get_original_filename()),
                      '{}{}'.format(SRC_DIR, self.get_temp_filename()))
        except OSError as e:
            logging.error('Error while renaming mp4! Exiting...')
            raise SystemExit(e)

    def get_original_filename(self) -> str:
        return self.original_filename
    
    def get_temp_filename(self) -> str:
        return self.temp_filename
    
class Srt:
    def __init__(self, original_filename: str, temp_filename: str) -> None:
        self.original_filename = original_filename
        self.temp_filename = str(temp_filename) + SRT_EXTENSION
        self.srt_filename = self._get_original_filename().replace(VTT_EXTENSION, SRT_EXTENSION)
        self._convert_vtt_to_srt()
        self._write_temp_filename()

    def _convert_vtt_to_srt(self) -> None:
        logging.info('Converting subtitles...')
        proc = subprocess.run(['ffmpeg',
                               '-i', SRC_DIR + self._get_original_filename(),
                               SRC_DIR + self.get_srt_filename()
                               ],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.STDOUT)
        
        if proc.returncode == 0:
            logging.info('Successfully converted {} subtitles!'.format(self._get_original_filename()))
        else:
            logging.error('Error while converting subtitles! Exiting...')
            raise SystemExit(proc.returncode)

    def _write_temp_filename(self) -> None:
        try:
            os.rename('{}{}'.format(SRC_DIR, self._get_original_filename()),
                      '{}{}'.format(SRC_DIR, self.get_temp_filename()))
        except OSError as e:
            logging.error('Error while renaming srt! Exiting...')
            raise SystemExit(e)

    def _get_original_filename(self) -> str:
        return self.original_filename
    
    def get_temp_filename(self) -> str:
        return self.temp_filename
    
    def get_srt_filename(self) -> str:
        return self.srt_filename

class Mp4SrtHandler:
    def __init__(self) -> None:
        self.mp4s = set()
        self.srts = set()

    def add_mp4(self, mp4: Mp4) -> None:
        self.get_mp4s().add(mp4)

    def add_srt(self, srt: Srt) -> None:
        self.get_srts().add(srt)

    def get_mp4s(self) -> Set[Mp4]:
        return self.mp4s
    
    def get_srts(self) -> Set[Srt]:
        return self.srts

class Mp4SrtMuxer:
    def __init__(self, mp4s_srts: Mp4SrtHandler) -> None:
        self.mp4s_srts = mp4s_srts

    def mux_mp4s_srts(self) -> None:
        mp4s_srts = self._get_mp4s_srts()

        for mp4, srt in zip(mp4s_srts.get_mp4s(), mp4s_srts.get_srts()):
            logging.info('Muxing...')
            proc = subprocess.run(['ffmpeg',
                                   '-i', SRC_DIR + mp4.get_temp_filename(),
                                   '-i', SRC_DIR + srt.get_temp_filename(),
                                   '-c:v', 'copy',
                                   '-c:a', 'copy',
                                   '-c:s', 'mov_text',
                                   '-metadata:s:a:0', 'language=eng',
                                   '-metadata:s:s:0', 'language=eng',
                                   SRC_DIR + mp4.get_original_filename()
                                   ],
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.STDOUT)
            
            if proc.returncode == 0:
                logging.info('Successfully muxed {}!'.format(mp4.get_original_filename()))
                try:
                    logging.info('Removing source files...')
                    os.remove(SRC_DIR + mp4.get_temp_filename())
                    os.remove(SRC_DIR + srt.get_temp_filename())
                    os.remove(SRC_DIR + srt.get_srt_filename())
                    logging.info('Removed source files!')
                except OSError as e:
                    logging.error('Failed to remove a file! Exiting...')
                    raise SystemExit(e)
            else:
                logging.error('Error while muxing! Exiting...')
                raise SystemExit(proc.returncode)
    
    def _get_mp4s_srts(self) -> Mp4SrtHandler:
        return self.mp4s_srts

def init_logger() -> None:
    logging.basicConfig(level=logging.INFO,
                        format='{asctime} :: {levelname} :: {module} :: {funcName} :: {message}',
                        style='{',
                        handlers=[
                            logging.StreamHandler()
                        ])
    
def main() -> None:
    init_logger()

    logging.info('Starting muxer...')
    mp4_filenames = [f for f in os.listdir(SRC_DIR) if f.endswith(MP4_EXTENSION)]
    vtt_filenames = [f for f in os.listdir(SRC_DIR) if f.endswith(VTT_EXTENSION)]

    if len(mp4_filenames) is not len(vtt_filenames):
        logging.error('Mismatch in mp4 and vtt count! Exiting...')
        raise SystemExit()

    mp4_srt_handler = Mp4SrtHandler()
    for count, mp4_filename in enumerate(mp4_filenames):
        mp4_srt_handler.add_mp4(Mp4(mp4_filename, count))

    for count, vtt_filename in enumerate(vtt_filenames):
        mp4_srt_handler.add_srt(Srt(vtt_filename, count))
    
    mp4_srt_muxer = Mp4SrtMuxer(mp4_srt_handler)
    mp4_srt_muxer.mux_mp4s_srts()
    logging.info('Completed all muxing!')

if __name__ == "__main__":
    main()