# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
try:
  import Queue
except ImportError:
  import queue as Queue

import datetime
import logging
import re
import threading


# Log marker containing SurfaceTexture timestamps.
_SURFACE_TEXTURE_TIMESTAMPS_MESSAGE = 'SurfaceTexture update timestamps'
_SURFACE_TEXTURE_TIMESTAMP_RE = '\d+'

_MIN_NORMALIZED_FRAME_LENGTH = 0.5


class SurfaceStatsCollector(object):
  """Collects surface stats for a SurfaceView from the output of SurfaceFlinger.

  Args:
    adb: the adb connection to use.
  """
  class Result(object):
    def __init__(self, name, value, unit):
      self.name = name
      self.value = value
      self.unit = unit

  def __init__(self, dev, activity):
    self._dev = dev
    self._collector_thread = None
    self._use_legacy_method = False
    self._surface_before = None
    self._get_data_event = None
    self._data_queue = None
    self._stop_event = None
    self._results = []
    self._warn_about_empty_data = True
    self._activity = activity

  def DisableWarningAboutEmptyData(self):
    self._warn_about_empty_data = False

  def Start(self):
    assert not self._collector_thread

    if self._ClearSurfaceFlingerLatencyData():
      self._get_data_event = threading.Event()
      self._stop_event = threading.Event()
      self._data_queue = Queue.Queue()
      self._collector_thread = threading.Thread(target=self._CollectorThread)
      self._collector_thread.start()
    else:
      self._use_legacy_method = True
      self._surface_before = self._GetSurfaceStatsLegacy()

  def Stop(self):
    self._StorePerfResults()
    if self._collector_thread:
      self._stop_event.set()
      self._collector_thread.join()
      self._collector_thread = None

  def SampleResults(self):
    self._StorePerfResults()
    results = self.GetResults()
    self._results = []
    return results

  def GetResults(self):
    return self._results or self._GetEmptyResults()

  def _GetEmptyResults(self):
    return [
        SurfaceStatsCollector.Result('refresh_period', None, 'seconds'),
        SurfaceStatsCollector.Result('jank_count', None, 'janks'),
        SurfaceStatsCollector.Result('max_frame_delay', None, 'vsyncs'),
        SurfaceStatsCollector.Result('frame_lengths', None, 'vsyncs'),
        SurfaceStatsCollector.Result('avg_surface_fps', None, 'fps')
    ]

  @staticmethod
  def _GetNormalizedDeltas(data, refresh_period, min_normalized_delta=None):
    deltas = [t2 - t1 for t1, t2 in zip(data, data[1:])]
    if min_normalized_delta != None:
      deltas = list(filter(lambda d: d / refresh_period >= min_normalized_delta,
                      deltas))
    return (deltas, [delta / refresh_period for delta in deltas])

  @staticmethod
  def _CalculateResults(refresh_period, timestamps, result_suffix):
    """Returns a list of SurfaceStatsCollector.Result."""
    frame_count = len(timestamps)
    seconds = timestamps[-1] - timestamps[0]

    frame_lengths, normalized_frame_lengths = \
        SurfaceStatsCollector._GetNormalizedDeltas(
            timestamps, refresh_period, _MIN_NORMALIZED_FRAME_LENGTH)
    if len(frame_lengths) < frame_count - 1:
      logging.warning('Skipping frame lengths that are too short.')
      frame_count = len(frame_lengths) + 1
    if len(frame_lengths) == 0:
      raise Exception('No valid frames lengths found.')
    length_changes, normalized_changes = \
        SurfaceStatsCollector._GetNormalizedDeltas(
            frame_lengths, refresh_period)
    jankiness = [max(0, round(change)) for change in normalized_changes]
    pause_threshold = 20
    jank_count = sum(1 for change in jankiness
                     if change > 0 and change < pause_threshold)
    return [
        SurfaceStatsCollector.Result(
            'avg_surface_fps' + result_suffix,
            int(round((frame_count - 1) / seconds)), 'fps'),
        SurfaceStatsCollector.Result(
            'jank_count' + result_suffix, jank_count, 'janks'),
        SurfaceStatsCollector.Result(
            'max_frame_delay' + result_suffix,
            round(max(normalized_frame_lengths)),
            'vsyncs'),
        SurfaceStatsCollector.Result(
            'frame_lengths' + result_suffix, normalized_frame_lengths,
            'vsyncs'),
    ]

  @staticmethod
  def _CalculateBuckets(refresh_period, timestamps):
    results = []
    for pct in [0.99, 0.5]:
      sliced = timestamps[min(int(-pct * len(timestamps)), -3) : ]
      results += SurfaceStatsCollector._CalculateResults(
          refresh_period, sliced, '_' + str(int(pct * 100)))
    return results

  def _StorePerfResults(self):
    if self._use_legacy_method:
      surface_after = self._GetSurfaceStatsLegacy()
      td = surface_after['timestamp'] - self._surface_before['timestamp']
      seconds = td.seconds + td.microseconds / 1e6
      frame_count = (surface_after['page_flip_count'] -
                     self._surface_before['page_flip_count'])
      self._results.append(SurfaceStatsCollector.Result(
          'avg_surface_fps', int(round(frame_count / seconds)), 'fps'))
      return

    # Non-legacy method.
    assert self._collector_thread
    (refresh_period, timestamps) = self._GetDataFromThread()
    if not refresh_period or not len(timestamps) >= 3:
      if self._warn_about_empty_data:
        logging.warning('Surface stat data is empty')
      return

    # if len(timestamps) >= 0:
    # print timestamps[1] - timestamps[0]

    self._results.append(SurfaceStatsCollector.Result(
        'refresh_period', refresh_period, 'seconds'))
    self._results += self._CalculateResults(refresh_period, timestamps, '')
    self._results += self._CalculateBuckets(refresh_period, timestamps)

  def _CollectorThread(self):
    last_timestamp = 0
    timestamps = []
    retries = 0

    while not self._stop_event.is_set():
      self._get_data_event.wait(1)
      try:
        refresh_period, new_timestamps = self._GetSurfaceFlingerFrameData()
        if refresh_period is None or timestamps is None:
          retries += 1
          if retries < 3:
            continue
          if last_timestamp:
            # Some data has already been collected, but either the app
            # was closed or there's no new data. Signal the main thread and
            # wait.
            self._data_queue.put((None, None))
            self._stop_event.wait()
            break
          raise Exception('Unable to get surface flinger latency data')

        timestamps += [timestamp for timestamp in new_timestamps
                       if timestamp > last_timestamp]
        if len(timestamps):
          last_timestamp = timestamps[-1]

        if self._get_data_event.is_set():
          self._get_data_event.clear()
          self._data_queue.put((refresh_period, timestamps))
          timestamps = []
      except Exception as e:
        # On any error, before aborting, put the exception into _data_queue to
        # prevent the main thread from waiting at _data_queue.get() infinitely.
        self._data_queue.put(e)
        raise

  def _GetDataFromThread(self):
    self._get_data_event.set()
    ret = self._data_queue.get()
    if isinstance(ret, Exception):
      raise ret
    return ret

  def _ClearSurfaceFlingerLatencyData(self):
    """Clears the SurfaceFlinger latency data.

    Returns:
      True if SurfaceFlinger latency is supported by the device, otherwise
      False.
    """
    # The command returns nothing if it is supported, otherwise returns many
    # lines of result just like 'dumpsys SurfaceFlinger'.
    results = self._dev.shell(
        'dumpsys SurfaceFlinger --latency-clear ' + self._activity).splitlines()
    return not len(results)

  def _GetSurfaceFlingerFrameData(self):
    """Returns collected SurfaceFlinger frame timing data.

    Returns:
      A tuple containing:
      - The display's nominal refresh period in seconds.
      - A list of timestamps signifying frame presentation times in seconds.
      The return value may be (None, None) if there was no data collected (for
      example, if the app was closed before the collector thread has finished).
    """
    # adb shell dumpsys SurfaceFlinger --latency <window name>
    # prints some information about the last 128 frames displayed in
    # that window.
    # The data returned looks like this:
    # 16954612
    # 7657467895508   7657482691352   7657493499756
    # 7657484466553   7657499645964   7657511077881
    # 7657500793457   7657516600576   7657527404785
    # (...)
    #
    # The first line is the refresh period (here 16.95 ms), it is followed
    # by 128 lines w/ 3 timestamps in nanosecond each:
    # A) when the app started to draw
    # B) the vsync immediately preceding SF submitting the frame to the h/w
    # C) timestamp immediately after SF submitted that frame to the h/w
    #
    # The difference between the 1st and 3rd timestamp is the frame-latency.
    # An interesting data is when the frame latency crosses a refresh period
    # boundary, this can be calculated this way:
    #
    # ceil((C - A) / refresh-period)
    #
    # (each time the number above changes, we have a "jank").
    # If this happens a lot during an animation, the animation appears
    # janky, even if it runs at 60 fps in average.
    #
    # We use the special "SurfaceView" window name because the statistics for
    # the activity's main window are not updated when the main web content is
    # composited into a SurfaceView.
    results = self._dev.shell(
        'dumpsys SurfaceFlinger --latency ' + self._activity).splitlines()
    if not len(results):
      return (None, None)

    while not results[0].isdigit():
      results = self._dev.shell(
          'dumpsys SurfaceFlinger --latency ' + self._activity).splitlines()

    timestamps = []
    nanoseconds_per_second = 1e9
    refresh_period = int(results[0]) / nanoseconds_per_second

    # If a fence associated with a frame is still pending when we query the
    # latency data, SurfaceFlinger gives the frame a timestamp of INT64_MAX.
    # Since we only care about completed frames, we will ignore any timestamps
    # with this value.
    pending_fence_timestamp = (1 << 63) - 1

    for line in results[1:]:
      fields = line.split()
      if len(fields) != 3:
        continue
      timestamp = int(fields[1])
      if timestamp == pending_fence_timestamp:
        continue
      timestamp /= nanoseconds_per_second
      timestamps.append(timestamp)

    return (refresh_period, timestamps)

  def _GetSurfaceStatsLegacy(self):
    """Legacy method (before JellyBean), returns the current Surface index
       and timestamp.

    Calculate FPS by measuring the difference of Surface index returned by
    SurfaceFlinger in a period of time.

    Returns:
      Dict of {page_flip_count (or 0 if there was an error), timestamp}.
    """
    results = self._dev.shell('su -c "service call SurfaceFlinger 1013;"').splitlines()
    assert len(results) == 1
    match = re.search('^Result: Parcel\((\w+)', results[0])
    cur_surface = 0
    if match:
      try:
        cur_surface = int(match.group(1), 16)
      except Exception:
        logging.error('Failed to parse current surface from ' + match.group(1))
    else:
      logging.warning('Failed to call SurfaceFlinger surface ' + results[0])
    return {
        'page_flip_count': cur_surface,
        'timestamp': datetime.datetime.now(),
    }
