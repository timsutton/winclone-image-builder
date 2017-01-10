#!/usr/bin/python
#
# Really simple test screen recorder script that could be used as an option
# during the Windows image build process. It's very frustrating to wait an
# hour for an image to finish a long build only to see that there was
# a very briefly-shown error in Windows before things aborted. I sometimes
# manually record screen captures while testing new changes to tne image build,
# but with something like this I wouldn't need to remember to do it each time.
# Currently this just runs for 10 seconds and records to "foo.mov" in the
# CWD.

# pylint: disable-msg=e1101,e0611
import time
import AVFoundation as AVF
import Quartz

from Foundation import NSObject, NSURL

def main():
    display_id = Quartz.CGMainDisplayID()

    session = AVF.AVCaptureSession.alloc().init()
    screen_input = AVF.AVCaptureScreenInput.alloc().initWithDisplayID_(display_id)
    file_output = AVF.AVCaptureMovieFileOutput.alloc().init()

    session.addInput_(screen_input)
    session.addOutput_(file_output)
    session.startRunning()

    file_url = NSURL.fileURLWithPath_('foo.mov')
    # Cheat and pass a dummy delegate object where normally we'd have a
    # AVCaptureFileOutputRecordingDelegate
    file_url = file_output.startRecordingToOutputFileURL_recordingDelegate_(
                file_url, NSObject.alloc().init())
    time.sleep(10)
    session.stopRunning()

if __name__ == '__main__':
    main()
