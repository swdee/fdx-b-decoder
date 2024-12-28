# FDX-B Sigrok Protocol Decoder

This sigrok decoder is for the ISO 11784/11785 standard to decode FDX-B 134.2kHz RFID transponders.
It is untested with sigrok, but is used with [DreamSourceLab's DSView](https://github.com/DreamSourceLab/DSView) application which
is a sigrok fork.

## Installation

Install DSView using that projects instructions on linux, once installed 
the sigrok decoder library directory is at `/usr/local/share/libsigrokdecode4DSL/decoders/`.

Clone this github project into that directory
```
cd /usr/local/share/libsigrokdecode4DSL/decoders/
git clone https://github.com/swdee/fdx-b-decoder.git fdx-b
```
Start DSView and select `FDX-B` as the decoder.


## Decoding Example

Screenshot of decoded transponder tag.

![Transponder Decoded](dsview-fdx-b-sample.png?raw=true)
