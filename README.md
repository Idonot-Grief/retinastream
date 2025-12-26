# retinastream
Stream over RTMP from something like OBS to a live preview window at the host.
This is useful in cases where you want a video feed of a desktop from a remote computer and you want it on another computer. The program accepts any stream keys. 
Here is an example of how to stream from OBS on a desktop to OBS on a laptop.

1. You go in to the settings for streaming on your desktop instance of OBS.
   
2. You set the server to custom and set the IP to your RetinaStream host.

3. You can leave the stream key blank or set it to anything.

4. Start RetinaStream RTMP on your laptop.

5. Start streaming on your desktop.

6. Setup a window capture in your laptop's OBS and set it to the RetinaStream preview.

That's how to setup an OBS to OBS connection.

You are able to setup your own resoloution and framerate for the host in the source code.
It is only recommended to use this on a local network considering someone could use any stream key if public.
