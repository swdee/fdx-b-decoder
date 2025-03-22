# FDX-B Sigrok Protocol Decoder

This sigrok decoder is for the ISO 11784/11785 standard to decode FDX-B 134.2kHz RFID transponders.
It has been tested with [Sigrok](https://sigrok.org/wiki/Main_Page)/[Pulseview](https://github.com/sigrokproject/pulseview) 
and used with [DreamSourceLab's DSView](https://github.com/DreamSourceLab/DSView) application (a sigrok fork).

## Installation

## Sigrok/PulseView

The sigrok decoder libraries are located at `/usr/local/share/libsigrokdecode/decoders/`

Clone this github project into that directory
```
cd /usr/local/share/libsigrokdecode/decoders/
git clone https://github.com/swdee/fdx-b-decoder.git fdx-b
```

Start PulseView and Add Protocol Decoder, then search for `FDX-B` in the list and add the decoder.


## DreamSourceLab DSView

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
