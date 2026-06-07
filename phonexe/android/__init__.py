"""
Android forensic modules.

Two acquisition models are supported, both for *authorized* examinations:

1. Filesystem extraction -- analyze a directory tree copied from the device's
   /data partition (e.g. obtained from a device you are lawfully permitted to
   examine). App data lives under /data/data/<package>/databases/*.db.

2. Live ADB logical extraction -- pull data from a connected device that has
   USB debugging enabled and is authorized for examination, via ADB content
   providers and file pulls.

As with the iOS side, these modules never bypass lock screens, defeat FRP,
exploit vulnerabilities, or access remote cloud accounts.
"""
