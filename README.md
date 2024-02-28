# FDX-B Sigrok Protocol Decoder

This sigrok decoder is for the ISO 11784/11785 standard to decode FDX-B 134.2kHz RFID transponders.
It is untested with sigrok, however is used with [DreamSourceLab's DSView](https://github.com/DreamSourceLab/DSView) application.

## Installation

Having installed DSView using that projects instructions on linux, it installed the sigrok decoder library to directory `/usr/local/share/libsigrokdecode4DSL/decoders/`.

Clone this github project into that directory
```
cd /usr/local/share/libsigrokdecode4DSL/decoders/
git clone https://github.com/swdee/fdx-b-decoder.git fdx-b
```
Start DSView and select `FDX-B` as the decoder.


## Decoding Example

Screenshot of decoded transponder tag.

![Transponder Decoded](dsview-fdx-b-sample.png?raw=true)
