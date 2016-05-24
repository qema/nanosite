Title: Sound Transfer

![Sound Transfer](http://wanganzhou.com/images/sound-transfer/screenshot.png)

Sound Transfer is a system to send a message from your computer to a friend's with speaker and mic. It uses a melodic pitch-based protocol, which means you can hear your message converted into a musical ditty in the process!

Check out the source code on GitHub: [Sound Transfer](https://github.com/losmmorpg/sound-transfer).

Method: The outgoing message is converted into its binary ASCII representation, then converted to pitches with the melodic protocol. The receiver picks up the pitches with Fourier transforms and decodes from binary to ASCII text.

Here's the protocol.

    Pitch   Symbol  Meaning
    ---------------------------------------
    1976 Hz  '!'    Begin transmission.
    1174 Hz  '0'    Send a binary 0.
    784 Hz   '1'    Send a binary 1.
    988 Hz   '*'    Used as a separator between repeated digits.
    1568 Hz  '.'    End transmission.

Wow! So musical!  
Create your own message melodies.
