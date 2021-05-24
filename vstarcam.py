"""Tool to extract/create a firmware for VStarCam wi-fi webcam."""
import sys
import argparse
import struct
import logging


class VStarCam:
    """Fictional class to group up methods and constants."""

    prefix = b'www.object-camera.com.by.hongzx.'
    postfix = b'www.object-camera.com.by.hongzx.'[::-1]
    # struct description could be found in sysdepack binary
    # https://files.catbox.moe/9dlhx7.png
    struct_header = '<64s64sIiI'

    @classmethod
    def extract(cls, firmware_file):
        """Extract a firmware file and create a buildfile.txt."""
        with open(firmware_file, 'rb') as f, \
                open('buildfile.txt', 'w') as filelist:
            assert cls.prefix == f.read(32)
            buf = f.read(32)
            while buf != cls.postfix:
                buf += f.read(32 + 64 + 4 + 4 + 4)
                (
                    path,
                    filename,
                    filesize,
                    version,
                    factory,
                ) = struct.unpack(cls.struct_header, buf)
                path = path.decode('utf-8').rstrip('\x00')
                filename = filename.decode('utf-8').rstrip('\x00')
                logger.info((path, filename, filesize, version, factory))
                file = f.read(filesize)
                with open(filename, 'wb') as out:
                    out.write(file)
                filelist.write('\t'.join([path, filename]) + '\n')
                buf = f.read(32)

    @classmethod
    def create(cls, buildfile):
        """Create a new firmware from buildfile."""
        version = 808791301  # does it need to be changed?
        factory = 0
        firmware = b''
        for path, filename in cls._get_filelist(buildfile):
            with open(filename, 'rb') as f:
                file = f.read()
            data = (
                path.encode('utf-8'),
                filename.encode('utf-8'),
                len(file),
                version,
                factory
            )
            logger.info(data)
            firmware += struct.pack(cls.struct_header, *data)
            firmware += file
        with open('firmware.bin', 'wb') as f:
            f.write(cls.prefix + firmware + cls.postfix)

    @staticmethod
    def _get_filelist(filename):
        with open(filename, 'r') as f:
            for row in f:
                path, name = row.rstrip('\n').split('\t')
                if path and name:
                    yield (path, name)


def main():
    """Main function."""
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        '--extract', '-e',
        metavar='<firmware_file>',
        dest='firmware_file',
        help='unpack an existing firmware file',
    )
    actions.add_argument(
        '--create', '-c',
        metavar='<buildfile>',
        dest='buildfile',
        help='''create a new firmware file using buildfile
            (tab-separated path+filename pairs per line)''',
    )
    args = vars(parser.parse_args())

    firmware = args.get('firmware_file')
    buildfile = args.get('buildfile')
    if firmware:
        VStarCam.extract(firmware)
    if buildfile:
        VStarCam.create(buildfile)


if __name__ == '__main__':
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    stdout_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stdout_handler)
    main()
